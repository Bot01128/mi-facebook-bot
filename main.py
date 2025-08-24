import os
import requests
from flask import Flask, request
from dotenv import load_dotenv
from cerebro import get_chatbot_with_history

load_dotenv()
app = Flask(__name__)

VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')
PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN')

# Obtenemos la cadena con memoria UNA SOLA VEZ al iniciar.
final_chain = get_chatbot_with_history()

@app.route('/')
def home():
    return "<h1>El servidor del Chatbot está funcionando</h1><p>¡Listo para conectar con Facebook!</p>", 200

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        token_sent = request.args.get("hub.verify_token")
        if token_sent == VERIFY_TOKEN:
            return request.args.get("hub.challenge"), 200
        return 'Token de verificación inválido', 403

    elif request.method == 'POST':
        data = request.get_json()
        if data and data.get("object") == "page":
            for entry in data.get("entry", []):
                for messaging_event in entry.get("messaging", []):
                    if messaging_event.get("message") and "text" in messaging_event["message"]:
                        sender_id = messaging_event["sender"]["id"]
                        message_text = messaging_event["message"]["text"]
                        
                        if final_chain is None:
                            print(f"!!! ERROR CRÍTICO: El cerebro no se inicializó.")
                            continue

                        print(f"--- Mensaje recibido de {sender_id}: '{message_text}' ---")
                        try:
                            # --- ¡ESTA ES LA INVOCACIÓN CORRECTA! ---
                            # Pasamos el 'session_id' en el objeto 'config'
                            response_text = final_chain.invoke(
                                {"input": message_text},
                                config={"configurable": {"session_id": sender_id}}
                            )
                            
                            send_message(sender_id, response_text)
                            print(f"--- Respuesta enviada a {sender_id} ---")
                        
                        except Exception as e:
                            print(f"!!! ERROR AL PROCESAR EL MENSAJE: {e} !!!")
                            send_message(sender_id, "Lo siento, estoy teniendo problemas técnicos.")
        return "OK", 200

def send_message(recipient_id, message_text):
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    data = {"recipient": {"id": recipient_id}, "message": {"text": message_text}}
    try:
        r = requests.post("https://graph.facebook.com/v19.0/me/messages", params=params, headers=headers, json=data, timeout=10)
        if r.status_code != 200:
            print(f"!!! ERROR al enviar mensaje a Facebook API: {r.status_code} {r.text} !!!")
    except requests.exceptions.RequestException as e:
        print(f"!!! ERROR de conexión al enviar mensaje: {e} !!!")
