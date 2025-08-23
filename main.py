import os
import requests
from flask import Flask, request
from dotenv import load_dotenv
from cerebro import create_chatbot
from seguimiento import run_follow_up 
import threading
import time

# --- CONFIGURACIÓN INICIAL ---
load_dotenv()
app = Flask(__name__)
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')
PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN')
last_follow_up_time = 0

# Creamos una única instancia de nuestro cerebro con memoria al arrancar.
final_chain = create_chatbot()

# --- RUTA PRINCIPAL (CON LÓGICA DE AUTODESPERTADOR) ---
@app.route('/')
def home():
    global last_follow_up_time
    # Revisa si ha pasado al menos 12 horas desde el último seguimiento
    if (time.time() - last_follow_up_time) > 43200: # 43200 segundos = 12 horas
        print("--- DISPARANDO SEGUIMIENTO PROACTIVO (VIA UPTIMEROBOT) ---")
        # Ejecutamos el seguimiento en un hilo separado para no bloquear la respuesta
        thread = threading.Thread(target=run_follow_up)
        thread.start()
        last_follow_up_time = time.time()
    
    return "<h1>El servidor del Chatbot está funcionando</h1><p>¡Listo para conectar con Facebook!</p>", 200

# --- RUTA WEBHOOK ---
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        token_sent = request.args.get("hub.verify_token")
        if token_sent == VERIFY_TOKEN:
            challenge = request.args.get("hub.challenge")
            return challenge, 200
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
                            print("!!! ERROR CRÍTICO: El cerebro no se pudo inicializar.")
                            send_message(sender_id, "Lo siento, estoy teniendo un problema grave. Por favor, contacta al administrador.")
                            continue

                        print(f"--- Mensaje recibido de {sender_id}: '{message_text}' ---")

                        try:
                            # La nueva forma de invocar, pasando la configuración con el session_id
                            response_text = final_chain.invoke(
                                {"question": message_text},
                                config={"configurable": {"session_id": sender_id}}
                            )
                            
                            print(f"--- Respuesta generada: {response_text} ---")
                            send_message(sender_id, response_text)
                            print(f"--- Respuesta enviada a {sender_id} ---")
                        
                        except Exception as e:
                            print(f"!!! ERROR AL PROCESAR EL MENSAJE: {e} !!!")
                            send_message(sender_id, "Lo siento, estoy teniendo problemas técnicos. Por favor, inténtalo de nuevo más tarde.")
        return "OK", 200

# --- FUNCIÓN PARA ENVIAR MENSAJES ---
def send_message(recipient_id, message_text):
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    try:
        r = requests.post("https://graph.facebook.com/v19.0/me/messages", params=params, headers=headers, json=data, timeout=10)
        if r.status_code != 200:
            print(f"!!! ERROR al enviar mensaje a Facebook API: {r.status_code} {r.text} !!!")
    except requests.exceptions.RequestException as e:
        print(f"!!! ERROR de conexión al enviar mensaje: {e} !!!")
