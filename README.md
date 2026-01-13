# StructGuard API

API de middleware para proteger estructuras XML/JSON durante la edición con LLMs.

## Inicio rápido

```bash
cd structguard
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Con Docker

```bash
cd structguard
docker build -t structguard-api .
docker run -p 8000:8000 structguard-api
```

## Endpoints

- `POST /v1/extract` - Extrae segmentos de texto de un XML
- `POST /v1/inject` - Inyecta modificaciones de vuelta al XML

## Tests

```bash
cd structguard
pytest tests/
```
