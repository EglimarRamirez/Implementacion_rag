# 🏛️ Asistente Inteligente de Orientación Tributaria Municipal  
### Basado en RAG + Cohere + ChromaDB

---

## 📌 Contexto y Problema

Durante el análisis de la experiencia real de contribuyentes municipales se identificaron problemas críticos:

- Pagos realizados que no aparecen imputados
- Personas que pagan dos veces el mismo impuesto sin saber cómo reclamar
- Desconocimiento de trámites, requisitos y documentación
- Información dispersa en documentos extensos y técnicos
- Dependencia del canal presencial → largas filas, demoras y frustración

🎯 **Los ciudadanos no necesitan normativa compleja. Necesitan respuestas claras, confiables y accionables.**

---

## 🎯 Objetivo del Proyecto

Construir un **Asistente Inteligente Tributario Municipal** capaz de:

✔️ Entender consultas en lenguaje natural  
✔️ Buscar información en normativa oficial y guías reales  
✔️ Responder únicamente si existe información documentada  
✔️ Evitar inventar contenido  
✔️ Orientar operativamente qué hacer y cómo hacerlo  

---

## 🧠 Arquitectura General

Documentos PDF municipales
↓
Limpieza + Chunking Inteligente
↓
Embeddings Cohere
↓
ChromaDB Persistente
↓
Consulta del Usuario
↓
Recuperación + Grounding
↓
Respuesta Segura y Contextual


---

## ⚙️ Pipeline Técnico RAG

### 1️⃣ Ingesta de Documentos
- Carga mediante endpoint `/upload-file`
- Extracción de texto
- Almacenamiento temporal + persistencia en ChromaDB

---

### 2️⃣ Chunking Inteligente
Se aplicaron estrategias dependientes del tipo de documento:

| Tipo documento | Estrategia |
|----------------|----------|
| Normativa | Chunks grandes (mantener coherencia legal) |
| Protocolos y notas | Chunks pequeños y precisos |

---

### 3️⃣ Metadatos Aplicados

Cada chunk almacena:

- `document_id`
- `title`
- `tipo_documento`
- `tramite`
- `chunk_index`

Permite:

✔️ Filtrar relevancia  
✔️ Asegurar consistencia  
✔️ Aplicar reglas de dominio  
✔️ Mejorar grounding

---

### 4️⃣ Embeddings Cohere
Modelo utilizado: embed-multilingual-v3.0


Incluye:

- Batch embeddings
- Manejo de límite de requests
- Compatibilidad multilenguaje

---

### 5️⃣ Base Vectorial Persistente
Se usa:

Chroma Persistent Client


Beneficios:

✔️ Persistencia local  
✔️ No se pierde información  
✔️ Alta velocidad de consulta  

---

### 6️⃣ Recuperación + Grounding Inteligente

Se recuperan `Top-K` chunks y se valida:

✔️ Mejor score  
✔️ Promedio de similitud  
✔️ Consistencia temática  
✔️ Validación por metadatos  

Si NO hay evidencia suficiente:

> "No cuento con información suficiente para responder con certeza este caso."

Nunca inventa normativa.

---

## 🧾 Base de Conocimiento

1️⃣ Código Tributario Municipal  
2️⃣ Guía de Trámites, Reclamos y Consultas  
3️⃣ Protocolo Nota Formal (Artículo 25)  
4️⃣ Autoridad Operativa / Representación  
5️⃣ Requisitos Plan de Pago y Regularización  

---

## 🤖 Prompt Engineering

El asistente:

- Responde en español claro
- No refiere normativa externa no disponible
- Diferencia:
  - Reclamos
  - Consultas
  - Planes de pago
- Solo usa información existente en documentos

---

## 🧪 Casos de Uso Cubiertos

✔️ Falta de imputación de pago  
✔️ Pago duplicado  
✔️ Emisión y consulta de cedulones  
✔️ Solicitud de plan de pago  
✔️ Presentación de nota formal  
✔️ Consultas generales  

---

## 🚫 Seguridad Semántica

- No responde sin grounding
- No inventa normativa
- No extrapola información
- Informa cuando falta evidencia

---

## 🔍 Logging Profesional

Implementado para:

- Auditoría
- Debugging
- Monitoreo del pipeline RAG

---

## 🚧 Limitaciones

- Base de conocimiento limitada a documentos cargados
- No accede a sistemas reales municipales
- No valida identidad del usuario

---

## ➕ Futuras Mejoras

- Frontend ciudadano productivo
- Incorporar resoluciones adicionales
- Analítica de consultas
- Integración con sistemas municipales reales
- Flujo conversacional guiado
- Seguimiento de ticket y estado de trámite

---

# 🛠️ Instalación y Ejecución

## ✅ Requisitos

- Python 3.10+
- Cohere API Key
- fastapi
- Chromadb
- langchain

---

## 📥 Clonar Repositorio

```bash
git clone <repo>
cd Asistente_Tributario_Municipal_RAG
```


---

## 🧩 Crear entorno e instalar dependencias

```bash
python -m venv venv
# Linux / macOS
source venv/bin/activate
# Windows (PowerShell)
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```


---

## 🔑 Configurar COHERE API
Crear archivo `.env` o variable de entorno:

```bash
# Ejemplo .env o variable de entorno
COHERE_API_KEY="tu_api_key_aqui"
```


---

## 🚀 Ejecutar Backend

```bash
uvicorn main:app --reload
```


Swagger disponible en:

http://localhost:8000/docs


---

## 💬 Ejecutar Frontend (Streamlit)
```bash
streamlit run app_streamlit.py
```


---

## 📡 Persistencia ChromaDB
Si no existe carpeta `chroma_db`, se generará automáticamente cuando se creen embeddings.

Si desea crearla manualmente:

```bash
# Linux / macOS
mkdir -p chroma_db
# Windows (PowerShell / CMD)
mkdir chroma_db
```

Se generará automáticamente cuando se creen embeddings.

---

## 🎯 Demo Sugerida
1️⃣ Caso simple: pago duplicado  
2️⃣ Caso intermedio: falta imputación  
3️⃣ Caso sobre titularidad  
4️⃣ Caso fuera de alcance  

(archivo `casos_de_prueba.txt` incluido)

---

## 🏁 Estado del Proyecto
✔️ Operativo  
✔️ Probado  
✔️ Enfocado en ciudadanía  
✔️ Listo para demo y evaluación  

---

## 👩‍💻 Autor
**Eglimar Ramirez**  
Proyecto desarrollado para Get Talent Challenge - IA Aplicada a la Administración Pública.
