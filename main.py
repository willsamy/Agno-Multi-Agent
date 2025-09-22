import os
import json
import asyncio
import requests
import time
import random
from typing import Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
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
        """Configura a API com a chave apropriada para o nível"""
        api_key = self.get_api_key(level, use_backup)
        if api_key and api_key.strip():
            try:
                genai.configure(api_key=api_key)
                return True
            except Exception as e:
                print(f"❌ [API] Erro ao configurar API para nível {level}: {e}")
                return False
        return False

# Inicializar configuração de API
api_config = APIConfig()

# Função para retry com backoff exponencial
async def retry_with_backoff(func, *args, max_retries=None, base_delay=None, **kwargs):
    if max_retries is None:
        max_retries = MAX_RETRIES
    if base_delay is None:
        base_delay = BASE_DELAY
    """
    Executa uma função com retry automático em caso de erro 500 da API
    """
    for attempt in range(max_retries):
        try:
            print(f"🔄 [RETRY] Tentativa {attempt + 1}/{max_retries}")
            result = await asyncio.to_thread(func, *args, **kwargs)
            print(f"✅ [RETRY] Sucesso na tentativa {attempt + 1}")
            return result
        except Exception as e:
            error_msg = str(e).lower()
            print(f"❌ [RETRY] Erro na tentativa {attempt + 1}: {str(e)}")
            
            # Verificar se é erro 500 ou erro interno da API
            if "500" in error_msg or "internal error" in error_msg or "retry" in error_msg:
                if attempt < max_retries - 1:
                    # Calcular delay com backoff exponencial + jitter
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"⏳ [RETRY] Aguardando {delay:.2f}s antes da próxima tentativa...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    print(f"💥 [RETRY] Todas as tentativas falharam. Usando fallback.")
                    raise e
            else:
                # Se não é erro 500, não tentar novamente
                print(f"🚫 [RETRY] Erro não relacionado a API 500, não tentando novamente")
                raise e
    
    raise Exception("Máximo de tentativas excedido")

# Criar app FastAPI
app = FastAPI(title="Agno Multi-Agent System", version="1.0.0")

# Servir arquivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configurar modelos Gemini a partir do .env
MODEL_BASE = os.getenv("MODEL_BASE", "gemini-2.5-flash-lite")
MODEL_MEDIO = os.getenv("MODEL_MEDIO", "gemini-2.5-flash")
MODEL_AVANCADO = os.getenv("MODEL_AVANCADO", "gemini-2.5-pro")

class ResearchAgent:
    def __init__(self, model_level: str = "base"):
        self.model_level = model_level
        self.model_name = MODEL_BASE if model_level == "base" else MODEL_MEDIO if model_level == "medio" else MODEL_AVANCADO
    
    async def research(self, query: str) -> Dict[str, Any]:
        try:
            # Configurar API para o nível apropriado
            if not api_config.configure_api(self.model_level):
                # Tentar backup se a primária falhar
                if not api_config.configure_api(self.model_level, use_backup=True):
                    return {
                        "type": "research",
                        "query": query,
                        "results": "Erro: Nenhuma chave de API válida disponível para pesquisa",
                        "sources": []
                    }
            
            model = genai.GenerativeModel(self.model_name)
            
            prompt = f"""
            Realize uma pesquisa completa sobre: {query}
            
            Forneça:
            1. Resumo dos principais achados
            2. Dados relevantes e insights
            3. Fontes confiáveis (simuladas)
            4. Links úteis
            
            Formato em texto claro e estruturado.
            """
            
            response = await retry_with_backoff(model.generate_content, prompt)
            
            return {
                "type": "research",
                "query": query,
                "results": response.text,
                "sources": [
                    "https://exemplo.com/fonte1",
                    "https://exemplo.com/fonte2",
                    "https://exemplo.com/fonte3"
                ]
            }
        except Exception as e:
            return {
                "type": "research",
                "query": query,
                "results": f"Erro na pesquisa: {str(e)}",
                "sources": []
            }

