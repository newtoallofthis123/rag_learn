from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import uvicorn

from rag import CustomGeminiRAG

load_dotenv()
app = FastAPI()


class NlpSearch_Req(BaseModel):
    question: str


class Search_Req(BaseModel):
    query: str


google_api_key = os.environ.get("GOOGLE_GEMINI_API_KEY")
if google_api_key == "":
    print("Google Gemini API KEY is missing")
    exit(1)

print("Starting Blog indexing process")
rag = CustomGeminiRAG(google_api_key)
print("Done with indexing process")


@app.post("/search")
async def search(req: Search_Req):
    query = req.query
    relavent_context = rag.search(query)

    res = [
        {"url": doc.metadata["source"], "content": doc.page_content}
        for doc in relavent_context
    ]

    return res


@app.post("/ask")
async def ask(req: NlpSearch_Req):
    question = req.question

    return rag.ask(question)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
