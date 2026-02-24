# Plataforma Inteligente de Análise e Otimização de Currículos

Aplicação desenvolvida em `Streamlit`, com persistência em `SQLite` e backend em `FastAPI`, focada em diagnóstico e otimização de currículos.

## 1) Problema
Candidatos costumam ter dificuldade para:
- saber se o currículo está claro e com impacto;
- identificar lacunas para vagas específicas;
- entender aderência a filtros ATS;
- transformar análise em melhorias práticas.

## 2) Solução proposta
A plataforma organiza o processo em módulos:
1. `Home`: visão geral, histórico e gestão de análises.
2. `Upload e Parsing`: envio do currículo e extração estruturada (mock).
3. `Análise por Seção`: métricas por seção + simulações de otimização com IA.
4. `Comparação com a Vaga`: fluxo estruturado de comparação currículo x vaga.
5. `Relatário Final`: painel analático com score, prioridades e recomendações.
6. `Histórico`: consulta das análises registradas.

## 3) Arquitetura
- Frontend: `Streamlit`
- Backend: `FastAPI` (API REST)
- Banco de dados: `SQLite` (`data/analises.db`)
- Lógica de negócio: módulo `core/`

### Estrutura de pastas
- `app.py`: ponto de entrada do Streamlit
- `pages/`: telas da aplicação
- `components/`: widgets e estilos
- `core/`: acesso a dados e regras de negócio
- `backend/main.py`: API FastAPI
- `backend/requirements.txt`: dependências do backend
- `data/analises.db`: banco SQLite

## 4) Como executar

### 4.1 Frontend (Streamlit)
```bash
python -m venv .venv
# PowerShell
.\.venv\Scripts\Activate.ps1
pip install streamlit
streamlit run app.py
```
Acesse: `http://localhost:8501`

### 4.2 Backend (FastAPI)
```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```
Acesse:
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 5) Endpoints principais da API
- `GET /health`
- `GET /analises`
- `GET /analises/{id}`
- `POST /analises`
- `DELETE /analises/{id}`
- `POST /comparacoes/run`
- `GET /comparacoes/analise/{analise_id}`
- `GET /comparacoes/{id}`
- `GET /relatorios/{analise_id}`