class CoderAgent:
    def __init__(self, model_level: str = "medio"):
        self.model_level = model_level
        self.model_name = MODEL_BASE if model_level == "base" else MODEL_MEDIO if model_level == "medio" else MODEL_AVANCADO
    
    def _extract_code_blocks(self, content: str) -> Dict[str, str]:
        import re
        
        html_match = re.search(r'```html\s*\n(.*?)\n```', content, re.DOTALL)
        css_match = re.search(r'```css\s*\n(.*?)\n```', content, re.DOTALL)
        js_match = re.search(r'```javascript\s*\n(.*?)\n```', content, re.DOTALL)
        
        # Se não encontrar blocos, tentar extrair HTML
        if not html_match:
            html_match = re.search(r'<html[\s\S]*?</html>', content, re.DOTALL)
        
        return {
            "html": html_match.group(1) if html_match else "",
            "css": css_match.group(1) if css_match else "",
            "js": js_match.group(1) if js_match else ""
        }
    
    async def create_website(self, description: str) -> Dict[str, Any]:
        try:
            print(f"🌐 [CODER] Iniciando criação de website: {description}")
            
            # Determinar se é um tema específico de IA
            is_ai_theme = any(keyword in description.lower() for keyword in [
                'inteligência artificial', 'ia', 'artificial intelligence', 'ai', 
                'machine learning', 'deep learning', 'futuro', 'tecnologia',
                'automação', 'robôs', 'algoritmos'
            ])
            
            print(f"🤖 [CODER] Tema de IA detectado: {is_ai_theme}")
            
            # Prompt específico para IA se o tema for sobre inteligência artificial
            if "inteligência artificial" in description.lower() or "ia" in description.lower() or "artificial intelligence" in description.lower():
                prompt = f"""
                Crie um site simples e profissional sobre Inteligência Artificial.
                Inclua seções básicas: introdução, benefícios, desafios e futuro.
                Use design moderno com cores azul e roxo, ícones Font Awesome e animações suaves.
                Retorne APENAS o código HTML completo com CSS e JS integrados.
                """
            else:
                prompt = f"""
                Crie um site simples e profissional sobre: "{description}".
                Inclua HTML5, CSS3 responsivo e JS para interatividade.
                Adicione seções: header, hero, conteúdo principal e footer.
                Use conteúdo real, design moderno e ícones Font Awesome.
                Retorne APENAS o código HTML completo.
                """
            
            # Configurar API para o nível apropriado
            if not api_config.configure_api(self.model_level):
                # Tentar backup se a primária falhar
                if not api_config.configure_api(self.model_level, use_backup=True):
                    return {
                        "type": "website",
                        "description": description,
                        "html": "<html><body><h1>Erro: Nenhuma chave de API válida disponível para criação de website</h1></body></html>",
                        "css": "",
                        "js": "",
                        "status": "error"
                    }
            
            model = genai.GenerativeModel(self.model_name)
            
            print("🤖 [CODER] Enviando prompt para o modelo com sistema de retry...")
            response = await retry_with_backoff(model.generate_content, prompt, max_retries=CODER_MAX_RETRIES, base_delay=CODER_BASE_DELAY)
            print(f"✅ [CODER] Resposta recebida do modelo (tamanho: {len(response.text)} chars)")
            
            # Extrair apenas o HTML, removendo texto extra
            html_content = response.text.strip()
            print(f"🔧 [CODER] HTML extraído (tamanho: {len(html_content)} chars)")
            
            # Remover texto explicativo que pode aparecer antes ou depois do HTML
            import re
            
            # Procurar pelo HTML completo
            html_match = re.search(r'<!DOCTYPE html>.*?</html>', html_content, re.DOTALL | re.IGNORECASE)
            if html_match:
                html_content = html_match.group()
            elif "<html" in html_content.lower():
                # Se não tem DOCTYPE, procurar pela tag html
                html_match = re.search(r'<html.*?</html>', html_content, re.DOTALL | re.IGNORECASE)
                if html_match:
                    html_content = "<!DOCTYPE html>\n" + html_match.group()
            
            # Se ainda não tem HTML válido, criar um site específico baseado no tema
            if "<!DOCTYPE html>" not in html_content.upper() and "<html" not in html_content.lower():
                if "inteligência artificial" in description.lower() or "ia" in description.lower():
                    # Site específico sobre IA
                    html_content = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>O Futuro da Inteligência Artificial</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Inter', 'Segoe UI', sans-serif; 
            line-height: 1.6; 
            color: #1a1a1a; 
            background: linear-gradient(135deg, #1e3a8a 0%, #7c3aed 50%, #1e3a8a 100%);
            min-height: 100vh;
            overflow-x: hidden;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }
        
        /* Header */
        header { 
            background: rgba(255,255,255,0.1); 
            backdrop-filter: blur(20px);
            color: white; 
            padding: 1rem 0; 
            position: fixed;
            width: 100%;
            top: 0;
            z-index: 1000;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        nav { display: flex; justify-content: space-between; align-items: center; }
        .logo { font-size: 1.5rem; font-weight: bold; }
        .nav-links { display: flex; list-style: none; gap: 2rem; }
        .nav-links a { color: white; text-decoration: none; transition: all 0.3s; }
        .nav-links a:hover { color: #60a5fa; }
        
        /* Hero Section */
        .hero { 
            padding: 8rem 0 4rem; 
            text-align: center; 
            color: white;
            position: relative;
        }
        .hero::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="20" cy="20" r="2" fill="rgba(255,255,255,0.1)"/><circle cx="80" cy="40" r="1" fill="rgba(255,255,255,0.1)"/><circle cx="40" cy="80" r="1.5" fill="rgba(255,255,255,0.1)"/></svg>');
            animation: float 20s infinite linear;
        }
        @keyframes float { 0% { transform: translateY(0px); } 100% { transform: translateY(-100px); } }
        
        .hero h1 { 
            font-size: 4rem; 
            margin-bottom: 1rem; 
            background: linear-gradient(45deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: glow 2s ease-in-out infinite alternate;
        }
        @keyframes glow { from { filter: drop-shadow(0 0 20px rgba(96, 165, 250, 0.5)); } to { filter: drop-shadow(0 0 30px rgba(167, 139, 250, 0.8)); } }
        
        .hero p { font-size: 1.3rem; margin-bottom: 2rem; opacity: 0.9; }
        .cta-btn { 
            display: inline-block; 
            padding: 15px 40px; 
            background: linear-gradient(45deg, #3b82f6, #8b5cf6);
            color: white; 
            text-decoration: none; 
            border-radius: 50px; 
            transition: all 0.3s ease;
            box-shadow: 0 10px 30px rgba(59, 130, 246, 0.3);
            position: relative;
            overflow: hidden;
        }
        .cta-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }
        .cta-btn:hover::before { left: 100%; }
        .cta-btn:hover { transform: translateY(-3px); box-shadow: 0 15px 40px rgba(59, 130, 246, 0.4); }
        
        /* Sections */
        .section { 
            background: white; 
            margin: 2rem 0; 
            padding: 4rem 0; 
            border-radius: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.1);
            position: relative;
        }
        .section-title { 
            text-align: center; 
            font-size: 2.5rem; 
            margin-bottom: 3rem; 
            color: #1e3a8a;
            position: relative;
        }
        .section-title::after {
            content: '';
            position: absolute;
            bottom: -10px;
            left: 50%;
            transform: translateX(-50%);
            width: 80px;
            height: 4px;
            background: linear-gradient(45deg, #3b82f6, #8b5cf6);
            border-radius: 2px;
        }
        
        /* Cards Grid */
        .cards-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 2rem; 
            margin: 2rem 0; 
        }
        .card { 
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            padding: 2rem; 
            border-radius: 20px; 
            text-align: center;
            transition: all 0.3s ease;
            border: 1px solid rgba(59, 130, 246, 0.1);
            position: relative;
            overflow: hidden;
        }
        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(45deg, #3b82f6, #8b5cf6);
        }
        .card:hover { 
            transform: translateY(-10px); 
            box-shadow: 0 20px 40px rgba(59, 130, 246, 0.2);
        }
        .card i { 
            font-size: 3rem; 
            color: #3b82f6; 
            margin-bottom: 1rem;
            display: block;
        }
        .card h3 { color: #1e3a8a; margin-bottom: 1rem; }
        
        /* Stats Section */
        .stats { 
            background: linear-gradient(135deg, #1e3a8a 0%, #7c3aed 100%);
            color: white;
            text-align: center;
            padding: 4rem 0;
            margin: 2rem 0;
            border-radius: 30px;
        }
        .stats-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 2rem; 
        }
        .stat-item h3 { 
            font-size: 3rem; 
            margin-bottom: 0.5rem;
            background: linear-gradient(45deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        /* Timeline */
        .timeline { position: relative; padding: 2rem 0; }
        .timeline::before {
            content: '';
            position: absolute;
            left: 50%;
            top: 0;
            bottom: 0;
            width: 4px;
            background: linear-gradient(to bottom, #3b82f6, #8b5cf6);
            transform: translateX(-50%);
        }
        .timeline-item {
            position: relative;
            margin: 2rem 0;
            padding: 0 2rem;
        }
        .timeline-item:nth-child(odd) { text-align: right; }
        .timeline-item:nth-child(even) { text-align: left; margin-left: 50%; }
        .timeline-content {
            background: white;
            padding: 1.5rem;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            position: relative;
        }
        
        /* Footer */
        footer { 
            background: rgba(0,0,0,0.9); 
            color: white; 
            text-align: center; 
            padding: 3rem 0; 
            margin-top: 2rem; 
        }
        .footer-content { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 2rem; margin-bottom: 2rem; }
        .footer-section h3 { color: #60a5fa; margin-bottom: 1rem; }
        
        /* Responsive */
        @media (max-width: 768px) {
            .hero h1 { font-size: 2.5rem; }
            .nav-links { display: none; }
            .timeline::before { left: 20px; }
            .timeline-item { margin-left: 40px !important; text-align: left !important; }
        }
        
        /* Animations */
        .fade-in { opacity: 0; transform: translateY(30px); transition: all 0.6s ease; }
        .fade-in.visible { opacity: 1; transform: translateY(0); }
    </style>
</head>
<body>
    <header>
        <nav class="container">
            <div class="logo"><i class="fas fa-brain"></i> IA Futuro</div>
            <ul class="nav-links">
                <li><a href="#home">Início</a></li>
                <li><a href="#about">Sobre IA</a></li>
                <li><a href="#impact">Impacto</a></li>
                <li><a href="#future">Futuro</a></li>
            </ul>
        </nav>
    </header>

    <main>
        <section class="hero" id="home">
            <div class="container">
                <h1>O Futuro da Inteligência Artificial</h1>
                <p>Como a IA está transformando o mundo do trabalho e redefinindo o futuro da humanidade</p>
                <a href="#about" class="cta-btn"><i class="fas fa-rocket"></i> Explore o Futuro</a>
            </div>
        </section>

        <section class="section" id="about">
            <div class="container">
                <h2 class="section-title fade-in">O que é Inteligência Artificial?</h2>
                <div class="cards-grid">
                    <div class="card fade-in">
                        <i class="fas fa-brain"></i>
                        <h3>Machine Learning</h3>
                        <p>Algoritmos que aprendem com dados para fazer previsões e tomar decisões sem programação explícita.</p>
                    </div>
                    <div class="card fade-in">
                        <i class="fas fa-network-wired"></i>
                        <h3>Deep Learning</h3>
                        <p>Redes neurais profundas que simulam o funcionamento do cérebro humano para resolver problemas complexos.</p>
                    </div>
                    <div class="card fade-in">
                        <i class="fas fa-comments"></i>
                        <h3>Processamento de Linguagem</h3>
                        <p>Capacidade de entender, interpretar e gerar linguagem humana, como ChatGPT e assistentes virtuais.</p>
                    </div>
                </div>
            </div>
        </section>

        <section class="stats">
            <div class="container">
                <h2 class="section-title" style="color: white;">IA em Números</h2>
                <div class="stats-grid">
                    <div class="stat-item">
                        <h3 class="counter" data-target="85">0</h3>
                        <p>% das empresas usam IA</p>
                    </div>
                    <div class="stat-item">
                        <h3 class="counter" data-target="375">0</h3>
                        <p>Milhões de empregos criados</p>
                    </div>
                    <div class="stat-item">
                        <h3 class="counter" data-target="40">0</h3>
                        <p>% aumento de produtividade</p>
                    </div>
                    <div class="stat-item">
                        <h3 class="counter" data-target="2030">0</h3>
                        <p>Ano da revolução IA</p>
                    </div>
                </div>
            </div>
        </section>

        <section class="section" id="impact">
            <div class="container">
                <h2 class="section-title fade-in">Impacto no Mercado de Trabalho</h2>
                <div class="cards-grid">
                    <div class="card fade-in">
                        <i class="fas fa-robot" style="color: #ef4444;"></i>
                        <h3>Profissões Automatizadas</h3>
                        <p>Operadores de máquinas, caixas, motoristas e trabalhos repetitivos serão gradualmente automatizados.</p>
                    </div>
                    <div class="card fade-in">
                        <i class="fas fa-lightbulb" style="color: #10b981;"></i>
                        <h3>Novas Profissões</h3>
                        <p>Engenheiros de IA, especialistas em ética digital, analistas de dados e desenvolvedores de IA.</p>
                    </div>
                    <div class="card fade-in">
                        <i class="fas fa-handshake" style="color: #3b82f6;"></i>
                        <h3>Colaboração Humano-IA</h3>
                        <p>O futuro será de colaboração, onde humanos e IA trabalham juntos para maximizar resultados.</p>
                    </div>
                </div>
            </div>
        </section>

        <section class="section" id="future">
            <div class="container">
                <h2 class="section-title fade-in">Preparando-se para o Futuro</h2>
                <div class="timeline">
                    <div class="timeline-item fade-in">
                        <div class="timeline-content">
                            <h3>Educação Continuada</h3>
                            <p>Mantenha-se atualizado com cursos online, certificações e aprendizado constante em tecnologia.</p>
                        </div>
                    </div>
                    <div class="timeline-item fade-in">
                        <div class="timeline-content">
                            <h3>Habilidades Humanas</h3>
                            <p>Desenvolva criatividade, inteligência emocional, pensamento crítico e habilidades de comunicação.</p>
                        </div>
                    </div>
                    <div class="timeline-item fade-in">
                        <div class="timeline-content">
                            <h3>Adaptabilidade</h3>
                            <p>Seja flexível e aberto a mudanças. A capacidade de se adaptar será crucial no futuro.</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </main>

    <footer>
        <div class="container">
            <div class="footer-content">
                <div class="footer-section">
                    <h3><i class="fas fa-brain"></i> IA Futuro</h3>
                    <p>Explorando o futuro da inteligência artificial e seu impacto na sociedade.</p>
                </div>
                <div class="footer-section">
                    <h3>Links Úteis</h3>
                    <p><a href="#" style="color: #60a5fa;">Cursos de IA</a></p>
                    <p><a href="#" style="color: #60a5fa;">Pesquisas</a></p>
                    <p><a href="#" style="color: #60a5fa;">Notícias</a></p>
                </div>
                <div class="footer-section">
                    <h3>Contato</h3>
                    <p><i class="fas fa-envelope"></i> contato@iafuturo.com</p>
                    <p><i class="fas fa-phone"></i> (11) 9999-9999</p>
                </div>
            </div>
            <p>&copy; 2024 IA Futuro | O futuro da inteligência artificial está aqui</p>
        </div>
    </footer>

    <script>
        // Smooth scrolling
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });

        // Fade in animation on scroll
        const observerOptions = { threshold: 0.1, rootMargin: '0px 0px -50px 0px' };
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, observerOptions);

        document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));

        // Counter animation
        function animateCounters() {
            const counters = document.querySelectorAll('.counter');
            counters.forEach(counter => {
                const target = parseInt(counter.getAttribute('data-target'));
                const increment = target / 100;
                let current = 0;
                
                const updateCounter = () => {
                    if (current < target) {
                        current += increment;
                        counter.textContent = Math.floor(current);
                        requestAnimationFrame(updateCounter);
                    } else {
                        counter.textContent = target;
                    }
                };
                updateCounter();
            });
        }

        // Start counter animation when stats section is visible
        const statsSection = document.querySelector('.stats');
        const statsObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCounters();
                    statsObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });

        if (statsSection) statsObserver.observe(statsSection);

        // Header background on scroll
        window.addEventListener('scroll', () => {
            const header = document.querySelector('header');
            if (window.scrollY > 100) {
                header.style.background = 'rgba(30, 58, 138, 0.95)';
            } else {
                header.style.background = 'rgba(255,255,255,0.1)';
            }
        });
    </script>
