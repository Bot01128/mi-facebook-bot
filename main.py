import os
import requests
from flask import Flask, request
from dotenv import load_dotenv
from cerebro import create_chatbot # Importamos nuestra función principal del cerebro

# --- CONFIGURACIÓN INICIAL ---
load_dotenv()
app = Flask(__name__)

# Cargamos los tokens desde los Secrets de Replit
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
        # Facebook envía un token para verificar que somos nosotros.
        token_sent = request.args.get("hub.verify_token")
        if token_sent == VERIFY_TOKEN:
            # Si el token es correcto, le devolvemos el "challenge" para confirmar.
            challenge = request.args.get("hub.challenge")
            print("--- VERIFICACIÓN DE WEBHOOK EXITOSA ---")
            return challenge, 200
        else:
            # Si el token es incorrecto, le decimos que no está autorizado.
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
                    if messaging_event.get("message"):
                        sender_id = messaging_event["sender"]["id"]
                        message_text = messaging_event["message"]["text"]

                        print(f"--- Mensaje recibido de {sender_id}: '{message_text}' ---")

                        # ¡Aquí usamos nuestro cerebro para obtener una respuesta!
                        response_text = final_chain.invoke(message_text)

                        send_message(sender_id, response_text)
                        print(f"--- Respuesta enviada a {sender_id}: '{response_text}' ---")

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
    r = requests.post("https://graph.facebook.com/v19.0/me/messages", params=params, headers=headers, json=data)
    if r.status_code != 200:
        print(f"!!! ERROR al enviar mensaje: {r.status_code} {r.text} !!!")

# --- ARRANQUE DEL SERVIDOR ---
if __name__ == "__main__":
    print("--- INICIANDO SERVIDOR FLASK ---")
    app.run(host='0.0.0.0', port=8080)