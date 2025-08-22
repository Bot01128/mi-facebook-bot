import os
import requests
from flask import Flask, request
from dotenv import load_dotenv
from cerebro import create_chatbot # Importamos nuestra función principal del cerebro

# --- CONFIGURACIÓN INICIAL ---
load_dotenv()
app = Flask(__name__)

# Cargamos los tokens desde las Variables de Entorno
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')
PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN')

# Creamos una única instancia de nuestro bot cuando el servidor arranca.
print("--- INICIANDO CONFIGURACIÓN DEL CEREBRO DEL BOT ---")
try:
    final_chain = create_chatbot()
    print(">>> Instancia del Chatbot creada exitosamente. <<<")
except Exception as e:
    print(f"!!! ERROR CRÍTICO AL INICIAR EL BOT: {e} !!!")
    final_chain = None

# --- RUTA PRINCIPAL (SOLO PARA VERIFICAR QUE EL SERVIDOR ESTÁ VIVO) ---
@app.route('/')
def home():
    return "<h1>El servidor del Chatbot está funcionando</h1><p>¡Listo para conectar con Facebook!</p>", 200

# --- RUTA WEBHOOK (EL CORAZÓN DE LA CONEXIÓN CON FACEBOOK) ---
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # --- PARTE 1: La Verificación (para conectar con Facebook) ---
        token_sent = request.args.get("hub.verify_token")
        if token_sent == VERIFY_TOKEN:
            challenge = request.args.get("hub.challenge")
            print("--- VERIFICACIÓN DE WEBHOOK EXITOSA ---")
            return challenge, 200
        else:
            print("--- ERROR: VERIFICACIÓN DE WEBHOOK FALLIDA, TOKEN INVÁLIDO ---")
            return 'Token de verificación inválido', 403

    elif request.method == 'POST':
        # --- PARTE 2: Recibir y Responder Mensajes ---
        if final_chain is None:
            print("!!! ERROR: El chatbot no está inicializado, no se puede procesar el mensaje.")
            return "OK", 200

        data = request.get_json()
        if data and data.get("object") == "page":
            for entry in data.get("entry", []):
                for messaging_event in entry.get("messaging", []):
                    if messaging_event.get("message") and "text" in messaging_event["message"]:
                        sender_id = messaging_event["sender"]["id"]
                        message_text = messaging_event["message"]["text"]

                        print(f"--- Mensaje recibido de {sender_id}: '{message_text}' ---")

                        try:
                            # ¡AQUÍ ESTÁ LA CORRECCIÓN!
                            response_object = final_chain.invoke(message_text)
                            print(f"--- Objeto de respuesta completo: {response_object} ---")
                            
                            # Extraemos el texto de la respuesta del diccionario
                            response_text = response_object.get('text', 'Disculpa, no pude procesar tu solicitud en este momento.')

                            send_message(sender_id, response_text)
                            print(f"--- Respuesta enviada a {sender_id}: '{response_text}' ---")
                        
                        except Exception as e:
                            print(f"!!! ERROR AL PROCESAR EL MENSAJE: {e} !!!")
                            # Enviamos un mensaje de error genérico al usuario
                            send_message(sender_id, "Lo siento, estoy teniendo problemas técnicos. Por favor, inténtalo de nuevo más tarde.")

        return "OK", 200

# --- FUNCIÓN PARA ENVIAR MENSAJES DE VUELTA A FACEBOOK ---
def send_message(recipient_id, message_text):
    params = {
        "access_token": PAGE_ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    }
    try:
        r = requests.post("https://graph.facebook.com/v19.0/me/messages", params=params, headers=headers, json=data, timeout=10)
        if r.status_code != 200:
            print(f"!!! ERROR al enviar mensaje a Facebook API: {r.status_code} {r.text} !!!")
    except requests.exceptions.RequestException as e:
        print(f"!!! ERROR de conexión al enviar mensaje: {e} !!!")

# --- ARRANQUE DEL SERVIDOR (NO NECESARIO PARA GUNICORN) ---
# Gunicorn se encarga de esto, por lo que no necesitamos el bloque if __name__ == "__main__":
