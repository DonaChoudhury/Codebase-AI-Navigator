import os
import requests
import base64
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

TARGET_OWNER = "DonaChoudhury"
TARGET_REPO = "rag-demo"

def get_file_content(path):
    """GitHub se file ke andar ka actual text download karta hai"""
    url = f"https://api.github.com/repos/{TARGET_OWNER}/{TARGET_REPO}/contents/{path}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        content_base64 = response.json()['content']
        # GitHub content ko base64 format mein bhejta hai, hum usko normal text mein decode kar rahe hain
        return base64.b64decode(content_base64).decode('utf-8')
    return None

def create_database():
    print("📥 GitHub se files download ho rahi hain...")
    
    # 1. Files ka data fetch karna
    readme_text = get_file_content("README.md")
    calculator_text = get_file_content("calculator.py")
    
    # Inko Langchain 'Documents' mein convert karna, sath mein metadata (file ka naam) attach karna
    documents = [
        Document(page_content=readme_text, metadata={"source": "README.md"}),
        Document(page_content=calculator_text, metadata={"source": "calculator.py"})
    ]
    
    print("✂️ Files ko chote chunks mein tod rahe hain...")
    # 2. Chunking: Code ko 500 characters ke tukdon mein todna
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)
    print(f"✅ Total {len(chunks)} chunks ban gaye.")

    print("🧠 AI Embedding Model load ho raha hai (Pehli baar thoda time lagega)...")
    # 3. Embedding Model: Text ko Vectors (numbers) mein convert karne ke liye (Free & Local)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print("💾 ChromaDB Vector Database mein data save ho raha hai...")
    # 4. Vector Database: Chunks aur Embeddings ko 'chroma_db' folder mein save karna
    vectorstore = Chroma.from_documents(
        documents=chunks, 
        embedding=embeddings, 
        persist_directory="./chroma_db" # Ye folder tumhare project mein ban jayega
    )
    
    print("\n🎉 SUCCESS! Tumhara Codebase RAG ka 'Dimaag' ban gaya hai aur database ready hai!")

if __name__ == "__main__":
    create_database()