</body>
</html>"""
                else:
                    # Site genérico melhorado
                    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{description}</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            line-height: 1.6; 
            color: #333; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 0 20px; }}
        header {{ 
            background: rgba(255,255,255,0.1); 
            backdrop-filter: blur(10px);
            color: white; 
            padding: 2rem 0; 
            text-align: center; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .hero {{ 
            padding: 4rem 0; 
            text-align: center; 
            color: white;
        }}
        .hero h2 {{ font-size: 3rem; margin-bottom: 1rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }}
        .hero p {{ font-size: 1.2rem; margin-bottom: 2rem; }}
        .btn {{ 
            display: inline-block; 
            padding: 12px 30px; 
            background: #ff6b6b; 
            color: white; 
            text-decoration: none; 
            border-radius: 50px; 
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(255,107,107,0.3);
        }}
        .btn:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px rgba(255,107,107,0.4); }}
        .content {{ 
            background: white; 
            margin: 2rem 0; 
            padding: 3rem 0; 
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        .features {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; margin: 2rem 0; }}
        .feature {{ text-align: center; padding: 2rem; background: #f8f9fa; border-radius: 15px; }}
        .feature i {{ font-size: 3rem; color: #667eea; margin-bottom: 1rem; }}
        footer {{ 
            background: rgba(0,0,0,0.8); 
            color: white; 
            text-align: center; 
            padding: 2rem 0; 
            margin-top: 2rem; 
        }}
        @media (max-width: 768px) {{
            .hero h2 {{ font-size: 2rem; }}
            .features {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1><i class="fas fa-star"></i> {description.title()}</h1>
        </div>
    </header>
    <main>
        <section class="hero">
            <div class="container">
                <h2>Explore o Futuro</h2>
                <p>Descubra tudo sobre {description} em um site moderno e interativo</p>
                <a href="#content" class="btn"><i class="fas fa-arrow-down"></i> Saiba Mais</a>
            </div>
        </section>
        <section class="content" id="content">
            <div class="container">
                <h3 style="text-align: center; margin-bottom: 3rem; font-size: 2.5rem; color: #333;">Principais Características</h3>
                <div class="features">
                    <div class="feature">
                        <i class="fas fa-rocket"></i>
                        <h4>Inovação</h4>
                        <p>Tecnologia de ponta aplicada a {description}</p>
                    </div>
                    <div class="feature">
                        <i class="fas fa-users"></i>
                        <h4>Comunidade</h4>
                        <p>Conecte-se com especialistas e entusiastas</p>
                    </div>
                    <div class="feature">
                        <i class="fas fa-chart-line"></i>
                        <h4>Crescimento</h4>
                        <p>Acompanhe as últimas tendências e desenvolvimentos</p>
                    </div>
                </div>
            </div>
        </section>
    </main>
    <footer>
        <div class="container">
            <p>&copy; 2024 - {description.title()} | Desenvolvido com <i class="fas fa-heart" style="color: #ff6b6b;"></i></p>
        </div>
    </footer>
    <script>
        // Smooth scrolling
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({{
                    behavior: 'smooth'
                }});
            }});
        }});
        
        // Add animation on scroll
        window.addEventListener('scroll', () => {{
            const features = document.querySelectorAll('.feature');
            features.forEach(feature => {{
                const rect = feature.getBoundingClientRect();
                if (rect.top < window.innerHeight) {{
                    feature.style.transform = 'translateY(0)';
                    feature.style.opacity = '1';
                }}
            }});
        }});
        
        // Initialize animations
        document.querySelectorAll('.feature').forEach(feature => {{
            feature.style.transform = 'translateY(20px)';
            feature.style.opacity = '0';
            feature.style.transition = 'all 0.6s ease';
        }});
    </script>
</body>
</html>"""
            
            result = {
                "type": "website",
                "title": f"Site: {description}",
                "description": description,
                "content": html_content,
                "url": None,
                "preview": "Site criado com sucesso"
            }
            
            print(f"🎯 [CODER] Website criado com sucesso: {result['title']}")
            return result
            
        except Exception as e:
            print(f"❌ [CODER] Erro ao criar website: {str(e)}")
            
            # Criar um site de fallback baseado na descrição
            error_msg = str(e)
            is_api_error = "500" in error_msg.lower() or "internal error" in error_msg.lower() or "retry" in error_msg.lower()
            
            if is_api_error:
                print("🔄 [CODER] Erro da API detectado, criando site de fallback inteligente...")
                
                # Site de fallback baseado no tema
                fallback_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Site: {description} (Fallback)</title>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
    </style>
