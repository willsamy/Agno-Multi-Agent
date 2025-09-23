"""
Endpoint HTTP para chat - Substitui WebSocket no Vercel
"""
import sys
import os
import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Remover importação direta para evitar falhas na inicialização em ambientes serverless
# from agents import SupervisorAgent

# Create FastAPI app instance for API only
app = FastAPI(title="Agno Chat API", version="1.0.0")

# Implementar importação lazy do SupervisorAgent
_supervisor = None

def get_supervisor():
    global _supervisor
    if _supervisor is None:
        try:
            from agents import SupervisorAgent
            _supervisor = SupervisorAgent()
        except Exception as e:
            # Logar erro sem quebrar endpoints simples como /api/health
            print(f"❌ [INIT] Falha ao inicializar SupervisorAgent: {str(e)}")
            _supervisor = None
    return _supervisor

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
        supervisor = get_supervisor()
        if supervisor is None:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Erro ao inicializar os agentes",
                    "data": {
                        "type": "error",
                        "content": "Não foi possível inicializar o SupervisorAgent. Verifique as dependências e configurações em produção."
                    }
                }
            )

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