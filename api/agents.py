"""
Agentes isolados para uso na API do Vercel
Evita dependências do app principal que requer diretório static
"""
import os
import json
import asyncio
import requests
import time
import random
from typing import Dict, Any
import google.generativeai as genai
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do sistema a partir do .env
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
BASE_DELAY = int(os.getenv("BASE_DELAY", "1"))
CODER_MAX_RETRIES = int(os.getenv("CODER_MAX_RETRIES", "3"))
CODER_BASE_DELAY = int(os.getenv("CODER_BASE_DELAY", "2"))
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
VERBOSE_LOGS = os.getenv("VERBOSE_LOGS", "true").lower() == "true"

# Configuração de chaves de API por nível
class APIConfig:
    def __init__(self):
        self.api_keys = {
            'base': {
                'primary': os.getenv("API_BASE_1"),
                'backup': os.getenv("API_BASE_2")
            },
            'medio': {
                'primary': os.getenv("API_MEDIO_1"),
                'backup': os.getenv("API_MEDIO_2")
            },
            'avancado': {
                'primary': os.getenv("API_AVANCADO_1"),
                'backup': os.getenv("API_AVANCADO_2")
            }
        }
    
    def get_api_key(self, level: str, use_backup: bool = False) -> str:
        """Retorna a chave de API para o nível especificado"""
        key_type = 'backup' if use_backup else 'primary'
        return self.api_keys[level][key_type]
    
    def configure_api(self, level: str, use_backup: bool = False) -> bool:
        """Configura a API do Google Gemini com a chave apropriada"""
        try:
            api_key = self.get_api_key(level, use_backup)
            if not api_key:
                print(f"❌ [API CONFIG] Chave de API não encontrada para nível {level}")
                return False
            
            genai.configure(api_key=api_key)
            print(f"✅ [API CONFIG] Configurado para nível {level} ({'backup' if use_backup else 'primary'})")
            return True
        except Exception as e:
            print(f"❌ [API CONFIG] Erro ao configurar API: {str(e)}")
            return False

# Instância global da configuração de API
api_config = APIConfig()

async def retry_with_backoff(func, *args, max_retries=None, base_delay=None, **kwargs):
    """
    Executa uma função com retry e backoff exponencial
    """
    if max_retries is None:
        max_retries = MAX_RETRIES
    if base_delay is None:
        base_delay = BASE_DELAY
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                if VERBOSE_LOGS:
                    print(f"⚠️ [RETRY] Tentativa {attempt + 1} falhou: {str(e)}. Tentando novamente em {delay:.2f}s...")
                await asyncio.sleep(delay)
            else:
                if VERBOSE_LOGS:
                    print(f"❌ [RETRY] Todas as {max_retries + 1} tentativas falharam")
    
    raise last_exception

# Modelos por nível
MODEL_BASE = os.getenv("MODEL_BASE", "gemini-2.5-flash-lite")
MODEL_MEDIO = os.getenv("MODEL_MEDIO", "gemini-2.5-flash")
MODEL_AVANCADO = os.getenv("MODEL_AVANCADO", "gemini-2.5-pro")

class ResearchAgent:
    def __init__(self, model_level: str = "base"):
        self.model_level = model_level
        self.model_name = MODEL_BASE if model_level == "base" else MODEL_MEDIO if model_level == "medio" else MODEL_AVANCADO

    async def research(self, query: str) -> Dict[str, Any]:
        """Realiza pesquisa usando Google Search API"""
        try:
            # Configurar API para o nível apropriado
            if not api_config.configure_api(self.model_level):
                # Tentar com backup
                if not api_config.configure_api(self.model_level, use_backup=True):
                    return {
                        "type": "error",
                        "content": "Erro na configuração da API de pesquisa",
                        "details": "Não foi possível configurar as chaves de API"
                    }

            # Simular pesquisa (implementação simplificada para o Vercel)
            research_prompt = f"""
            Você é um agente de pesquisa especializado. Forneça informações detalhadas e precisas sobre: {query}
            
            Inclua:
            - Informações principais sobre o tópico
            - Dados relevantes e atuais
            - Fontes confiáveis quando possível
            - Contexto importante
            
            Seja preciso, informativo e objetivo.
            """

            model = genai.GenerativeModel(self.model_name)
            response = await retry_with_backoff(
                model.generate_content,
                research_prompt,
                max_retries=MAX_RETRIES,
                base_delay=BASE_DELAY
            )

            return {
                "type": "research",
                "content": response.text,
                "query": query,
                "model_used": self.model_name
            }

        except Exception as e:
            print(f"❌ [RESEARCH] Erro na pesquisa: {str(e)}")
            return {
                "type": "error",
                "content": f"Erro na pesquisa: {str(e)}",
                "query": query
            }

