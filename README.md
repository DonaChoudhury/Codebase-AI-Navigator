# 🚀 Pro Codebase RAG API

An AI-powered developer assistant that understands any GitHub repository and lets you chat with your codebase, generate README files, and explore project structure intelligently using RAG (Retrieval-Augmented Generation).

---

## 🎥 Demo Video

> 🎥 A quick walkthrough of how this system transforms any codebase into an interactive, AI-powered assistant.

▶️ Watch here:  
https://drive.google.com/file/d/1CtY1tnKRGva1kOaMgT-FttU-GMrsXQIC/view?usp=drivesdk

---

## ✨ Features

### 🔐 User Authentication
- Signup & Login with JWT-based authentication  
- Secure password hashing using bcrypt  

### 📂 Smart GitHub Repo Processing
- Fetches only relevant source files (filters junk like `node_modules`, `.git`, etc.)  
- Detects new & updated files using SHA tracking  
- Efficient incremental updates  

### 🧠 RAG-based Code Understanding
- Uses embeddings + vector DB to understand code context  
- Ask questions about any repo like:
  - "What does this project do?"
  - "Explain the authentication flow"

### 💬 Chat with Your Codebase
- Context-aware AI answers using Gemini  
- Retrieves top relevant code chunks for better responses  

### 📄 Auto README Generator
- Generates a professional README.md from codebase  

**Includes:**
- Features  
- Tech stack  
- Setup instructions  
- Project structure  

### ⚡ Efficient Vector Storage
- Uses ChromaDB for fast semantic search  
- Updates only changed files  

---

## 🏗️ Tech Stack

- **Backend:** FastAPI  
- **Database:** MongoDB Atlas  
- **Authentication:** JWT + OAuth2  
- **AI/LLM:** Google Gemini (via LangChain)  
- **Embeddings:** HuggingFace (`all-MiniLM-L6-v2`)  
- **Vector DB:** ChromaDB  

**Other Tools:**
- bcrypt (password hashing)  
- dotenv (env management)  
- requests (GitHub API)  

---

## ⚙️ Setup & Installation

### 1️⃣ Clone the Repository
```bash
git clone <your-repo-url>
cd <your-project-folder>


2️⃣ Create Virtual Environment
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

3️⃣ Install Dependencies
pip install -r requirements.txt
4️⃣ Setup Environment Variables

Create a .env file:

GITHUB_TOKEN=your_github_token
GEMINI_API_KEY=your_gemini_api_key
MONGO_URI=your_mongodb_connection_string
5️⃣ Run the Server
uvicorn updated:app --reload

Server runs on:
http://127.0.0.1:8000

📖 API Usage
🔐 Authentication

Signup

POST /signup

Login

POST /login

Returns JWT token for protected routes.

📂 Process GitHub Repo
POST /process

Body:

{
  "owner": "repo-owner",
  "repo": "repo-name"
}

➡️ Fetches, filters, and stores repo embeddings.

💬 Chat with Repo
POST /chat

Body:

{
  "owner": "repo-owner",
  "repo": "repo-name",
  "question": "Explain this project"
}
📄 Generate README
POST /readme

➡️ Auto-generates a professional README file.

🧠 How It Works
Fetch Repo Files
Uses GitHub API
Filters only useful files
Chunking
Splits code into smaller parts
Embedding
Converts text → vectors using HuggingFace
Storage
Saves vectors in ChromaDB
Query
Retrieves relevant chunks
Sends to Gemini for answer generation
