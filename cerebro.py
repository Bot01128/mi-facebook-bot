import os
from langchain_google_genai import ChatGoogleGenerativeAI
# ¡LA IMPORTACIÓN CORRECTA PARA LA LIBRERÍA QUE SÍ FUNCIONA!
from langchain_postgres.chat_message_histories import PostgresChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

print(">>> [cerebro.py] Cargando Módulo... VERSIÓN FINAL ESTABLE")

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
    # ¡LA SINTAXIS CORRECTA PARA langchain-postgres!
    return PostgresChatMessageHistory(
        connection_string=db_url,
        session_id=session_id,
        table_name="message_store"
    )

# --- EL MANUAL DE VENTAS MAESTRO (PROMPT) ---
# Asegúrate de pegar tu prompt completo aquí
PROMPT = ChatPromptTemplate.from_messages([
    ("system", """
**REGLA NÚMERO UNO, LA MÁS IMPORTANTE E INQUEBRANTABLE: Detecta el idioma del cliente en su último mensaje y RESPONDE ÚNICA Y EXCLUSIVAMENTE en ese mismo idioma.**

Tu personalidad es la de un Agente de Ventas IA de 'AutoNeura AI'. Eres un súper vendedor: piensas, analizas, haces cálculos, resuelves cualquier problema y, sobre todo, CIERRAS VENTAS. Tu propósito es asegurarte de que el negocio de tu cliente nunca más pierda una venta por no poder responder al instante. Superas a los humanos en todo, especialmente en ventas.

# ... (AQUÍ VA EL RESTO DE TU PROMPT COMPLETO) ...
"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
])

# --- FUNCIÓN PRINCIPAL DE CREACIÓN DEL CHATBOT ---
def create_chatbot():
    """
    Crea la cadena de conversación una sola vez.
    """
    if not llm:
        print("!!! ERROR [cerebro.py]: El LLM no está inicializado.")
        return None
        
    try:
        chain = PROMPT | llm
        
        chatbot_with_history = RunnableWithMessageHistory(
            chain,
            get_chat_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )
        print(">>> [cerebro.py] Cerebro FINAL ESTABLE creado.")
        return chatbot_with_history
    except Exception as e:
        print(f"!!! ERROR [cerebro.py] al crear la cadena: {e} !!!")
        return None

print(">>> [cerebro.py] Módulo cargado.")
