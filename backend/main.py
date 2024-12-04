from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os
from datetime import datetime

# Import your existing classes
from rag_assistant import RAGAssistant, Document
from utils.document_reader import DocumentReader
from utils.security import verify_api_key

app = FastAPI(title="Document AI API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Your React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store instances of RAGAssistant for each user session
assistants = {}

class Query(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    tokens_used: int

class DocumentResponse(BaseModel):
    success: bool
    message: str

@app.post("/api/initialize")
async def initialize_assistant(api_key: str):
    try:
        if api_key not in assistants:
            assistants[api_key] = RAGAssistant(api_key)
        return {"status": "success", "message": "Assistant initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    try:
        # Save uploaded file temporarily
        file_path = f"temp_{datetime.now().timestamp()}.pdf"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Process document
        assistant = assistants.get(api_key)
        if not assistant:
            raise HTTPException(status_code=400, detail="Assistant not initialized")

        success, message = assistant.add_document(file_path)

        # Clean up temporary file
        os.remove(file_path)

        return DocumentResponse(success=success, message=message)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/query", response_model=ChatResponse)
async def query_document(
    query: Query,
    api_key: str = Depends(verify_api_key)
):
    try:
        assistant = assistants.get(api_key)
        if not assistant:
            raise HTTPException(status_code=400, detail="Assistant not initialized")

        answer, tokens = assistant.query(query.question)
        return ChatResponse(answer=answer, tokens_used=tokens)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/chat-history")
async def get_chat_history(api_key: str = Depends(verify_api_key)):
    try:
        assistant = assistants.get(api_key)
        if not assistant:
            raise HTTPException(status_code=400, detail="Assistant not initialized")

        history = assistant.get_chat_history()
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/reset")
async def reset_knowledge_base(api_key: str = Depends(verify_api_key)):
    try:
        assistant = assistants.get(api_key)
        if not assistant:
            raise HTTPException(status_code=400, detail="Assistant not initialized")

        assistant.reset_knowledge_base()
        return {"status": "success", "message": "Knowledge base reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)