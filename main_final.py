# import os
# import requests
# import base64
# from collections import defaultdict
# from datetime import datetime, timedelta

# from fastapi import FastAPI, HTTPException, Depends
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from pydantic import BaseModel
# from dotenv import load_dotenv

# from pymongo import MongoClient
# import bcrypt
# from jose import JWTError, jwt

# # LangChain Imports
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_community.vectorstores import Chroma
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.runnables import RunnablePassthrough
# from langchain_core.output_parsers import StrOutputParser
# from langchain_core.documents import Document

# # =========================================================
# # 1. SETUP & CONFIGURATION
# # =========================================================
# load_dotenv()
# GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# MONGO_URI = os.getenv("MONGO_URI")

# if not MONGO_URI:
#     print("❌ Error: MONGO_URI nahi mila .env file mein!")

# print("🔌 Connecting to MongoDB Atlas...")
# client = MongoClient(MONGO_URI)
# db = client["codebase_rag_db"]
# repo_collection = db["repo_states"]
# users_collection = db["users"] 

# SECRET_KEY = "mera_super_secret_key_isko_badal_dena" 
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# app = FastAPI(title="Pro Codebase RAG API")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], 
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
# llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=GEMINI_API_KEY)

# # =========================================================
# # 2. PYDANTIC MODELS (Data Validation)
# # =========================================================
# class UserCreate(BaseModel):
#     username: str
#     password: str

# class RepoRequest(BaseModel):
#     owner: str
#     repo: str

# class ChatRequest(BaseModel):
#     owner: str
#     repo: str
#     question: str

# # =========================================================
# # 3. SECURITY HELPER FUNCTIONS (The Guards)
# # =========================================================
# def get_password_hash(password: str):
#     salt = bcrypt.gensalt()
#     hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
#     return hashed_password.decode('utf-8')

# def verify_password(plain_password: str, hashed_password: str):
#     return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# def create_access_token(data: dict):
#     to_encode = data.copy()
#     expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# # 🌟 NAYA HELPER: Bouncer jo har request par token check karega
# async def get_current_user(token: str = Depends(oauth2_scheme)):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         username: str = payload.get("sub")
#         if username is None:
#             raise HTTPException(status_code=401, detail="Invalid Authentication")
#         return username
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid or Expired Token")

# # =========================================================
# # 4. AUTHENTICATION ENDPOINTS (Open for all)
# # =========================================================
# @app.post("/signup")
# async def signup(user: UserCreate):
#     existing_user = users_collection.find_one({"_id": user.username})
#     if existing_user:
#         raise HTTPException(status_code=400, detail="Username already exists! Try using different username.")

#     user_dict = {
#         "_id": user.username,
#         "password": get_password_hash(user.password),
#         "history": [] 
#     }
#     users_collection.insert_one(user_dict)
#     return {"message": "Account successfully created! Welcome to the club 🚀"}

# @app.post("/login")
# async def login(form_data: OAuth2PasswordRequestForm = Depends()):
#     user = users_collection.find_one({"_id": form_data.username})
#     if not user or not verify_password(form_data.password, user["password"]):
#         raise HTTPException(status_code=401, detail="Incorrect  Username or Password!")

#     access_token = create_access_token(data={"sub": user["_id"]})
#     return {
#         "access_token": access_token, 
#         "token_type": "bearer",
#         "message": f"Welcome back, {user['_id']}!"
#     }

# # =========================================================
# # 5. CORE ENDPOINTS (LOCKED 🔒 - Needs Token)
# # =========================================================

# # 🔒 Locked: current_user lagaya gaya hai
# @app.post("/process")
# async def process_repo(request: RepoRequest, current_user: str = Depends(get_current_user)):
#     repo_id = f"{request.owner}/{request.repo}"
    
#     # 🌟 HISTORY TRACKING: Kis user ne konsa repo sync kiya
#     users_collection.update_one(
#         {"_id": current_user}, 
#         {"$addToSet": {"history": repo_id}}
#     )
    
