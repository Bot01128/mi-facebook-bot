import os
import requests
from flask import Flask, request
from dotenv import load_dotenv
from cerebro import create_chatbot
from twilio.rest import Client  # Importamos la librería de Twilio

# --- CONFIGURACIÓN INICIAL ---
load_dotenv()
app = Flask(__name__)

# Leemos las credenciales de Twilio de las variables de entorno
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
# Este es el Page ID de tu página de Facebook, que actúa como el "número" remitente de Twilio
TWILIO_FACEBOOK_SENDER_ID = os.environ.get('TWILIO_FACEBOOK_SENDER_ID')

# Inicializamos el cliente de Twilio una sola vez
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# --- RUTA PRINCIPAL ---
@app.route('/')
def home():
    return "<h1>El servidor del Chatbot (versión Twilio) está funcionando</h1>", 200

# --- RUTA WEBHOOK PARA TWILIO ---
@app.route('/webhook', methods=['POST'])
def webhook():
    # Twilio envía los datos de forma diferente a Facebook (en un formulario, no en JSON)
    incoming_data = request.values
    print(f"--- Datos recibidos de Twilio: {incoming_data} ---")

    sender_id = incoming_data.get('From')
    message_text = incoming_data.get('Body')
    
    # Twilio añade el prefijo "messenger:" al ID del remitente. Lo quitamos.
    if sender_id and sender_id.startswith('messenger:'):
        sender_id = sender_id.replace('messenger:', '')

    if sender_id and message_text:
        print(f"--- Mensaje procesado de {sender_id}: '{message_text}' ---")

        # El cerebro sigue siendo el mismo, no cambia nada aquí
        final_chain = create_chatbot(session_id=sender_id)

        if final_chain is None:
            print(f"!!! ERROR: No se pudo crear el cerebro para {sender_id}.")
            return "OK", 200

        try:
            response_text = final_chain.invoke({"question": message_text})
            print(f"--- Respuesta generada por la IA: '{response_text}' ---")
            
            # Usamos la nueva función para enviar la respuesta a través de Twilio
            send_message_via_twilio(sender_id, response_text)
            print(f"--- Respuesta enviada a {sender_id} vía Twilio ---")
        
        except Exception as e:
            print(f"!!! ERROR AL PROCESAR EL MENSAJE: {e} !!!")
    
    return "OK", 200

# --- FUNCIÓN PARA ENVIAR MENSAJES VÍA TWILIO ---
def send_message_via_twilio(recipient_id, message_text):
    try:
        message = twilio_client.messages.create(
            to=f'messenger:{recipient_id}',
            from_=f'messenger:{TWILIO_FACEBOOK_SENDER_ID}',
            body=message_text
        )
        print(f"Mensaje enviado con SID: {message.sid}")
    except Exception as e:
        print(f"!!! ERROR al enviar mensaje con Twilio: {e} !!!")
