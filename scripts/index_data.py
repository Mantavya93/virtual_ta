import os
import json
from typing import List
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from openai import OpenAI
from langchain_core.embeddings import Embeddings

# Load environment variables from .env
load_dotenv()

DATA_PATH = "data/tds_course_content.json"
INDEX_PATH = "data/faiss_index"


class AIPipeEmbeddings(Embeddings):
    def __init__(self, model: str = "text-embedding-3-small", aipipe_key: str = None):
        self.model = model
        self.client = OpenAI(
            api_key=aipipe_key or os.getenv("OPENAI_API_KEY"),
            base_url="https://api.aipipe.ai/v1"
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embeddings.create(
            input=texts,
            model=self.model,
        )
        return [r.embedding for r in response.data]

    def embed_query(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            input=[text],
            model=self.model,
        )
        return response.data[0].embedding


def load_documents_from_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    documents = []
    for section in data:
        section_title = section.get("section_title", "")
        for item in section.get("items", []):
            title = item.get("title", "")
            content = item.get("content", "")
            full_text = f"{section_title}\n{title}\n{content}".strip()
            documents.append(Document(page_content=full_text))
    return documents


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100
    )
    return splitter.split_documents(documents)


def main():
    print("📚 Loading documents from JSON files...")
    docs = load_documents_from_json(DATA_PATH)
    print(f"✅ Loaded {len(docs)} total documents")

    print("✂️ Splitting documents into chunks...")
    chunks = split_documents(docs)
    print(f"✅ Split into {len(chunks)} chunks")

    print("🧠 Creating FAISS vectorstore with AIPipe embeddings...")
    embeddings = AIPipeEmbeddings()
    db = FAISS.from_documents(chunks, embeddings)

    print("💾 Saving to FAISS vectorstore...")
    db.save_local(INDEX_PATH)
    print(f"✅ Vectorstore saved to {INDEX_PATH}")


if __name__ == "__main__":
    main()
