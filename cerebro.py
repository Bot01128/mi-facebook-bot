import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_message_histories import PostgresChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

print(">>> [Cerebro Unificado] Cargando Módulo...")

llm = None
try:
    # Usamos la conexión robusta que ya habíamos investigado
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0.7, api_version="v1")
    print(">>> [Cerebro Unificado] Conexión con Google AI (v1) exitosa.")
except Exception as e:
    print(f"!!! ERROR [Cerebro Unificado]: No se pudo conectar a Google AI: {e} !!!")
    llm = None

# Esta función es la que conecta con Supabase para la memoria
def get_chat_history(session_id: str):
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("!!! ERROR CRÍTICO [Cerebro Unificado]: DATABASE_URL no está configurada. La memoria no funcionará.")
        from langchain_core.chat_history import InMemoryChatMessageHistory
        return InMemoryChatMessageHistory() # Devuelve una memoria temporal para evitar un crash total
        
    return PostgresChatMessageHistory(
        session_id=session_id,
        connection_string=db_url,
        table_name="message_store" # La tabla que creamos en Supabase
    )

# Este es el prompt del Dashboard que ya teníamos.
# Más adelante lo haremos dinámico para que cargue la información del cliente.
PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Eres 'Auto', un asistente de IA amigable y ultra-eficiente, la cara visible de AutoNeura. Tu propósito es responder a las preguntas de los clientes sobre los planes, características y funcionamiento del sistema de ventas automatizado. Tu tono debe ser claro, servicial y generar confianza."),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
])

def create_chatbot():
    """
    Crea la cadena de LangChain completa, con la memoria conectada a la base de datos.
    """
    if not llm:
        return None
    try:
        # La cadena que une el prompt con el modelo de IA
        chain = PROMPT | llm
        
        # Le añadimos la capa de memoria, usando nuestra función get_chat_history
        chatbot_with_history = RunnableWithMessageHistory(
            chain,
            get_chat_history,
            input_messages_key="input",
            history_messages_key="chat_history",
        )
        print(">>> [Cerebro Unificado] Cerebro con memoria creado exitosamente.")
        return chatbot_with_history
    except Exception as e:
        print(f"!!! ERROR [Cerebro Unificado] al crear la cadena de LangChain: {e} !!!")
        return None

print(">>> [Cerebro Unificado] Módulo cargado.")