class CoderAgent:
    def __init__(self, model_level: str = "medio"):
        self.model_level = model_level
        self.model_name = MODEL_MEDIO if model_level == "medio" else MODEL_AVANCADO if model_level == "avancado" else MODEL_BASE

    def _extract_code_blocks(self, content: str) -> Dict[str, str]:
        """Extrai blocos de código do conteúdo gerado"""
        code_blocks = {}
        lines = content.split('\n')
        current_file = None
        current_code = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```'):
                if in_code_block:
                    if current_file:
                        code_blocks[current_file] = '\n'.join(current_code)
                    current_code = []
                    in_code_block = False
                else:
                    in_code_block = True
            elif in_code_block:
                if line.strip().startswith('# ') and line.strip().endswith('.html'):
                    current_file = line.strip()[2:]
                elif line.strip().startswith('/* ') and line.strip().endswith(' */'):
                    current_file = line.strip()[3:-3]
                else:
                    current_code.append(line)
        
        return {
            "html": content,  # Retorna todo o conteúdo como HTML por padrão
            "css": "",
            "js": ""
        }

    async def create_website(self, description: str) -> Dict[str, Any]:
        """Cria um website completo baseado na descrição"""
        try:
            # Configurar API para o nível apropriado
            if not api_config.configure_api(self.model_level):
                if not api_config.configure_api(self.model_level, use_backup=True):
                    return {
                        "type": "error",
                        "content": "Erro na configuração da API de desenvolvimento",
                        "details": "Não foi possível configurar as chaves de API"
                    }

            coding_prompt = f"""
            Você é um desenvolvedor web especializado. Crie um website completo e funcional baseado nesta descrição: {description}

            Requisitos:
            - HTML5 semântico e bem estruturado
            - CSS moderno com design responsivo
            - JavaScript funcional quando necessário
            - Design atrativo e profissional
            - Código limpo e comentado
            - Compatibilidade com navegadores modernos

            Forneça o código completo em um único arquivo HTML com CSS e JavaScript inline.
            Use apenas tecnologias web padrão (HTML, CSS, JavaScript).
            """

            model = genai.GenerativeModel(self.model_name)
            response = await retry_with_backoff(
                model.generate_content,
                coding_prompt,
                max_retries=CODER_MAX_RETRIES,
                base_delay=CODER_BASE_DELAY
            )

            code_blocks = self._extract_code_blocks(response.text)

            return {
                "type": "website",
                "content": response.text,
                "code": code_blocks,
                "description": description,
                "model_used": self.model_name
            }

        except Exception as e:
            print(f"❌ [CODER] Erro na criação do website: {str(e)}")
            return {
                "type": "error",
                "content": f"Erro na criação do website: {str(e)}",
                "description": description
            }

class SupervisorAgent:
    def __init__(self):
        self.research_agent = ResearchAgent(model_level="base")
        self.coder_agent = CoderAgent(model_level="medio")
        self.model_level = "avancado"
        self.model_name = MODEL_AVANCADO

    async def process_request(self, message: str) -> Dict[str, Any]:
        """Processa a requisição do usuário e decide qual agente usar"""
        try:
            # Configurar API para análise
            if not api_config.configure_api(self.model_level):
                if not api_config.configure_api(self.model_level, use_backup=True):
                    return {
                        "type": "error",
                        "content": "Erro na configuração da API principal",
                        "details": "Não foi possível configurar as chaves de API"
                    }

            # Analisar a intenção do usuário
            analysis_prompt = f"""
            Analise esta mensagem do usuário e determine a melhor ação: "{message}"

            Opções:
            1. RESEARCH - Se o usuário quer informações, pesquisa, dados, explicações
            2. CODE - Se o usuário quer criar website, aplicação, código
            3. CHAT - Se é uma conversa geral, saudação, ou pergunta simples

            Responda apenas com: RESEARCH, CODE, ou CHAT
            """

            model = genai.GenerativeModel(self.model_name)
            analysis_response = await retry_with_backoff(
                model.generate_content,
                analysis_prompt,
                max_retries=MAX_RETRIES,
                base_delay=BASE_DELAY
            )

            intent = analysis_response.text.strip().upper()

            if "RESEARCH" in intent:
                return await self.research_agent.research(message)
            elif "CODE" in intent:
                return await self.coder_agent.create_website(message)
            else:
                # Chat geral
                chat_prompt = f"""
                Você é Agno, um assistente inteligente e prestativo. Responda de forma amigável e útil: {message}
                
                Seja conversacional, informativo e mantenha um tom profissional mas acessível.
                """

                chat_response = await retry_with_backoff(
                    model.generate_content,
                    chat_prompt,
                    max_retries=MAX_RETRIES,
                    base_delay=BASE_DELAY
                )

                return {
                    "type": "chat",
                    "content": chat_response.text,
                    "message": message,
                    "model_used": self.model_name
                }

        except Exception as e:
            print(f"❌ [SUPERVISOR] Erro no processamento: {str(e)}")
            return {
                "type": "error",
                "content": f"Desculpe, ocorreu um erro ao processar sua mensagem: {str(e)}",
                "message": message
            }