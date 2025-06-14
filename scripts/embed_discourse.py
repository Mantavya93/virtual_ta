import os
import json
from dotenv import load_dotenv
from pathlib import Path
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

# Load env vars
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

def load_discussions(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    docs = []
    for item in data:
        metadata = {"source": item["url"]}
        docs.append(Document(page_content=item["content"], metadata=metadata))
    return docs

def main():
    print("📂 Loading scraped discussions...")
    docs = load_discussions("data/discourse_content.json")

    print("🔪 Splitting text into chunks...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(docs)

    print("🧠 Embedding using AI Pipe-compatible OpenAI endpoint...")
    embeddings = OpenAIEmbeddings(
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_BASE_URL
    )

    print("📦 Creating FAISS vector store...")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    save_path = Path("data/faiss_index_discourse")
    save_path.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(save_path))

    print(f"✅ Vectorstore saved to {save_path}")

if __name__ == "__main__":
    main()
