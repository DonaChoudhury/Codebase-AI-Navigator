from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests
import base64
from dotenv import load_dotenv

# LangChain Imports
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

# 1. Setup Environment aur Models
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = FastAPI(title="Dynamic Codebase RAG API")

# CORS setup (Taaki React isse bina kisi error ke baat kar sake)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI Models (Inko globally ek baar load karenge taaki app fast rahe)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=GEMINI_API_KEY)

# 2. Request Data Models (React se kya data aayega uska structure)
class RepoRequest(BaseModel):
    owner: str
    repo: str

class ChatRequest(BaseModel):
    owner: str
    repo: str
    question: str

# Helper Function: GitHub se file laane ke liye
def get_repo_files(owner, repo):
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/"
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []
        
    files_data = []
    for item in response.json():
        if item['type'] == 'file' and item['name'].endswith(('.py', '.md', '.js', '.txt')):
            file_resp = requests.get(item['url'], headers=headers)
            if file_resp.status_code == 200:
                content = base64.b64decode(file_resp.json()['content']).decode('utf-8')
                files_data.append({"name": item['name'], "content": content})
    return files_data


# =========================================================
# ENDPOINT 1: /process (Nayi Repo ko Database mein daalna)
# =========================================================
@app.post("/process")
async def process_repo(request: RepoRequest):
    repo_id = f"{request.owner}/{request.repo}"
    
    print(f"📥 Fetching files for {repo_id}...")
    files = get_repo_files(request.owner, request.repo)
    
    if not files:
        raise HTTPException(status_code=404, detail="Repo not found or empty")

    documents = []
    for file in files:
        # MAGIC: Har document mein hum 'repo_id' save kar rahe hain
        doc = Document(
            page_content=file['content'], 
            metadata={"source": file['name'], "repo_id": repo_id}
        )
        documents.append(doc)

    print("✂️ Chunking and saving to DB...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)

    # Database mein save karna
    Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory="./chroma_db")
    
    return {"message": f"Successfully processed {len(files)} files for {repo_id}!"}


# =========================================================
# ENDPOINT 2: /chat (Sawal poochna)
# =========================================================
@app.post("/chat")
async def chat_with_repo(request: ChatRequest):
    repo_id = f"{request.owner}/{request.repo}"
    
    # Database load karo
    vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    
    # MAGIC: Sirf usi repo ke code mein dhoondho jo user ne bheji hai
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": 3, "filter": {"repo_id": repo_id}}
    )
    
    template = """You are an expert developer assistant. 
    Use the provided code context to answer the user's question about their GitHub repository. 
    Explain clearly and simply. If the answer is not in the context, say 'I don't know based on the provided codebase'.
    
    Context: {context}
    Question: {question}
    Answer:"""
    
    prompt = ChatPromptTemplate.from_template(template)
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
        
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    print(f"🤖 Generating answer for {repo_id}...")
    answer = rag_chain.invoke(request.question)
    
    return {"repo": repo_id, "question": request.question, "answer": answer}