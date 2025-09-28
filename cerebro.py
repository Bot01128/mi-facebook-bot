import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_postgres.chat_message_histories import PostgresChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

print(">>> [cerebro.py] Cargando Módulo...")

# --- INICIALIZACIÓN DEL MODELO DE LENGUAJE ---
try:
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)
    print(">>> [cerebro.py] Conexión con Google AI exitosa.")
except Exception as e:
    print(f"!!! ERROR [cerebro.py]: No se pudo conectar a Google AI: {e} !!!")
    llm = None

# --- CONEXIÓN A LA MEMORIA (BASE DE DATOS) ---
def get_chat_history(session_id: str):
    db_url = os.environ.get("DATABASE_URL")
    # --- ¡ESTA ES LA LÍNEA CORREGIDA! ---
    # La nueva versión de la librería espera los argumentos sin los nombres ("keyword arguments")
    # y en un orden específico.
    return PostgresChatMessageHistory(
        session_id,
        db_url,
        "message_store"
    )

# --- EL MANUAL DE VENTAS MAESTRO (PROMPT) ---
# Recuerda reemplazar el texto de ejemplo con tu prompt completo.
PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
**REGLA NÚMERO UNO, LA MÁS IMPORTANTE E INQUEBRANTABLE: Detecta el idioma del cliente en su último mensaje y RESPONDE ÚNICA Y EXCLUSIVAMENTE en ese mismo idioma.**

Tu personalidad es la de un Agente de Ventas IA de 'AutoNeura AI'. Eres un súper vendedor: piensas, analizas, haces cálculos, resuelves cualquier problema y, sobre todo, CIERRAS VENTAS. Tu propósito es asegurarte de que el negocio de tu cliente nunca más pierda una venta por no poder responder al instante. Superas a los humanos en todo, especialmente en ventas.

### CONOCIMIENTO BASE Y PRECIOS DE AUTONEURA AI ###

**Paquetes:**
1.  **Paquete Básico ("Asistente de Respuesta 24/7"): $49/mes.**
2.  **Paquete Intermedio ("Agente de Ventas y Soporte IA"): $99/mes.**
3.  **Paquete Premium ("Director de Comunicaciones IA Multicanal"): $199/mes.**

# ... (Aquí va el resto de tu increíble prompt de ventas) ...

"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
])

# --- FUNCIÓN PRINCIPAL DE CREACIÓN DEL CHATBOT ---
def create_chatbot():
    """
    Crea la cadena de conversación una sola vez.
    La gestión de la memoria por session_id se hará al invocarla.
    """
    if not llm:
        print("!!! ERROR [cerebro.py]: El LLM no está inicializado. No se puede crear el cerebro.")
        return None
        
    try:
        chain = PROMPT | llm
        
        chatbot_with_history = RunnableWithMessageHistory(
            chain,
            get_chat_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )
        print(">>> [cerebro.py] Cerebro Inmortal (v12 - Corregido) creado exitosamente.")
        return 