</head>
<body>
    <h1>Site sobre: {description}</h1>
    <p>Este é um site de fallback gerado devido a um erro na API. Descrição: {description}</p>
    <p class="warning">Gerado em modo de fallback</p>
</body>
</html>"""
                        
                print(f"🎯 [CODER] Site de fallback criado (tamanho: {len(fallback_html)} chars)")
                
                return {
                    "type": "website",
                    "title": f"Site: {description} (Fallback)",
                    "description": f"Site de fallback para: {description}",
                    "content": fallback_html,
                    "url": None,
                    "preview": "Site criado em modo de fallback devido a instabilidade da API"
                }
            else:
                # Erro não relacionado à API
                simple_fallback = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Erro</title>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
        .error {{ color: #e74c3c; }}
    </style>
</head>
<body>
    <h1 class="error">Erro ao criar site</h1>
    <p>{str(e)}</p>
</body>
</html>"""
                print(f"🔄 [CODER] Usando HTML de fallback simples (tamanho: {len(simple_fallback)} chars)")
                
                return {
                    "type": "error",
                    "title": "Erro ao criar site",
                    "description": str(e),
                    "content": simple_fallback,
                    "url": None,
                    "preview": "Erro ao criar site"
                }

class SupervisorAgent:
    def __init__(self):
        self.research_agent = ResearchAgent(model_level="base")
        self.coder_agent = CoderAgent(model_level="medio")
    
    async def process_request(self, message: str) -> Dict[str, Any]:
        try:
            print(f"🎯 [SUPERVISOR] Processando solicitação: {message}")
            
            # Primeiro, determinar se precisa de ferramentas ou é conversa normal
            decision_prompt = f"""
            Analise esta mensagem do usuário: "{message}"
            
            Você é um assistente conversacional que pode usar ferramentas quando necessário.
            
            Determine se esta mensagem:
            1. É uma CONVERSA NORMAL (saudações, perguntas gerais, conversas casuais) - responda diretamente
            2. PRECISA DE PESQUISA (buscar informações específicas, dados atuais, fatos)
            3. PRECISA CRIAR WEBSITE (solicita criação de site, página web, código HTML)
            
            Responda APENAS com um JSON válido:
            {{
                "needs_tool": true/false,
                "tool_type": "research|website|none",
                "description": "descrição para a ferramenta ou resposta direta",
                "is_greeting": true/false
            }}
            """
            
            # Configurar API para o supervisor (usa o modelo médio)
            if not api_config.configure_api("medio"):
                if not api_config.configure_api("medio", use_backup=True):
                    return {
                        "response": "Desculpe, não consigo acessar a API no momento. Tente novamente mais tarde.",
                        "results": [],
                        "type": "error",
                        "status": "error"
                    }
            
            supervisor_model = genai.GenerativeModel(MODEL_MEDIO)
            
            print("🤖 [SUPERVISOR] Enviando prompt de decisão para o modelo com retry...")
            decision_response = await retry_with_backoff(supervisor_model.generate_content, decision_prompt)
            print(f"✅ [SUPERVISOR] Resposta de decisão recebida: {decision_response.text}")
            
            # Parse da decisão
            try:
                decision_text = decision_response.text.strip()
                import re
                json_match = re.search(r'\{.*\}', decision_text, re.DOTALL)
                if json_match:
                    decision_data = json.loads(json_match.group())
                    print(f"📋 [SUPERVISOR] Decisão parseada: {decision_data}")
                else:
                    decision_data = {"needs_tool": False, "tool_type": "none", "description": message, "is_greeting": False}
                    print("⚠️ [SUPERVISOR] Não foi possível extrair JSON, usando fallback")
            except Exception as parse_error:
                print(f"❌ [SUPERVISOR] Erro ao parsear decisão: {parse_error}")
                decision_data = {"needs_tool": False, "tool_type": "none", "description": message, "is_greeting": False}
            
            # Se não precisa de ferramenta, responder diretamente
            if not decision_data.get("needs_tool", False):
                print("💬 [SUPERVISOR] Processando como conversa normal")
                conversation_prompt = f"""
                Responda de forma natural e amigável à mensagem: "{message}"
                
                Você é um assistente inteligente que pode ajudar com:
                - Pesquisas na web (quando solicitado)
                - Criação de websites (quando solicitado)
                - Conversas gerais e dúvidas
                
                Seja conversacional, útil e mencione suas capacidades quando apropriado.
                Responda em português brasileiro.
                """
                
                conversation_response = await retry_with_backoff(supervisor_model.generate_content, conversation_prompt)
                
                result = {
                    "response": conversation_response.text,
                    "results": [],
                    "type": "conversation",
                    "status": "completed"
                }
                print(f"✅ [SUPERVISOR] Conversa processada: {result}")
                return result
            
            # Se precisa de ferramenta, usar o agente apropriado
            results = []
            tool_type = decision_data.get("tool_type", "research")
            description = decision_data.get("description", message)
            
            print(f"🔧 [SUPERVISOR] Usando ferramenta: {tool_type} com descrição: {description}")
            
            if tool_type == "research":
                print("🔍 [SUPERVISOR] Chamando agente de pesquisa...")
                result = await self.research_agent.research(description)
                results.append(result)
                final_result = {
                    "response": "🔍 Pesquisa realizada com sucesso!",
                    "results": results,
                    "type": "research",
                    "status": "completed"
                }
                print(f"✅ [SUPERVISOR] Pesquisa concluída: {final_result}")
                return final_result
            elif tool_type == "website":
                print("🌐 [SUPERVISOR] Chamando agente de criação de website...")
                result = await self.coder_agent.create_website(description)
                results.append(result)
                final_result = {
                    "response": "💻 Website criado com sucesso!",
                    "results": results,
                    "type": "website", 
                    "status": "completed"
                }
                print(f"✅ [SUPERVISOR] Website concluído: {final_result}")
                return final_result
            else:
                print("💬 [SUPERVISOR] Fallback para conversa")
                # Fallback para conversa
                conversation_prompt = f"Responda de forma natural à mensagem: '{message}'"
                conversation_response = await retry_with_backoff(supervisor_model.generate_content, conversation_prompt)
                
                result = {
                    "response": conversation_response.text,
                    "results": [],
                    "type": "conversation",
                    "status": "completed"
                }
                print(f"✅ [SUPERVISOR] Fallback processado: {result}")
                return result
            
        except Exception as e:
            print(f"❌ [SUPERVISOR] Erro no processamento: {str(e)}")
            return {
                "response": f"Desculpe, ocorreu um erro ao processar sua solicitação: {str(e)}",
                "results": [],
                "type": "error",
                "status": "error"
            }

