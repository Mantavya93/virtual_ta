from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import base64

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains.question_answering import load_qa_chain
from langchain.chat_models import ChatOpenAI

# Load environment variables
load_dotenv()
AIPIPE_TOKEN = os.getenv("OPENAI_API_KEY")
AIPIPE_EMBEDDING_URL = "https://aipipe.org/openai/v1"
AIPIPE_CHAT_URL = "https://aipipe.org/openrouter/v1"

if not AIPIPE_TOKEN:
    raise ValueError("OPENAI_API_KEY (AIPIPE_TOKEN) is missing. Please check your .env file.")

# Initialize FastAPI
app = FastAPI()

# Add root route for Railway health check
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <h2>✅ TDS Virtual TA is running</h2>
    <p>Visit <a href="/docs">/docs</a> to test the API.</p>
    """

# Allow all CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load FAISS vectorstore and chain
@app.on_event("startup")
def load_vectorstore():
    global qa_chain, vectorstore

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=None,
        openai_api_base=AIPIPE_EMBEDDING_URL,
        default_headers={"Authorization": f"Bearer {AIPIPE_TOKEN}"}
    )

    vs_course = FAISS.load_local(
        "data/faiss_index",
        embeddings,
        allow_dangerous_deserialization=True
    )

    vs_discourse = FAISS.load_local(
        "data/faiss_index_discourse",
        embeddings,
        allow_dangerous_deserialization=True
    )

    vs_course.merge_from(vs_discourse)
    vectorstore = vs_course

    llm = ChatOpenAI(
        model="openai/gpt-4o",
        openai_api_key=None,
        openai_api_base=AIPIPE_CHAT_URL,
        temperature=0,
        default_headers={"Authorization": f"Bearer {AIPIPE_TOKEN}"}
    )
    qa_chain = load_qa_chain(llm, chain_type="stuff")

@app.post("/api/")
async def ask_question(
    question: str = Form(...),
    image: str = Form(None)
):
    if image:
        try:
            image_data = base64.b64decode(image)
            # Future image processing
        except Exception as e:
            print("Failed to decode image:", e)

    docs = vectorstore.similarity_search(question, k=6)

    print("\n=== Retrieved Documents ===")
    if not docs:
        print("No documents found.")
        return {"response": "No relevant documents found.", "links": [], "images": []}
    for i, doc in enumerate(docs):
        print(f"Doc {i+1}: {doc.page_content[:300]}\n")

    response = qa_chain.run(input_documents=docs, question=question)

    fallback_phrases = [
        "i don't know",
        "no relevant answer",
        "i am not sure",
        "unable to help",
        "couldn't find",
        "don't have enough information"
    ]

    if not response or any(phrase in response.lower() for phrase in fallback_phrases):
        return {"response": "The system couldn't find a confident answer. Please try rephrasing.", "links": [], "images": []}

    links = []
    images = []
    for doc in docs:
        metadata = doc.metadata or {}
        source = metadata.get("source")
        if source and source not in links:
            links.append(source)
        image_link = metadata.get("image")
        if image_link and image_link not in images:
            images.append(image_link)

    return {
        "response": response,
        "links": links,
        "images": images
    }
