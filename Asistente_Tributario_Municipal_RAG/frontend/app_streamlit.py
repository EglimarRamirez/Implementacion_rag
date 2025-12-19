import streamlit as st
import requests

FASTAPI_URL = "http://127.0.0.1:8000/query"

st.set_page_config(
    page_title="Asistente Tributario Municipal",
    page_icon="💬",
    layout="centered"
)

st.title("🤖 Asistente de Orientación Tributaria Municipal")
st.write("Haz una pregunta sobre trámites, reclamos o pagos municipales y el asistente responderá basado solo en documentos oficiales cargados.")

# --- Input ---
question = st.text_input("✍️ Escribe tu consulta")

if st.button("Consultar"):
    if not question.strip():
        st.warning("Por favor escribe una pregunta antes de continuar.")
    else:
        with st.spinner("Procesando tu consulta..."):
            try:
                payload = {"question": question}
                response = requests.post(FASTAPI_URL, json=payload)

                if response.status_code == 200:
                    data = response.json()

                    st.success("Respuesta generada correctamente")

                    st.subheader("🧠 Respuesta")
                    st.write(data["answer"])

                    st.divider()

                    col1, col2 = st.columns(2)
                    col1.metric("Grounded", "Sí" if data["grounded"] else "No")
                    col2.metric("Similitud", f"{data['similarity_score']:.2f}")

                    with st.expander("📚 Ver contexto utilizado"):
                        st.write(data["context_used"])

                else:
                    st.error("Error en el servicio. Ver consola FastAPI.")
                    st.json(response.json())

            except Exception as e:
                st.error("No se pudo conectar con la API.")
                st.write(str(e))
