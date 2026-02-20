# Backend API

API FastAPI integrada ao mesmo SQLite usado pelo Streamlit.

## Rodar local

```bash
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

## Endpoints principais

- `GET /health`
- `GET /analises`
- `GET /analises/{id}`
- `POST /analises`
- `DELETE /analises/{id}`
- `POST /comparacoes/run`
- `GET /comparacoes/analise/{analise_id}`
- `GET /comparacoes/{id}`
- `GET /relatorios/{analise_id}`

## Docs

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
