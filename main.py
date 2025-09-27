import os
from flask import Flask, request
from dotenv import load_dotenv
from twilio.rest import Client
from cerebro import create_chatbot

print(">>> [main.py] Cargando Módulo...")
load_dotenv()
app = Flask(__name__)
print(">>> [main.py] App Flask creada.")

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_FACEBOOK_SENDER_ID = os.environ.get('TWILIO_FACEBOOK_SENDER_ID')
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
print(">>> [main.py] Cliente Twilio inicializado.")

final_chain = create_chatbot()

@app.route('/')
def home():
    return "<h1>Servidor AutoNeura AI (Twilio) VIVO</h1>", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    incoming_data = request.values
    sender_id = incoming_data.get('From')
    message_text = incoming_data.get('Body')
    
    if sender_id and sender_id.startswith('messenger:'):
        sender_id = sender_id.replace('messenger:', '')

    if sender_id and message_text:
        print(f"--- Mensaje de {sender_id}: '{message_text}' ---")
        try:
            response_object = final_chain.invoke(
                {"input": message_text},
                config={"configurable": {"session_id": sender_id}}
            )
            response_text = response_object.content
            
            print(f"--- Respuesta IA: '{response_text}' ---")
            send_message_via_twilio(sender_id, response_text)
        except Exception as e:
            print(f"!!! ERROR al procesar mensaje: {e} !!!")
    
    return "OK", 200

def send_message_via_twilio(recipient_id, message_text):
    try:
        message = twilio_client.messages.create(
            to=f'messenger:{recipient_id}',
            from_=f'messenger:{TWILIO_FACEBOOK_SENDER_ID}',
            body=message_text
        )
        print(f"Mensaje enviado SID: {message.sid}")
    except Exception as e:
        print(f"!!! ERROR al enviar con Twilio: {e} !!!")

print(">>> [main.py] Módulo cargado.")