#     print(f"📥 {current_user} is checking GitHub for {repo_id}...")
#     headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
#     url = f"https://api.github.com/repos/{request.owner}/{request.repo}/contents/"
    
#     response = requests.get(url, headers=headers)
#     if response.status_code != 200:
#         raise HTTPException(status_code=404, detail="Repo not found or empty")

#     github_items = response.json()
#     db_record = repo_collection.find_one({"_id": repo_id})
#     current_repo_state = db_record.get("files", {}) if db_record else {}
    
#     new_files_list = []
#     updated_files_list = []
#     files_to_download = []
#     new_repo_state = current_repo_state.copy()

#     for item in github_items:
#         if item['type'] == 'file' and item['name'].endswith(('.py', '.md', '.js', '.txt', '.jsx', '.json')):
#             name = item['name']
#             sha = item['sha']
            
#             if name not in current_repo_state:
#                 new_files_list.append(name)
#                 files_to_download.append(item)
#             elif current_repo_state[name] != sha:
#                 updated_files_list.append(name)
#                 files_to_download.append(item)
                
#             new_repo_state[name] = sha

#     if not files_to_download:
#         return {"message": "Files already downloaded ", "new_files": [], "updated_files": []}

#     print(f"🚀 Downloading: {len(new_files_list)} New, {len(updated_files_list)} Updated.")
    
#     documents = []
#     vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)

#     for item in files_to_download:
#         name = item['name']
        
#         if name in updated_files_list:
#             try:
#                 existing_data = vectorstore.get(where={"source": name, "repo_id": repo_id})
#                 if existing_data['ids']:
#                     vectorstore.delete(ids=existing_data['ids'])
#             except Exception as e:
#                 pass 

#         file_resp = requests.get(item['url'], headers=headers)
#         if file_resp.status_code == 200:
#             content = base64.b64decode(file_resp.json()['content']).decode('utf-8')
#             doc = Document(page_content=content, metadata={"source": name, "repo_id": repo_id})
#             documents.append(doc)

#     if documents:
#         text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
#         chunks = text_splitter.split_documents(documents)
#         vectorstore.add_documents(documents=chunks)
    
#     repo_collection.update_one(
#         {"_id": repo_id}, 
#         {"$set": {"files": new_repo_state}}, 
#         upsert=True
#     )
    
#     return {
#         "message": "Sync Successful & Saved to MongoDB!",
#         "new_files": new_files_list,
#         "updated_files": updated_files_list
#     }

# # 🔒 Locked: current_user lagaya gaya hai
# @app.post("/chat")
# async def chat_with_repo(request: ChatRequest, current_user: str = Depends(get_current_user)):
#     repo_id = f"{request.owner}/{request.repo}"
#     print(f"💬 {current_user} asked a question about {repo_id}")
    
#     vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
#     retriever = vectorstore.as_retriever(search_kwargs={"k": 3, "filter": {"repo_id": repo_id}})
    
#     template = """You are an expert developer assistant. 
#     Use the provided code context to answer the user's question. 
#     Explain clearly and simply. If the answer is not in the context, say 'I don't know based on the provided codebase'.
    
#     Context: {context}
#     Question: {question}
#     Answer:"""
    
#     prompt = ChatPromptTemplate.from_template(template)
#     def format_docs(docs): return "\n\n".join(doc.page_content for doc in docs)
        
#     rag_chain = ({"context": retriever | format_docs, "question": RunnablePassthrough()} | prompt | llm | StrOutputParser())
    
#     answer = rag_chain.invoke(request.question)
#     return {"repo": repo_id, "question": request.question, "answer": answer}

# # 🔒 Locked: current_user lagaya gaya hai
# @app.post("/readme")
# async def generate_readme_efficient(request: RepoRequest, current_user: str = Depends(get_current_user)):
#     repo_id = f"{request.owner}/{request.repo}"
#     print(f"📄 {current_user} is generating EFFICIENT README for {repo_id}...")

#     vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
#     repo_data = vectorstore.get(where={"repo_id": repo_id})
    
