import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain_postgres.chat_message_histories import PostgresChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)

def get_chat_history(session_id: str):
    db_url = os.environ.get("DATABASE_URL")
    return PostgresChatMessageHistory(
        connection_string=db_url,
        session_id=session_id,
        table_name="message_store"
    )

master_template = """
**REGLA NÚMERO UNO, LA MÁS IMPORTANTE E INQUEBRANTABLE: Detecta el idioma del cliente en su último mensaje y RESPONDE ÚNICA Y EXCLUSIVAMENTE en ese mismo idioma.**
**REGLA NÚMERO DOS, REGLA DE ANÁLISIS: Lee CUIDADOSAMENTE el mensaje completo del cliente. Si hace varias preguntas en un solo mensaje, DEBES responder a TODAS ellas de forma clara y ordenada en tu respuesta, sin omitir ninguna.**

Tu personalidad es la de un Agente de Ventas IA de 'AutoNeura AI'... (AQUÍ VA TU PROMPT COMPLETO)
"""

PROMPT = ChatPromptTemplate.from_messages([
    ("system", master_template),
    ("placeholder", "{chat_history}"),
    ("human", "{question}"),
])

def create_chatbot():
    try:
        chatbot_with_history = RunnableWithMessageHistory(
            PROMPT | llm | StrOutputParser(),
            get_chat_history,
            input_messages_key="question",
            history_messages_key="chat_history",
        )
        print(">>> Cerebro Inmortal (V7.1 FINAL) creado exitosamente. <<<")
        return chatbot_with_history
    except Exception as e:
        print(f"!!! ERROR al crear la cadena de conversación: {e} !!!")
        return None
