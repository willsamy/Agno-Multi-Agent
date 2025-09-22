# 🚀 Guia de Deploy na Vercel - Agno Multi-Agent System

## 📋 Pré-requisitos Completados

✅ **Estrutura do Projeto Organizada**
- Arquivo `vercel.json` configurado para FastAPI
- `package.json` com scripts e dependências
- `.gitignore` atualizado para deploy
- Variáveis de ambiente configuradas

✅ **Repositório Git Inicializado**
- Repositório Git criado
- Todos os arquivos adicionados ao staging
- Commit inicial realizado

## 🔧 Próximos Passos para Deploy

### 1. Configurar Repositório Remoto no GitHub

```bash
# Criar repositório no GitHub primeiro, depois:
git remote add origin https://github.com/seu-usuario/agno-multi-agent-system.git
git branch -M main
git push -u origin main
```

### 2. Configurar Variáveis de Ambiente na Vercel

No painel da Vercel, configure estas variáveis obrigatórias:

```
GOOGLE_API_KEY=sua_chave_api_google_gemini
RESEARCH_MODEL=gemini-2.5-flash-lite
CODER_MODEL=gemini-2.5-flash
SUPERVISOR_MODEL=gemini-2.5-flash
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
MAX_RETRIES=3
BASE_DELAY=1
CODER_MAX_RETRIES=3
CODER_BASE_DELAY=2
DEBUG_MODE=false
VERBOSE_LOGS=false
```

**Variáveis Opcionais (para múltiplas chaves de API):**
```
API_BASE_1=sua_chave_base_1
API_BASE_2=sua_chave_base_2
API_MEDIO_1=sua_chave_medio_1
API_MEDIO_2=sua_chave_medio_2
API_AVANCADO_1=sua_chave_avancado_1
API_AVANCADO_2=sua_chave_avancado_2
MODEL_BASE=gemini-2.5-flash-lite
MODEL_MEDIO=gemini-2.5-flash
MODEL_AVANCADO=gemini-2.5-pro
```

### 3. Deploy na Vercel

1. **Via Dashboard Vercel:**
   - Acesse [vercel.com](https://vercel.com)
   - Clique em "New Project"
   - Conecte seu repositório GitHub
   - Configure as variáveis de ambiente
   - Deploy automático será iniciado

2. **Via CLI Vercel:**
   ```bash
   npm i -g vercel
   vercel login
   vercel --prod
   ```

### 4. Configurações Importantes

**Arquivo `vercel.json` já configurado com:**
- Build usando `@vercel/python`
- Rotas para arquivos estáticos (`/static/`)
- Rota para WebSocket (`/ws`)
- Timeout de 30 segundos para funções
- Variável `PYTHONPATH` configurada

**Arquivo `package.json` já configurado com:**
- Scripts de build e start
- Metadados do projeto
- Compatibilidade com Python 3.8+

## ⚠️ Limitações da Vercel para FastAPI

1. **WebSockets:** Limitados na Vercel (funciona melhor em desenvolvimento)
2. **Timeout:** Máximo 30 segundos por função
3. **Cold Start:** Primeira requisição pode ser mais lenta

## 🔍 Verificação Pós-Deploy

Após o deploy, teste:
- ✅ Página inicial carrega
- ✅ Interface de chat funciona
- ✅ Sistema de login opera
- ✅ Agentes respondem (pode haver delay no cold start)

## 📝 Comandos Úteis

```bash
# Verificar status do Git
git status

# Ver logs da Vercel
vercel logs

# Redeployar
git add .
git commit -m "Update: descrição da mudança"
git push origin main
```

## 🆘 Troubleshooting

**Erro de Build:**
- Verifique se todas as dependências estão no `requirements.txt`
- Confirme se as variáveis de ambiente estão configuradas

**Erro de Runtime:**
- Verifique logs na Vercel Dashboard
- Confirme se a chave da API Google está válida
- Verifique se os modelos Gemini estão disponíveis

**WebSocket não funciona:**
- Normal na Vercel, use polling como fallback
- Para WebSocket completo, considere Railway ou Render

## 🎯 Status Atual

✅ **Projeto 100% preparado para deploy**
✅ **Git configurado e commitado**
✅ **Arquivos de configuração criados**
✅ **Documentação completa**

**Próximo passo:** Criar repositório no GitHub e fazer push!