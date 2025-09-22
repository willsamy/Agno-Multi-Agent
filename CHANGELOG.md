# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [22/09/2025] - Inicialização do Projeto

### Inicializado
- Projeto Agno Multi-Agent System iniciado com sucesso
- Servidor FastAPI rodando em http://localhost:8192/
- Interface web funcional com sistema de chat
- Sistema de artefatos operacional
- Autenticação simples implementada

### Status
- ✅ Servidor iniciado e funcionando
- ✅ Interface web carregando sem erros
- ✅ Sistema de autenticação ativo
- ✅ WebSocket conectado e operacional

## [Não Lançado]

### Adicionado
- Sistema de autenticação simples com localStorage
- Modal de login para identificação do usuário
- Persistência de dados por usuário (conversas e artefatos)
- Sistema de fallback dinâmico para geração de websites

### Modificado
- Lógica de armazenamento no localStorage agora é específica por usuário
- Sistema de fallback de websites agora usa a descrição real em vez de temas fixos
- Correções de sintaxe e indentação no código de fallback

### Corrigido
- Erro de JavaScript "loadUserData is not defined"
- Problemas de sintaxe no arquivo main.py
- Temas de websites em cache ou anteriores

# Histórico de Mudanças

## [1.2.0] - 2024-12-19 - Sistema de Configuração com Variáveis de Ambiente

### 🔧 Implementações Realizadas

#### 1. Sistema de Configuração com .env
- **Arquivos**: `.env`, `.env.exemplo`, `.gitignore`
- **Melhorias**:
  - Chave de API do Google Gemini movida para variável de ambiente
  - Configuração de modelos Gemini via .env
  - Configurações de servidor (host/porta) via .env
  - Configurações de retry personalizáveis
  - Arquivo de exemplo para facilitar setup

#### 2. Segurança Aprimorada
- **Arquivo**: `.gitignore`
- **Melhorias**:
  - Arquivo .env protegido do controle de versão
  - Chave de API não mais exposta no código
  - Configurações sensíveis isoladas

#### 3. Flexibilidade de Modelos
- **Arquivo**: `main.py`
- **Melhorias**:
  - Troca fácil de modelos Gemini via .env
  - Suporte a todos os modelos disponíveis
  - Configurações específicas por agente

#### 4. Configurações Personalizáveis
- **Variáveis disponíveis**:
  - `GOOGLE_API_KEY`: Chave de API obrigatória
  - `RESEARCH_MODEL`, `CODER_MODEL`, `SUPERVISOR_MODEL`: Modelos por agente
  - `SERVER_HOST`, `SERVER_PORT`: Configurações do servidor
  - `MAX_RETRIES`, `BASE_DELAY`: Configurações de retry
  - `DEBUG_MODE`, `VERBOSE_LOGS`: Configurações de debug

### 📦 Dependências Adicionadas
- **python-dotenv==1.0.0**: Para carregar variáveis de ambiente

### 📚 Documentação Atualizada
- **README.md**: Instruções de configuração com .env
- **Modelos disponíveis**: Lista completa de modelos Gemini suportados
- **Variáveis de ambiente**: Documentação completa de todas as opções

### 🔍 Benefícios
1. **Segurança**: Chaves de API protegidas
2. **Flexibilidade**: Troca fácil de modelos e configurações
3. **Portabilidade**: Setup simplificado em diferentes ambientes
4. **Manutenibilidade**: Configurações centralizadas

---

## [1.1.0] - 2024-12-19 - Melhorias no Sistema de Tratamento de Erros

### 🔧 Implementações Realizadas

#### 1. Sistema de Retry Robusto
- **Arquivo**: `main.py`
- **Função**: `retry_with_backoff()`
- **Melhorias**:
  - Retry automático para erros 500 da API do Google Gemini
  - Backoff exponencial com jitter para evitar sobrecarga
  - Máximo de 3 tentativas configuráveis
  - Logs detalhados para cada tentativa
  - Detecção inteligente de erros da API vs outros erros

#### 2. Integração do Sistema de Retry
- **CoderAgent**: Integrado na geração de websites
- **ResearchAgent**: Integrado na pesquisa de conteúdo
- **SupervisorAgent**: Integrado em todas as chamadas do modelo

#### 3. Sistema de Fallback Inteligente para Websites
- **Localização**: `CoderAgent.create_website()`
- **Funcionalidades**:
  - Detecção automática de erros da API
  - Fallback específico para temas de Inteligência Artificial
  - Fallback genérico para outros temas
  - Sites de fallback com design profissional
  - Aviso claro sobre modo de fallback

#### 4. Melhorias no Tratamento de Erros
- **WebSocket**: Tratamento robusto de desconexões
- **ResearchAgent**: Fallback gracioso para erros de pesquisa
- **Logs Detalhados**: Sistema de logging melhorado em todos os componentes