#     if not repo_data['metadatas']:
#         raise HTTPException(status_code=404, detail="Repo data not found. Please sync the repo first.")

#     project_structure = []
#     unique_files = sorted(list(set(m['source'] for m in repo_data['metadatas'])))
    
#     skeleton_text = "Project Structure:\n"
#     current_path = []
#     for file_path in unique_files:
#         parts = file_path.split('/')
#         for i, part in enumerate(parts):
#             if i < len(current_path) and current_path[i] == part:
#                 continue
#             current_path = current_path[:i] + [part]
#             indent = "  " * (len(current_path) - 1)
#             prefix = "└── " if i == len(parts) - 1 else "├── "
#             skeleton_text += f"{indent}{prefix}{part}\n"

#     core_files_data = ""
#     core_files_keywords = ['main.py', 'app.py', 'requirements.txt', 'package.json', 'README_template.md', 'run.py', 'config.py']
    
#     for file_path in unique_files:
#         is_core_file = any(keyword in file_path for keyword in core_files_keywords)
#         if is_core_file:
#             core_files_data += f"\n--- CONTENT OF {file_path} ---\n"
#             matched_docs = vectorstore.get(where={"source": file_path, "repo_id": repo_id})
#             if matched_docs['documents']:
#                 core_files_data += matched_docs['documents'][0] 
#                 if len(matched_docs['documents']) > 1:
#                      core_files_data += f"\n... (File content shortened for efficiency) ..."

#     prompt = f"""
#     You are an expert Senior Developer. I am giving you the core information about a project, not the entire codebase, to write a highly professional, beautifully formatted GitHub README.md file.
    
#     Your strictly single job is to write a highly professional, beautiful README.md that must include:
#     1. 🚀 Project Title & A Catchy Description
#     2. ✨ Key Features (deduced from project structure and core files)
#     3. 💻 Tech Stack Used (infer from the code/dependencies)
#     4. ⚙️ Setup & Installation Instructions (make an educated guess based on tech stack)
#     5. 📖 Basic Usage Example (infer from core entry point file if possible)
    
#     ***
#     Here is the project data:
    
#     {skeleton_text}
    
#     {core_files_data}
#     """
    
#     try:
#         response = llm.invoke(prompt)
#         return {"repo": repo_id, "readme": response.content}
#     except Exception as e:
#         return {"error": f"Failed to generate README: {str(e)}"}





















import os
import requests
import base64
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from dotenv import load_dotenv

from pymongo import MongoClient
import bcrypt
from jose import JWTError, jwt

# LangChain Imports
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

# =========================================================
# 1. SETUP & CONFIGURATION
# =========================================================
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    print("❌ Error: MONGO_URI nahi mila .env file mein!")

print("🔌 Connecting to MongoDB Atlas...")
client = MongoClient(MONGO_URI)
db = client["codebase_rag_db"]
repo_collection = db["repo_states"]
users_collection = db["users"] 

SECRET_KEY = "mera_super_secret_key_isko_badal_dena" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

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

# =========================================================
# 2. PYDANTIC MODELS (Data Validation)
# =========================================================
class UserCreate(BaseModel):
    username: str
    password: str

class RepoRequest(BaseModel):
    owner: str
    repo: str

class ChatRequest(BaseModel):
    owner: str
    repo: str
    question: str

# =========================================================
# 3. SECURITY HELPER FUNCTIONS
# =========================================================
def get_password_hash(password: str):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid Authentication")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or Expired Token")

