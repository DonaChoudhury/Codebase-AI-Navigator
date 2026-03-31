from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests
import base64
from dotenv import load_dotenv
from pymongo import MongoClient  # NAYA IMPORT

# LangChain Imports
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document


# --- NAYE AUTH IMPORTS ---
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends

# 1. Load Keys & Connect to MongoDB
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    print("❌ Error: MONGO_URI nahi mila .env file mein!")

# MongoDB Connection Setup
print("🔌 Connecting to MongoDB Atlas...")
client = MongoClient(MONGO_URI)
db = client["codebase_rag_db"]         # Database ka naam
repo_collection = db["repo_states"]    # Collection (Table) ka naam



# MongoDB Collections
repo_collection = db["repo_states"]
users_collection = db["users"] # 👈 NAYA: Users ka data yahan save hoga

# --- SECURITY SETUP (JWT & Hashing) ---
# Asli project mein is secret key ko .env mein rakhte hain
SECRET_KEY = "mera_super_secret_key_isko_badal_dena" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # Token 1 din tak chalega

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Pydantic Model (Signup ke liye)
class UserCreate(BaseModel):
    username: str
    password: str

# Helper Functions (Password chupane aur Token banane ke liye)
# Aur apne dono purane password functions ko isse REPLACE kar do:
def get_password_hash(password: str):
    # Password ko pehle bytes mein convert karte hain, phir hash karte hain
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8') # Wapas string banakar save karenge

def verify_password(plain_password: str, hashed_password: str):
    # Check karte waqt dono ko bytes mein compare karna hota hai
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

app = FastAPI(title="Pro Codebase RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=GEMINI_API_KEY)

class RepoRequest(BaseModel):
    owner: str
    repo: str

class ChatRequest(BaseModel):
    owner: str
    repo: str
    question: str




# =========================================================
# ENDPOINT: /signup (Naya account banana)
# =========================================================
@app.post("/signup")
async def signup(user: UserCreate):
    # 1. Check karo ki user pehle se toh nahi hai
    existing_user = users_collection.find_one({"_id": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists! Koi aur naam try karo.")

    # 2. Naya user save karo (Password hash karke)
    user_dict = {
        "_id": user.username,
        "password": get_password_hash(user.password),
        "history": [] # 👈 Yahan hum save karenge ki isne konse repos search kiye!
    }
    users_collection.insert_one(user_dict)
    
    return {"message": "Account successfully created! Welcome to the club 🚀"}

# =========================================================
# ENDPOINT: /login (Token generate karna)
# =========================================================
@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # 1. User dhoondo
    user = users_collection.find_one({"_id": form_data.username})
    
    # 2. Password match karo
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Galat Username ya Password!")

    # 3. Agar sab sahi hai, toh JWT Token (Entry Pass) banao
    access_token = create_access_token(data={"sub": user["_id"]})
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "message": f"Welcome back, {user['_id']}!"
    }

# =========================================================
# ENDPOINT 1: /process (MONGODB DELTA SYNC)
# =========================================================
@app.post("/process")
async def process_repo(request: RepoRequest):
    repo_id = f"{request.owner}/{request.repo}"
    
    print(f"📥 Checking GitHub for {repo_id}...")
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"https://api.github.com/repos/{request.owner}/{request.repo}/contents/"
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Repo not found or empty")

    github_items = response.json()
    
    # 🌟 MONGODB MAGIC: Fetch existing state
    db_record = repo_collection.find_one({"_id": repo_id})
    current_repo_state = db_record.get("files", {}) if db_record else {}
    
    new_files_list = []
    updated_files_list = []
    files_to_download = []
    new_repo_state = current_repo_state.copy()

    for item in github_items:
        if item['type'] == 'file' and item['name'].endswith(('.py', '.md', '.js', '.txt')):
            name = item['name']
            sha = item['sha']
            
            if name not in current_repo_state:
                new_files_list.append(name)
                files_to_download.append(item)
            elif current_repo_state[name] != sha:
                updated_files_list.append(name)
                files_to_download.append(item)
                
            new_repo_state[name] = sha

    if not files_to_download:
        return {"message": "Sab kuch up-to-date hai!", "new_files": [], "updated_files": []}

    print(f"🚀 Downloading: {len(new_files_list)} New, {len(updated_files_list)} Updated.")
    
    documents = []
    vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

    for item in files_to_download:
        name = item['name']
        
        if name in updated_files_list:
            try:
                existing_data = vectorstore.get(where={"source": name, "repo_id": repo_id})
                if existing_data['ids']:
                    vectorstore.delete(ids=existing_data['ids'])
            except Exception as e:
                pass 

        file_resp = requests.get(item['url'], headers=headers)
        if file_resp.status_code == 200:
            content = base64.b64decode(file_resp.json()['content']).decode('utf-8')
            doc = Document(page_content=content, metadata={"source": name, "repo_id": repo_id})
            documents.append(doc)

    if documents:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = text_splitter.split_documents(documents)
        vectorstore.add_documents(documents=chunks)
    
    # 🌟 MONGODB MAGIC: Update or Insert the new state (Upsert)
    repo_collection.update_one(
        {"_id": repo_id}, 
        {"$set": {"files": new_repo_state}}, 
        upsert=True
    )
    
    return {
        "message": "Sync Successful & Saved to MongoDB!",
        "new_files": new_files_list,
        "updated_files": updated_files_list
    }


# =========================================================
# ENDPOINT 2: /chat (Same as before)
# =========================================================
@app.post("/chat")
async def chat_with_repo(request: ChatRequest):
    repo_id = f"{request.owner}/{request.repo}"
    vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3, "filter": {"repo_id": repo_id}})
    
    template = """You are an expert developer assistant. 
    Use the provided code context to answer the user's question. 
    Explain clearly and simply. If the answer is not in the context, say 'I don't know based on the provided codebase'.
    
    Context: {context}
    Question: {question}
    Answer:"""
    
    prompt = ChatPromptTemplate.from_template(template)
    def format_docs(docs): return "\n\n".join(doc.page_content for doc in docs)
        
    rag_chain = ({"context": retriever | format_docs, "question": RunnablePassthrough()} | prompt | llm | StrOutputParser())
    
    answer = rag_chain.invoke(request.question)
    return {"repo": repo_id, "question": request.question, "answer": answer}


