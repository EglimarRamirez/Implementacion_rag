# Implementacion_rag
proyecto de asistente tributario municipal basado en rag

🏛️ Asistente Inteligente para Orientación Tributaria Municipal
Basado en RAG + Cohere + ChromaDB
💡 Contexto y Problema

Durante la experiencia con usuarios reales del municipio se identificaron dolores críticos:

Contribuyentes realizan pagos y no aparecen imputados.

Personas pagan dos veces sin saber cómo reclamar.

Ciudadanos no entienden los trámites ni la normativa.

Información está dispersa en documentos largos y técnicos.

Canal presencial saturado → largas filas, frustración, demoras.

Los vecinos no necesitan teoría.
Necesitan respuestas claras, confiables y accionables.

🎯 Objetivo del Proyecto

Construir un Asistente Inteligente de Orientación Tributaria Municipal capaz de:

✔️ Entender consultas naturales de ciudadanos
✔️ Buscar en normativa oficial y guías reales
✔️ Responder solo si la información existe
✔️ Evitar inventar respuestas
✔️ Guiar operativamente qué hacer y cómo hacerlo

🧠 Arquitectura General
PDFs oficiales → Limpieza → Chunking Inteligente
→ Embeddings Cohere → Base Vectorial Chroma Persistente
→ Query del Usuario
→ Recuperación con Grounding
→ Respuesta Segura y Contextual

⚙️ Pipeline Técnico RAG
1️⃣ Ingesta de Documentos

Carga vía endpoint /upload-file

Extracción de texto

Almacenamiento en memoria + persistencia Chroma

2️⃣ Chunking Inteligente

Se aplican estrategias distintas según el tipo de documento:

Tipo de Documento	Estrategia
Normativa (Código Tributario)	Chunks grandes para mantener coherencia legal
Guías / Trámites	Chunks medianos, orientados a pasos
Protocolos / Notas	Chunks pequeños y precisos
3️⃣ Metadatos aplicados

Cada chunk se almacena con:

document_id

title

tipo_documento

tramite

chunk_index

📌 Esto permite:
✔️ Filtrar relevancia
✔️ Garantizar consistencia de contexto
✔️ Aplicar reglas de dominio
✔️ Mejorar grounding

4️⃣ Embeddings Cohere

Modelo usado:
embed-multilingual-v3.0

Se implementó:

Batch embedding
Para evitar límite de 96 embeddings por request.

5️⃣ Base Vectorial Persistente

Se usa:

Chroma Persistent Client


Beneficios:

✔️ No se pierde info al reiniciar API
✔️ Base local segura
✔️ Consulta rápida

6️⃣ Recuperación y Grounding Inteligente

Se obtienen top-k resultados y se valida:

✔️ best similarity score
✔️ promedio de similitud
✔️ consistencia por tipo de documento
✔️ consistencia por trámite

Si NO hay evidencia suficiente:

🔒 El sistema NO responde inventando.
Responde seguro:

“No cuento con información suficiente para responder con certeza este caso.”

🧾 Base de Conocimiento

1️⃣ Código Tributario Municipal – 144 páginas
2️⃣ Guía de trámites, reclamos y consultas
3️⃣ Protocolo Art. 25 – Nota Formal
4️⃣ Autoridad Operativa / Representación
5️⃣ Requisitos Plan de Pago y Regularización

🤖 Prompt Engineering

El modelo:

habla en español

respuesta clara, administrativa

NO agrega leyes fuera del contexto

diferencia entre:

reclamos

plan de pago

consultas

respeta contenido exacto del PDF

🧪 Casos de Uso Cubiertos

✔️ Falta de imputación de pago
✔️ Pago duplicado
✔️ Emisión de Cedulones
✔️ Solicitud de Plan de Pago
✔️ Protocolo Art. 25
✔️ Consultas generales

🚫 Seguridad Semántica

No responde sin grounding

No inventa normativa

No extrapola contexto

Detecta cuando falta información

🔍 Logging Profesional

Implementado para:

Debugging

Auditoría

Monitoreo de RAG Pipeline

🚧 Limitaciones

Base limitada a documentos cargados

No consulta bases reales municipales

No valida identidad real del usuario

➕ Futuras Mejoras

Frontend ciudadano

Más fuentes (boletines, resoluciones, FAQs)

Analítica de consultas ciudadanas

Integración con sistemas municipales reales

Seguimiento de tickets
