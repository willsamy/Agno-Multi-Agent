# Agno Multi-Agent System V2

Sistema inteligente de agentes com seleção automática de modelos baseada na complexidade da tarefa. Construído com FastAPI e Google Gemini AI, permitindo interação com agentes especializados que se adaptam dinamicamente às necessidades do usuário.

## Funcionalidades V2

- **Intermediador Inteligente**: Analisa complexidade e seleciona modelo apropriado
- **Modelos por Complexidade**: Base, Médio e Avançado adaptados à tarefa
- **Agente Pesquisador**: Pesquisas adaptativas com níveis de detalhe variáveis
- **Agente Coder**: Criação de websites com complexidade ajustável
- **Interface Web**: Chat moderno com pré-visualização de artefatos
- **WebSocket**: Comunicação em tempo real
- **Sistema de APIs**: Preparado para múltiplas APIs com failover

## Tecnologias Utilizadas

- **Backend**: FastAPI, Agno, Google Gemini AI
- **Frontend**: HTML5, CSS3, JavaScript puro
- **IA**: Google Gemini 2.5 Flash Lite (pesquisa), Gemini 2.5 Flash (gestor e coder)
- **WebSocket**: Comunicação bidirecional em tempo real

## Instalação

1. Clone o repositório
2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente:
```bash
# Copie o arquivo de exemplo
copy .env.exemplo .env

# Edite o arquivo .env e configure sua chave de API do Google Gemini
# GOOGLE_API_KEY=sua_chave_api_aqui
```

4. Execute o servidor:
```bash
python main.py
```

5. Acesse: http://localhost:8192

## Configuração

O sistema utiliza variáveis de ambiente para configuração. Copie o arquivo `.env.exemplo` para `.env` e configure:

### Variáveis Obrigatórias
- `GOOGLE_API_KEY`: Sua chave de API do Google Gemini

### Modelos por Complexidade (V2)
- `MODEL_BASE`: Modelo para tarefas simples (padrão: gemini-2.5-flash-lite)
- `MODEL_MEDIO`: Modelo para tarefas moderadas (padrão: gemini-2.5-flash)
- `MODEL_AVANCADO`: Modelo para tarefas complexas (padrão: gemini-2.5-pro)

### Configurações de Servidor
- `SERVER_HOST`: Host do servidor (padrão: 0.0.0.0)
- `SERVER_PORT`: Porta do servidor (padrão: 8192)
- `MAX_RETRIES`: Tentativas de retry (padrão: 3)
- `BASE_DELAY`: Delay base para retry (padrão: 1)
- `DEBUG_MODE`: Modo debug (padrão: false)
- `VERBOSE_LOGS`: Logs detalhados (padrão: false)

### APIs Múltiplas (Preparação)
- `API_BASE_1`: API primária para modelos base
- `API_BASE_2`: API secundária para modelos base
- `API_MEDIO_1`: API primária para modelos médios
- `API_MEDIO_2`: API secundária para modelos médios
- `API_AVANCADO_1`: API primária para modelos avançados
- `API_AVANCADO_2`: API secundária para modelos avançados

### Rate Limits
- `RATE_LIMIT_BASE`: Limite para modelos base (padrão: 60)
- `RATE_LIMIT_MEDIO`: Limite para modelos médios (padrão: 30)
- `RATE_LIMIT_AVANCADO`: Limite para modelos avançados (padrão: 10)

### Modelos Disponíveis
- `gemini-2.5-flash-lite`: Otimizado para tarefas simples
- `gemini-2.5-flash`: Equilíbrio entre velocidade e capacidade
- `gemini-2.5-pro`: Máxima capacidade para tarefas complexas
- `gemini-1.5-flash`: Modelo anterior (compatibilidade)
- `gemini-1.5-pro`: Modelo anterior avançado (compatibilidade)

## Estrutura do Projeto

```
├── main.py              # Servidor FastAPI com agentes
├── requirements.txt     # Dependências do projeto
├── static/              # Arquivos estáticos da interface
│   ├── index.html       # Interface principal
│   ├── styles.css       # Estilos da interface
│   └── script.js        # Lógica JavaScript
└── README.md           # Este arquivo
```

## Como Usar

1. **Pesquisas**: Digite qualquer pergunta ou tópico para pesquisa
2. **Desenvolvimento Web**: Peça para criar um site descrevendo o que você quer
3. **Visualização de Artefatos**: Clique no ícone de paleta para ver resultados
4. **Pré-visualização**: Clique em artefatos de websites para pré-visualizar

## Exemplos de Uso - Nova Arquitetura V2

### 1. Tarefas Simples (Modelo Base)
**Você:** "Explique o que é Python"
**Sistema:** Usa modelo base (gemini-2.5-flash-lite) para resposta rápida e direta

### 2. Tarefas Moderadas (Modelo Médio)
**Você:** "Crie um site sobre tecnologia"
**Sistema:** Usa modelo médio (gemini-2.5-flash) para site profissional com funcionalidades

### 3. Tarefas Complexas (Modelo Avançado)
**Você:** "Desenvolva uma arquitetura de microserviços escalável para e-commerce"
**Sistema:** Usa modelo avançado (gemini-2.5-pro) para análise técnica profunda

### 4. Criação de Site por Complexidade
- **Simples**: "Faça um site básico de portfólio" → HTML/CSS essencial
- **Médio**: "Crie um site moderno para empresa de tecnologia" → Design profissional + interações
- **Complexo**: "Desenvolva um site completo de marketplace com sistema de pagamento" → Arquitetura completa

## Comandos de Teclado

- `Ctrl + B`: Alternar painel de artefatos
- `Enter`: Enviar mensagem
- `Shift + Enter`: Nova linha

## API Endpoints

- `GET /`: Interface web principal
- `WebSocket /ws`: Comunicação em tempo real

## Segurança

- Validação de entrada de usuário
- Sanitização de HTML
- CORS configurado
- WebSocket com tratamento de desconexão

## Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT.