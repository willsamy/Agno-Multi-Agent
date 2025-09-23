"""
Endpoint HTTP para chat - Substitui WebSocket no Vercel
"""
import sys
import os
import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import the isolated agents
from agents import SupervisorAgent

# Create FastAPI app instance for API only
app = FastAPI(title="Agno Chat API", version="1.0.0")

# Initialize supervisor
supervisor = SupervisorAgent()

class ChatMessage(BaseModel):
    message: str
    conversation_id: str = None

@app.post("/api/chat")
async def chat_endpoint(chat_message: ChatMessage):
    """
    Endpoint HTTP para processar mensagens de chat
    Substitui a funcionalidade WebSocket para compatibilidade com Vercel
    """
    try:
        # Process the message using the supervisor
        response = await supervisor.process_request(chat_message.message)
        
        return JSONResponse(content={
            "success": True,
            "data": response,
            "conversation_id": chat_message.conversation_id
        })
        
    except Exception as e:
        print(f"❌ [CHAT API] Erro ao processar mensagem: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Erro interno do servidor: {str(e)}",
                "data": {
                    "type": "error",
                    "content": "Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente."
                }
            }
        )

@app.get("/api/health")
async def health_check():
    """Endpoint para verificar se a API está funcionando"""
    return {"status": "ok", "message": "Chat API funcionando"}

# Export the app for Vercel
handler = app