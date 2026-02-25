# Plataforma de Analise e Otimizacao de Curriculos

Projeto da avaliacao intermediaria de IA Generativa: interface completa e estrutura funcional sem integrar LLM real (somente mocks).

## 1) Problema e Solucao
Problema:
- Candidatos nao sabem se o curriculo esta bem estruturado, aderente a vaga e apto para filtros ATS.

Solucao proposta:
- Plataforma com fluxo completo de analise de curriculo:
1. Dashboard/Home
2. Upload e parsing (mock)
3. Analise por secao
4. Comparacao com a vaga
5. Relatorio final
6. Historico de analises

Como IA entrara no futuro:
- Reescrita de secoes com maior impacto.
- Ajuste semantico por vaga especifica.
- Sugestao automatica de palavras-chave ATS.
- Avaliacao de clareza e objetividade por secao.

## 2) Arquitetura e escolhas de design
Stack usada:
- Frontend: Streamlit
- Backend: FastAPI + Uvicorn
- Banco local: SQLite (`data/analises.db`)

Por que essa arquitetura:
- Rapida para prototipar UI multipagina.
- Facil de integrar API de LLM depois.
- SQLite simplifica desenvolvimento local sem infra extra.

Alternativas consideradas:
- React + Vite (mais controle de UI, mais setup).
- Gradio (rapido, mas menos flexivel para fluxo multipagina complexo).

Decisao:
- Streamlit + FastAPI para entregar funcionalidade completa no prazo com boa evolucao futura.

## 3) Estrutura do projeto
- `app.py`: entrada do frontend Streamlit
- `pages/`: telas da aplicacao
- `components/`: estilos e widgets
- `core/`: regras de negocio e persistencia
- `backend/main.py`: API FastAPI
- `backend/requirements.txt`: dependencias do backend
- `prompts/prompts.txt`: historico de prompts usados
- `data/analises.db`: banco SQLite

## 4) Como executar
### 4.1 Frontend (Streamlit)
```bash
python -m venv .venv
# PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```
Acesso local: `http://localhost:8501`

### 4.2 Backend (FastAPI)
```bash
python -m venv .venv
# PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```
Acesso local:
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 5) Endpoint publico
Link do endpoint publico:
- `https://resume-ai-app-kc858pmaceu5fquaoomsdb.streamlit.app/`

Checklist minimo para validacao em 1 minuto:
- App abre sem erro.
- Sidebar navega entre todas as telas.
- Upload e formularios respondem.
- Comparacao e relatorio exibem dados mock.

## 6) Endpoints da API
- `GET /health`
- `GET /analises`
- `GET /analises/{id}`
- `POST /analises`
- `DELETE /analises/{id}`
- `POST /comparacoes/run`
- `GET /comparacoes/analise/{analise_id}`
- `GET /comparacoes/{id}`
- `GET /relatorios/{analise_id}`

## 7) O que funcionou com o agente de codificacao
- Estrutura inicial do app multipagina em Streamlit.
- Componentizacao em `pages/`, `components/`, `core/`.
- Fluxo de UI com mocks coerentes para analise de curriculo.
- Integracao de API FastAPI com SQLite.
- Ajustes de UX (ex.: manter apenas uma navegacao na sidebar).

Exemplos de prompts que funcionaram:
- "faca isso no streamlit" com escopo detalhado das 5 telas.

## 8) O que nao funcionou bem e o que precisou de intervencao
- Prompt inicial muito amplo gerou necessidade de refinamento de escopo.
- README ficou inconsistente em um momento (referencia a arquivo inexistente de requirements).
- Foi necessario ajuste manual de configuracao para remover navegacao duplicada do Streamlit.
- Foi necessario organizar documentacao para atender exatamente a rubrica (endpoint publico, processo, prompts e critica tecnica).

O que seria feito diferente:
- Definir criterio de pronto por tela antes de codar.
- Separar requisitos obrigatorios da rubrica em checklist desde o dia 1.
- Registrar prompts e resultados em paralelo ao desenvolvimento.

## 9) Evidencia de uso do agente
- Historico de prompts e resultados em `prompts/prompts.txt`.
- Iteracoes registradas no historico de commits.
- Ajustes guiados por prompts para UI, documentacao e organizacao do projeto.