# =========================================================
# 🌟 THE ULTIMATE SMART FETCHER (INDUSTRY STANDARD)
# =========================================================
def fetch_all_files(owner, repo, path="", token=""):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return []
        
    contents = response.json()
    if not isinstance(contents, list): 
        contents = [contents]
        
    all_files = []
    
    # ✅ RULE 1: THE ALLOWLIST (Sirf kaam ki files)
    valid_extensions = (
        '.py', '.md', '.js', '.jsx', '.ts', '.tsx', 
        '.html', '.css', '.java', '.cpp', '.json', '.yml', '.yaml'
    )
    
    # 🚫 RULE 2: THE ULTIMATE JUNK FOLDERS
    ignore_folders = {
        'node_modules', '.git', 'venv', 'env', '__pycache__', 
        'build', 'dist', '.next', 'out', '.cache', 'coverage', 
        '.idea', '.vscode', 'vendor', 'target'
    }
    
    # 🚫 RULE 3: THE ULTIMATE JUNK FILES
    ignore_files = {
        'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 
        'poetry.lock', 'Pipfile.lock', '.DS_Store', '.env', 
        'tsconfig.tsbuildinfo'
    }
    
    for item in contents:
        if item["type"] == "file":
            if item["name"].endswith(valid_extensions) and item["name"] not in ignore_files:
                all_files.append(item)
        elif item["type"] == "dir":
            if item["name"] not in ignore_folders:
                print(f"📂 Scanning: {item['path']}...")
                all_files.extend(fetch_all_files(owner, repo, item["path"], token))
            else:
                print(f"🛡️ Blocked Junk: {item['path']}")
                
    return all_files

