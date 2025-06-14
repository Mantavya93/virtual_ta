from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains.question_answering import load_qa_chain
import os
import base64

# Load .env
load_dotenv()
AIPIPE_TOKEN = os.getenv("OPENAI_API_KEY")
AIPIPE_EMBEDDING_URL = "https://aipipe.org/openai/v1"
AIPIPE_CHAT_URL = "https://aipipe.org/openrouter/v1"

if not AIPIPE_TOKEN:
    raise ValueError("Missing OPENAI_API_KEY in .env")

# Initialize FastAPI
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global objects
vectorstore = None
qa_chain = None

@app.on_event("startup")
def load_models():
    global vectorstore, qa_chain

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=None,
        openai_api_base=AIPIPE_EMBEDDING_URL,
        default_headers={"Authorization": f"Bearer {AIPIPE_TOKEN}"}
    )

    vs_course = FAISS.load_local(
        "data/faiss_index", embeddings, allow_dangerous_deserialization=True
    )
    vs_discourse = FAISS.load_local(
        "data/faiss_index_discourse", embeddings, allow_dangerous_deserialization=True
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

# Health check route
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <h2>✅ TDS Virtual TA is running</h2>
    <p>Visit <a href="/docs">/docs</a> to test the API.</p>
    """

# POST alias for project evaluator compatibility
@app.post("/")
async def ask_question_alias(request: Request):
    form = await request.form()
    question = form.get("question")
    image = form.get("image")
    return await ask_question(question, image)

# Actual question answer route
@app.post("/api/")
async def ask_question(
    question: str = Form(...),
    image: str = Form(None)
):
    if image:
        try:
            _ = base64.b64decode(image)
            # Image processing not implemented
        except Exception as e:
            print("Image decode failed:", e)

    docs = vectorstore.similarity_search(question, k=6)

    if not docs:
        return {"response": "No relevant documents found.", "links": [], "images": []}

    response = qa_chain.run(input_documents=docs, question=question)

    fallback_phrases = [
        "i don't know", "no relevant answer", "i am not sure",
        "unable to help", "couldn't find", "don't have enough information"
    ]

    if not response or any(p in response.lower() for p in fallback_phrases):
        return {"response": "The system couldn't find a confident answer. Please try rephrasing.", "links": [], "images": []}

    links, images = [], []
    for doc in docs:
        source = doc.metadata.get("source")
        image_link = doc.metadata.get("image")
        if source and source not in links:
            links.append(source)
        if image_link and image_link not in images:
            images.append(image_link)

    return {
        "response": response,
        "links": links,
        "images": images
    }