### 🎯 Benefícios Implementados

1. **Maior Confiabilidade**: Sistema continua funcionando mesmo com instabilidade da API
2. **Experiência do Usuário**: Fallbacks inteligentes mantêm a funcionalidade
3. **Debugging Melhorado**: Logs detalhados facilitam identificação de problemas
4. **Performance**: Retry inteligente evita tentativas desnecessárias
5. **Robustez**: Sistema resiliente a falhas temporárias

### 🔍 Problemas Resolvidos

- **Erro 500 da API Gemini**: Sistema de retry automático implementado
- **Sites não sendo entregues**: Fallback inteligente garante entrega de conteúdo
- **Falta de feedback**: Logs detalhados para monitoramento
- **Instabilidade**: Sistema robusto contra falhas temporárias

### 📊 Configurações Implementadas

```python
# Configurações de Retry
max_retries = 3
base_delay = 1-2 segundos (dependendo do agente)
backoff_exponential = True
jitter = True (0-1 segundo aleatório)
```

## [1.0.0] - 2024-12-19

### Adicionado
- **Servidor FastAPI**: Criado servidor principal na porta 8191 com rotas REST e WebSocket
- **Agente Supervisor**: Implementado agente principal que coordena solicitações dos usuários
- **Agente Pesquisador**: Criado agente especializado em pesquisas web com Google Gemini 2.5 Flash Lite
- **Agente Coder**: Desenvolvido agente para criação de websites com JavaScript puro usando Gemini 2.5 Flash
- **Interface Web Moderna**: Criada interface inspirada no ChatGPT com design responsivo
- **Painel de Artefatos**: Implementado sistema de visualização de resultados em painel lateral
- **WebSocket**: Adicionado comunicação em tempo real entre cliente e servidor
- **Pré-visualização de Websites**: Funcionalidade para visualizar sites criados antes de baixar
- **Sistema de Chat Persistente**: Interface com histórico de conversas e scroll automático
- **Validação de Entrada**: Implementada sanitização e validação de entrada do usuário
- **Responsividade**: Interface adaptável para dispositivos móveis
- **Documentação**: Criados arquivos README.md e CHANGELOG.md

### Arquivos Criados
- `main.py`: Servidor FastAPI com lógica dos agentes
- `requirements.txt`: Lista de dependências do projeto
- `static/index.html`: Interface principal do chatbot
- `static/styles.css`: Estilos modernos da interface
- `static/script.js`: Lógica JavaScript para interação
- `README.md`: Documentação completa do projeto
- `CHANGELOG.md`: Este arquivo de histórico de mudanças

### Tecnologias Integradas
- **FastAPI**: Framework web assíncrono
- **Agno**: Framework para agentes de IA
- **Google Gemini AI**: Modelos de linguagem para processamento
- **WebSocket**: Comunicação bidirecional
- **HTML5/CSS3/JavaScript**: Interface web moderna
- **Font Awesome**: Ícones para interface

### Configurações
- Porta: 8191
- API Key: Google Gemini configurada
- Modelos: Gemini 2.5 Flash Lite (pesquisa), Gemini 2.5 Flash (gestor/coder)
- CORS: Configurado para aceitar conexões locais
- WebSocket: Reconexão automática em caso de falha

### Segurança
- Validação de entrada de usuário
- Sanitização de HTML
- Tratamento de erros de WebSocket
- Código executado em ambiente isolado

### Próximos Passos
- Adicionar autenticação de usuário
- Implementar histórico persistente
- Adicionar mais especialistas
- Implementar exportação de artefatos
- Adicionar testes automatizados

---

## [1.0.1] - 2024-12-19

### Adicionado
- Sistema de configuração de API por nível de modelo (base, médio, avançado)
- Suporte para chaves primárias e de backup para cada nível de modelo
- Classe `APIConfig` para gerenciar configurações de API de forma centralizada
- Variáveis de ambiente específicas para cada nível de modelo:
  - `API_BASE_1` e `API_BASE_2` para modelo base
  - `API_MEDIO_1` e `API_MEDIO_2` para modelo médio  
  - `API_AVANCADO_1` e `API_AVANCADO_2` para modelo avançado

### Modificado
- Classes `ResearchAgent`, `CoderAgent` e `SupervisorAgent` agora usam a nova classe `APIConfig` para configuração de API
- Removida configuração global única da API (`GOOGLE_API_KEY`)
- Atualizados os modelos para usar variáveis de ambiente por nível:
  - `MODEL_BASE=gemini-2.5-flash-lite`
  - `MODEL_MEDIO=gemini-2.5-flash`
  - `MODEL_AVANCADO=gemini-2.5-pro`

### Segurança
- Chaves de API agora são gerenciadas por nível de complexidade, permitindo melhor controle e isolamento
- Sistema de fallback automático para chaves de backup quando primárias falham