import os
import requests
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.tools.tavily_search import TavilySearchResults

print("--- INICIANDO SCRIPT DE SEGUIMIENTO PROACTIVO ---")

# --- CONFIGURACIÓN ---
DATABASE_URL = os.environ.get("DATABASE_URL")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

# Inicializamos el modelo de lenguaje y la herramienta de búsqueda
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
search = TavilySearchResults()

# --- PLANTILLAS DE PROMPT PARA EL INVESTIGADOR ---

topic_prompt = PromptTemplate.from_template(
    "Basado en esta conversación, extrae el tema principal o el interés del cliente en una o dos palabras clave para una búsqueda en internet. Conversación: {conversation}"
)

follow_up_prompt = PromptTemplate.from_template(
    """Eres un asistente proactivo y amigable de AutoNeura AI. Tu misión es recontactar a un cliente potencial que no ha respondido en más de 24 horas.

    Contexto de la conversación anterior: {conversation}
    Información de valor que has encontrado en internet sobre su interés ('{topic}'): {search_results}

    Tu Tarea: Escribe un mensaje de seguimiento corto, amigable y que no presione.
    1.  Empieza saludando ("¡Hola de nuevo!").
    2.  Menciona que estabas pensando en su conversación.
    3.  Aporta el dato de valor que encontraste de forma muy breve.
    4.  Termina con un llamado a la acción suave y abierto.
    5.  IMPORTANTE: Escribe el mensaje en el mismo idioma de la conversación.

    Ejemplo de mensaje: "¡Hola de nuevo! Pensando en nuestra conversación sobre los paquetes de Agentes IA, encontré este dato interesante: [dato de valor]. Si te surge alguna otra duda o quieres que exploremos cómo se aplicaría a tu negocio, aquí estoy para ayudarte. ¡Sin compromiso!"

    Escribe solo el mensaje de seguimiento:
    """
)

# --- FUNCIÓN PARA ENVIAR MENSAJE ---
def send_facebook_message(recipient_id, message_text):
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    r = requests.post("https://graph.facebook.com/v19.0/me/messages", params=params, headers=headers, json=data)
    if r.status_code == 200:
        print(f"Mensaje de seguimiento enviado exitosamente a {recipient_id}")
    else:
        print(f"!!! ERROR al enviar mensaje de seguimiento a {recipient_id}: {r.status_code} {r.text}")

# --- LÓGICA PRINCIPAL ---
def run_follow_up():
    if not DATABASE_URL:
        print("!!! ERROR CRÍTICO: DATABASE_URL no encontrada. Abortando seguimiento. !!!")
        return

    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        # 1. Buscar conversaciones que no han sido actualizadas en las últimas 48 horas pero sí en los últimos 7 días
        # y que no hayamos contactado ya.
        query = text("""
            SELECT session_id, MAX(created_at) as last_message_time
            FROM langchain_chat_histories
            WHERE session_id NOT IN (SELECT session_id FROM follow_up_log)
            GROUP BY session_id
            HAVING MAX(created_at) BETWEEN NOW() - INTERVAL '7 days' AND NOW() - INTERVAL '24 hours';
        """)
        inactive_sessions = connection.execute(query).fetchall()

        print(f"Se encontraron {len(inactive_sessions)} conversaciones inactivas para seguimiento.")

        for session in inactive_sessions:
            session_id = session[0]
            print(f"--- Procesando seguimiento para: {session_id} ---")

            # 2. Obtener el historial de la conversación
            history_query = text("SELECT message FROM langchain_chat_histories WHERE session_id = :sid ORDER BY created_at DESC LIMIT 6")
            messages_raw = connection.execute(history_query, {"sid": session_id}).fetchall()
            conversation_history = "\n".join([str(msg[0]) for msg in reversed(messages_raw)])

            # 3. Usar la IA para determinar el tema de búsqueda
            topic_chain = LLMChain(llm=llm, prompt=topic_prompt)
            topic = topic_chain.run(conversation_history)
            print(f"Tema de interés detectado: {topic}")

            # 4. Buscar en internet
            search_results = search.run(topic)
            print(f"Resultados de búsqueda encontrados: {search_results[:100]}...") # Mostramos solo los primeros 100 caracteres

            # 5. Usar la IA para generar el mensaje de seguimiento
            follow_up_chain = LLMChain(llm=llm, prompt=follow_up_prompt)
            message_to_send = follow_up_chain.run({
                "conversation": conversation_history,
                "topic": topic,
                "search_results": search_results
            })

            # 6. Enviar el mensaje
            send_facebook_message(session_id, message_to_send)
            
            # 7. Registrar que ya hemos contactado a este usuario para no volver a hacerlo
            log_query = text("INSERT INTO follow_up_log (session_id, created_at) VALUES (:sid, NOW()) ON CONFLICT (session_id) DO NOTHING;")
            connection.execute(log_query, {"sid": session_id})
            connection.commit() # Guardamos el registro en la base de datos
            print(f"Usuario {session_id} registrado en el log de seguimiento.")

if __name__ == "__main__":
    # Creamos la tabla de seguimiento si no existe
    if DATABASE_URL:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS follow_up_log (
                    session_id VARCHAR(255) PRIMARY KEY,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))
            connection.commit()
            print("Tabla 'follow_up_log' verificada/creada exitosamente.")
    
    run_follow_up()
    print("--- SCRIPT DE SEGUIMIENTO PROACTIVO FINALIZADO ---")