# =========================================================
# 4. AUTHENTICATION ENDPOINTS
# =========================================================
@app.post("/signup")
async def signup(user: UserCreate):
    existing_user = users_collection.find_one({"_id": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists! Try using different username.")

    user_dict = {
        "_id": user.username,
        "password": get_password_hash(user.password),
        "history": [] 
    }
    users_collection.insert_one(user_dict)
    return {"message": "Account successfully created! Welcome to the club 🚀"}

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_collection.find_one({"_id": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect Username or Password!")

    access_token = create_access_token(data={"sub": user["_id"]})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "message": f"Welcome back, {user['_id']}!"
    }

# =========================================================
# 5. CORE ENDPOINTS (LOCKED 🔒)
# =========================================================

@app.post("/process")
async def process_repo(request: RepoRequest, current_user: str = Depends(get_current_user)):
    repo_id = f"{request.owner}/{request.repo}"
    
    users_collection.update_one(
        {"_id": current_user}, 
        {"$addToSet": {"history": repo_id}}
    )
    
    print(f"📥 {current_user} is scanning GitHub for {repo_id}...")
    
    github_items = fetch_all_files(request.owner, request.repo, path="", token=GITHUB_TOKEN)
    
    if not github_items:
        raise HTTPException(status_code=404, detail="Repo not found, empty, or rate limit reached.")

    db_record = repo_collection.find_one({"_id": repo_id})
    current_repo_state = db_record.get("files", {}) if db_record else {}
    
    new_files_list = []
    updated_files_list = []
    files_to_download = []
    new_repo_state = current_repo_state.copy()

    for item in github_items:
        file_path = item['path'] 
        sha = item['sha']
        
        if file_path not in current_repo_state:
            new_files_list.append(file_path)
            files_to_download.append(item)
        elif current_repo_state[file_path] != sha:
            updated_files_list.append(file_path)
            files_to_download.append(item)
            
        new_repo_state[file_path] = sha

    if not files_to_download:
        return {"message": "Files already up-to-date!", "new_files": [], "updated_files": []}

    print(f"🚀 Found {len(new_files_list)} New, {len(updated_files_list)} Updated core files. Processing...")
    
    documents = []
    vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

    for item in files_to_download:
        file_path = item['path']
        
        if file_path in updated_files_list:
            try:
                existing_data = vectorstore.get(where={"$and": [{"source": file_path}, {"repo_id": repo_id}]})
                if existing_data['ids']:
                    vectorstore.delete(ids=existing_data['ids'])
            except Exception:
                pass 

        file_resp = requests.get(item['url'], headers=headers)
        if file_resp.status_code == 200:
            try:
                content = base64.b64decode(file_resp.json()['content']).decode('utf-8', errors='ignore')
                doc = Document(page_content=content, metadata={"source": file_path, "repo_id": repo_id})
                documents.append(doc)
            except Exception as e:
                print(f"⚠️ Could not decode file {file_path}: {e}")

    if documents:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
        chunks = text_splitter.split_documents(documents)
        vectorstore.add_documents(documents=chunks)
    
    repo_collection.update_one(
        {"_id": repo_id}, 
        {"$set": {"files": new_repo_state}}, 
        upsert=True
    )
    
    return {
        "message": f"Successfully processed {len(documents)} core files (Blocked all junk)!",
        "new_files": new_files_list,
        "updated_files": updated_files_list
    }

@app.post("/chat")
async def chat_with_repo(request: ChatRequest, current_user: str = Depends(get_current_user)):
    repo_id = f"{request.owner}/{request.repo}"
    print(f"💬 {current_user} asking about {repo_id}: {request.question}")
    
    vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    # 🌟 NAYA: k=10 taaki AI aur zyada files padh sake
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10, "filter": {"repo_id": repo_id}})
    
    template = """You are an expert developer assistant. 
    Use the provided code context to answer the user's question. 
    Explain clearly and simply. If the answer is not in the context, say 'I don't know based on the provided codebase'.
    
    Context: {context}
    Question: {question}
    Answer:"""
    
    prompt = ChatPromptTemplate.from_template(template)
    def format_docs(docs): return "\n\n".join(f"File: {doc.metadata.get('source', 'Unknown')}\n{doc.page_content}" for doc in docs)
        
    rag_chain = ({"context": retriever | format_docs, "question": RunnablePassthrough()} | prompt | llm | StrOutputParser())
    
    answer = rag_chain.invoke(request.question)
    return {"repo": repo_id, "question": request.question, "answer": answer}

@app.post("/readme")
async def generate_readme_efficient(request: RepoRequest, current_user: str = Depends(get_current_user)):
    repo_id = f"{request.owner}/{request.repo}"
    
    vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    repo_data = vectorstore.get(where={"repo_id": repo_id})
    
    if not repo_data['metadatas']:
        raise HTTPException(status_code=404, detail="Repo data not found. Please sync the repo first.")

    unique_files = sorted(list(set(m['source'] for m in repo_data['metadatas'])))
    
    skeleton_text = "Project Structure:\n"
    current_path = []
    for file_path in unique_files:
        parts = file_path.split('/')
        for i, part in enumerate(parts):
            if i < len(current_path) and current_path[i] == part:
                continue
            current_path = current_path[:i] + [part]
            indent = "  " * (len(current_path) - 1)
            prefix = "└── " if i == len(parts) - 1 else "├── "
            skeleton_text += f"{indent}{prefix}{part}\n"

    core_files_data = ""
    core_files_keywords = ['main.py', 'app.py', 'requirements.txt', 'package.json', 'README_template.md', 'run.py', 'config.py', 'server.js', 'index.js']
    
    for file_path in unique_files:
        is_core_file = any(keyword in file_path.lower() for keyword in core_files_keywords)
        if is_core_file:
            core_files_data += f"\n--- CONTENT OF {file_path} ---\n"
            matched_docs = vectorstore.get(where={"$and": [{"source": file_path}, {"repo_id": repo_id}]})
            if matched_docs['documents']:
                core_files_data += matched_docs['documents'][0] 
                if len(matched_docs['documents']) > 1:
                     core_files_data += f"\n... (File content shortened for efficiency) ..."

    prompt = f"""
    You are an expert Senior Developer. I am giving you the core information about a project to write a highly professional GitHub README.md file.
    
    Must include:
    1. 🚀 Project Title & A Catchy Description
    2. ✨ Key Features
    3. 💻 Tech Stack Used
    4. ⚙️ Setup & Installation
    5. 📖 Basic Usage
    
    ***
    Here is the project data:
    
    {skeleton_text}
    
    {core_files_data}
    """
    
    try:
        response = llm.invoke(prompt)
        return {"repo": repo_id, "readme": response.content}
    except Exception as e:
        return {"error": f"Failed to generate README: {str(e)}"}