# Instância global do supervisor
supervisor = SupervisorAgent()

# Rota principal
@app.get("/", response_class=HTMLResponse)
async def read_root():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Erro: Arquivo index.html não encontrado</h1>")

# WebSocket para comunicação em tempo real
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections[:]:
            try:
                await connection.send_text(message)
            except:
                self.disconnect(connection)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
        print("🔗 [WEBSOCKET] Nova conexão WebSocket")
        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                print(f"📨 [WEBSOCKET] Mensagem recebida: {data[:100]}...")
                
                try:
                    message_data = json.loads(data)
                    print(f"📋 [WEBSOCKET] Dados parseados: {message_data}")
                    
                    if message_data.get("type") == "message":
                        user_message = message_data.get("content", "")
                        print(f"💬 [WEBSOCKET] Processando mensagem do usuário: {user_message}")
                        
                        # Enviar mensagem de processamento
                        await manager.send_personal_message(
                            json.dumps({
                                "type": "processing",
                                "content": "Processando sua solicitação..."
                            }),
                            websocket
                        )
                        print("⚙️ [WEBSOCKET] Mensagem de processamento enviada")
                        
                        # Processar com o supervisor
                        print("🤖 [WEBSOCKET] Enviando para o supervisor...")
                        result = await supervisor.process_request(user_message)
                        print(f"✅ [WEBSOCKET] Resultado do supervisor: {result}")
                        
                        # Enviar resultados com base no tipo de resposta
                        response_data = {
                            "type": "response",
                            "content": result["response"],
                            "response_type": result["type"],
                            "timestamp": str(asyncio.get_event_loop().time())
                        }
                        
                        # Só incluir resultados se houver e não for conversa
                        if result["results"] and result["type"] != "conversation":
                            response_data["results"] = result["results"]
                            print(f"🎨 [WEBSOCKET] Incluindo {len(result['results'])} artefato(s) na resposta")
                        else:
                            print("💬 [WEBSOCKET] Resposta sem artefatos (conversa normal)")
                        
                        print(f"📤 [WEBSOCKET] Enviando resposta final: {response_data}")
                        await manager.send_personal_message(
                            json.dumps(response_data),
                            websocket
                        )
                        print("✅ [WEBSOCKET] Resposta enviada com sucesso")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ [WEBSOCKET] Erro ao parsear JSON: {e}")
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "error",
                            "content": "Erro ao processar mensagem"
                        }),
                        websocket
                    )
        except WebSocketDisconnect:
            print("🔌 [WEBSOCKET] Conexão WebSocket desconectada")
            manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8192"))
    uvicorn.run(app, host=host, port=port)