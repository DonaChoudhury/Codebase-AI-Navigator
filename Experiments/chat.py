import os
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 1. API Keys load karna
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ Error: GEMINI_API_KEY nahi mila! .env file check karo.")
    exit()

print("🧠 Vector Database aur Embeddings load ho rahe hain...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Purana ChromaDB folder load karna
vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 2}) 

print("🤖 Gemini AI model load ho raha hai...")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=GEMINI_API_KEY)

# 2. Naya Prompt Template (Simple aur clear)
template = """You are an expert Python developer assistant. 
Use the provided code context to answer the user's question. 
Explain it simply. If the answer is not in the context, say 'I don't know'.

Context: {context}

Question: {question}

Answer:"""
prompt = ChatPromptTemplate.from_template(template)

# Helper function: Code chunks ko text mein jodne ke liye
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# 3. Modern LCEL Chain (Bina 'chains' module ke!)
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

if __name__ == "__main__":
    print("\n💬 Setup Complete! AI se sawal puchte hain...\n")
    
    # Woh tricky sawal jisme humne directly "divide" ya "zero" use nahi kiya
    question = "What happens if someone tries to split a number by nothing?"
    print(f"👉 User Question: {question}\n")
    
    # AI se answer maangna
    answer = rag_chain.invoke(question)
    
    print("🤖 AI Answer:")
    print(answer)
    
    print("\n🔍 Context Sources (Kahan se padh ke bataya):")
    # Ye bas terminal mein print karne ke liye hai ki AI ne kaunsi file padhi
    docs = retriever.invoke(question)
    for doc in docs:
        print(f"- {doc.metadata['source']}")