# Naya Import adds ke liye (Sabse upar):
from collections import defaultdict

# =========================================================
# ENDPOINT 3: /readme (EFFICIENT SKELETON APPROACH)
# =========================================================
@app.post("/readme")
async def generate_readme_efficient(request: RepoRequest):
    repo_id = f"{request.owner}/{request.repo}"
    print(f"📄 Generating EFFICIENT README for {repo_id}...")

    # 1. Database se connect karo
    vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    
    # 2. Repo ka SAARA data uthao (Sirf metadata ke liye)
    repo_data = vectorstore.get(where={"repo_id": repo_id})
    
    if not repo_data['metadatas']:
        raise HTTPException(status_code=404, detail="Repo data not found. Please sync the repo first.")

    # --- SKELETON GENERATION LOGIC ---
    
    # 3. Project Tree/Skeleton Banao (Files aur Unki Locations)
    project_structure = []
    # Hum unique sources (file paths) nikalenge
    unique_files = sorted(list(set(m['source'] for m in repo_data['metadatas'])))
    
    print(f"🏗️ Building Project Skeleton... Found {len(unique_files)} files.")
    
    skeleton_text = "Project Structure:\n"
    current_path = []
    for file_path in unique_files:
        parts = file_path.split('/')
        
        # Simple tree structure format
        for i, part in enumerate(parts):
            if i < len(current_path) and current_path[i] == part:
                continue
            
            # Reset current path after divergence
            current_path = current_path[:i] + [part]
            
            # Print indentation
            indent = "  " * (len(current_path) - 1)
            prefix = "└── " if i == len(parts) - 1 else "├── "
            skeleton_text += f"{indent}{prefix}{part}\n"

    # 4. Main/Core Files ka Content Fetch Karo (E.g., main.py, requirements.txt)
    core_files_data = ""
    # Hum ginti ki files ka poora content nikalenge
    # (Humein vectorstore se pure content ke liye un unique files ke ids nikalne padenge)
    # Yeh part vectorstore search logic par dependent hai. Simplicity ke liye hum ginti ke chunks fetch kar lete hain jo in files se associated hon.
    core_files_keywords = ['main.py', 'app.py', 'requirements.txt', 'package.json', 'README_template.md', 'run.py', 'config.py']
    
    # Ginti ke files ka complete code fetch karenge (Simulated)
    print("💻 Fetching Core Files for AI Context...")
    for file_path in unique_files:
        is_core_file = any(keyword in file_path for keyword in core_files_keywords)
        if is_core_file:
            core_files_data += f"\n--- CONTENT OF {file_path} ---\n"
            # Ginti ke documents (chunks) fetch kar lenge jo in unique files se match karte hon
            matched_docs = vectorstore.get(where={"source": file_path, "repo_id": repo_id})
            if matched_docs['documents']:
                core_files_data += matched_docs['documents'][0] # Sirf pehla chunk le rahe hain for speed/efficiency
                if len(matched_docs['documents']) > 1:
                     core_files_data += f"\n... (File content shortened for efficiency) ..."

    # 5. The "Smart Skeleton Prompt"
    prompt = f"""
    You are an expert Senior Developer. I am giving you the core information about a project, not the entire codebase, to write a highly professional, beautifully formatted GitHub README.md file.
    
    Use the Project Structure (Skeleton) and the Content of Core Files to infer the tech stack, main functionalities, and usage instructions.
    
    Your strictly single job is to write a highly professional, beautiful README.md that must include:
    1. 🚀 Project Title & A Catchy Description
    2. ✨ Key Features (deduced from project structure and core files)
    3. 💻 Tech Stack Used (infer from the code/dependencies)
    4. ⚙️ Setup & Installation Instructions (make an educated guess based on tech stack)
    5. 📖 Basic Usage Example (infer from core entry point file if possible)
    
    ***
    Here is the project data:
    
    {skeleton_text}
    
    {core_files_data}
    """
    
    # 6. Gemini se direct jawab maango (Kam tokens aur faster response!)
    try:
        print("🧠 Gemini is reading the skeleton... (Faster, cheaper, smarter)")
        response = llm.invoke(prompt)
        return {"repo": repo_id, "readme": response.content}
    except Exception as e:
        return {"error": f"Failed to generate README: {str(e)}"}