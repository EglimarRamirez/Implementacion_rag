import logging

def configure_logging():
    """
    Configuración global de logging para toda la aplicación.
    - Establece formato estándar
    - Define nivel mínimo INFO
    - Reduce ruido de librerías externas
    """

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )

    # Reducir nivel de logging de librerías externas
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
