import json
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import os

# Load course content
with open("data/tds_course_content.json", "r", encoding="utf-8") as f:
    course = json.load(f)

# Split into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
docs = []

for section in course:
    text = section["content"]
    metadata = {"title": section["title"]}
    splits = splitter.create_documents([text], metadatas=[metadata] * len(text))
    docs.extend(splits)

print(f"✅ Split {len(course)} sections into {len(docs)} chunks")

# Use AI Pipe for embeddings
embedding = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=os.environ["OPENAI_API_KEY"],
    base_url=os.environ.get("OPENAI_BASE_URL", "https://aipipe.org/openai/v1")
)

# Create vector store
vectorstore = FAISS.from_documents(docs, embedding)
vectorstore.save_local("data/vectorstore")
print("✅ Vectorstore saved to data/vectorstore")
