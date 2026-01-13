# StructGuard-API

**StructGuard-API** es un middleware stateless en FastAPI diseñado como "cortafuegos estructural" para LLMs. Su objetivo es permitir que una IA edite textos masivos sin romper jamás la estructura (tags XML/JSON).

## 🎯 Objetivo

Proporciona un flujo ETL (Extract-Transform-Load) que permite a los LLMs editar contenido textual de manera segura sin comprometer la estructura de documentos XML o JSON.

## 🚀 Flujo ETL

### 1. **POST /extract** - Extracción
Convierte XML/JSON en un mapa plano (JSON) seguro para editar.

**Input:**
```json
{
  "content": "<root><title>Original</title></root>",
  "format": "xml"
}
```

**Output:**
```json
{
  "flat_map": {
    "node_0": "Original"
  },
  "metadata": {
    "original_content": "...",
    "node_info": [...]
  }
}
```

### 2. **POST /inject** - Inyección
Reconstruye el archivo final fusionando el XML/JSON original (esqueleto) con los textos editados.

**Input:**
```json
{
  "flat_map": {
    "node_0": "Edited"
  },
  "metadata": { ... },
  "format": "xml"
}
```

**Output:**
```json
{
  "content": "<root><title>Edited</title></root>"
}
```

## 📦 Instalación

```bash
# Clonar el repositorio
git clone https://github.com/PejarRu/StructGuard-ETL.git
cd StructGuard-ETL

# Instalar dependencias
pip install -r requirements.txt

# Para desarrollo y tests
pip install -r requirements-test.txt
```

## 🏃 Ejecución

```bash
# Iniciar el servidor
python main.py

# O usando uvicorn directamente
uvicorn main:app --reload
```

El servidor estará disponible en `http://localhost:8000`

## 📚 Documentación API

Una vez iniciado el servidor, accede a:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Tests

```bash
# Ejecutar todos los tests
pytest test_main.py -v

# Ejecutar tests específicos
pytest test_main.py::TestXMLExtractInject -v
```

## 💡 Ejemplos de Uso

### Ejemplo XML

```python
import requests

# 1. Extract
response = requests.post("http://localhost:8000/extract", json={
    "content": """
    <article>
        <title>Mi Artículo</title>
        <content>Contenido original</content>
    </article>
    """,
    "format": "xml"
})

data = response.json()
flat_map = data["flat_map"]
metadata = data["metadata"]

# 2. Editar el mapa plano (simulando edición por LLM)
for key, value in flat_map.items():
    flat_map[key] = value.upper()  # Ejemplo: convertir a mayúsculas

# 3. Inject
response = requests.post("http://localhost:8000/inject", json={
    "flat_map": flat_map,
    "metadata": metadata,
    "format": "xml"
})

print(response.json()["content"])
# Output: XML con estructura original pero textos en mayúsculas
```

### Ejemplo JSON

```python
import requests

# 1. Extract
response = requests.post("http://localhost:8000/extract", json={
    "content": '{"title": "Original", "items": ["Item 1", "Item 2"]}',
    "format": "json"
})

data = response.json()
flat_map = data["flat_map"]

# 2. Editar
for key in flat_map:
    flat_map[key] = f"Editado: {flat_map[key]}"

# 3. Inject
response = requests.post("http://localhost:8000/inject", json={
    "flat_map": flat_map,
    "metadata": data["metadata"],
    "format": "json"
})

print(response.json()["content"])
```

## 🔒 Características de Seguridad Estructural

- **Preservación de estructura**: Los tags, atributos y jerarquía se mantienen intactos
- **Validación de formato**: Rechaza XML/JSON malformado
- **Separación de contenido**: Solo extrae texto editable, preservando metadatos
- **Reconstrucción segura**: Fusiona cambios sin alterar la estructura original

## 🛠️ Tecnologías

- **FastAPI**: Framework web moderno y rápido
- **Pydantic**: Validación de datos
- **Python 3.10+**: Tipos modernos y mejor rendimiento
- **XML ElementTree**: Procesamiento XML nativo
- **JSON**: Procesamiento JSON nativo

## 📋 Casos de Uso

1. **Traducción de documentos**: Traduce contenido sin romper tags
2. **Edición por LLM**: Permite a IAs editar contenido estructurado
3. **Normalización de texto**: Aplica transformaciones manteniendo estructura
4. **Migración de contenido**: Extrae y transforma contenido entre formatos

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es de código abierto.

## 👤 Autor

PejarRu

## 🙏 Agradecimientos

Diseñado para facilitar la integración de LLMs con contenido estructurado, manteniendo la integridad de los documentos.
