import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
# from twilio.rest import Client  <-- YA NO USAMOS TWILIO
from cerebro import create_chatbot # <-- ESTO ES TU CEREBRO, LO DEJAMOS QUIETO

print(">>> [main.py] Cargando Módulo... VERSIÓN JIREH-META (CEREBRO ACTIVO)")
load_dotenv()
app = Flask(__name__)

# --- CONFIGURACIÓN DE JIREH C.A. (META DIRECTO) ---
# PEGA AQUÍ EL TOKEN LARGO QUE GUARDASTE (EAAdYe...):
WHATSAPP_TOKEN = "PEGA_TU_TOKEN_LARGO_AQUI"

# TUS IDENTIFICADORES (Ya están puestos):
PHONE_NUMBER_ID = "990084764187764" 
VERIFY_TOKEN = "HOLA_JIREH"  # Contraseña para verificar con Facebook

# --- INICIALIZACIÓN DEL CEREBRO (INTACTO) ---
try:
    final_chain = create_chatbot()
    print(">>> [main.py] CEREBRO IA CARGADO EXITOSAMENTE 🧠")
except Exception as e:
    print(f"!!! ERROR CRÍTICO CARGANDO CEREBRO: {e}")
    final_chain = None

# --- RUTA PRINCIPAL ---
@app.route('/')
def home():
    return "<h1>Servidor JIREH C.A. (Cerebro + Meta) está VIVO 🤖🚀</h1>", 200

# --- VERIFICACIÓN DEL WEBHOOK (OBLIGATORIO PARA FACEBOOK) ---
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print(">>> WEBHOOK VERIFICADO CON FACEBOOK ✅")
            return challenge, 200
        else:
            return "Token incorrecto", 403
    return "Hola, ruta de verificación activa.", 200

# --- RECEPCIÓN DE MENSAJES (POST) ---
@app.route('/webhook', methods=['POST'])
def webhook():
    # 1. Recibir el JSON de Facebook
    body = request.get_json()
    
    try:
        if body.get("object"):
            # Verificar si hay un mensaje válido dentro de la estructura compleja de Meta
            if (
                body.get("entry")
                and body["entry"][0].get("changes")
                and body["entry"][0]["changes"][0].get("value")
                and body["entry"][0]["changes"][0]["value"].get("messages")
            ):
                # 2. Extraer datos
                change = body["entry"][0]["changes"][0]["value"]
                message = change["messages"][0]
                phone_number = message["from"] # Número del cliente
                
                # Solo procesamos texto por ahora
                if "text" in message:
                    user_message = message["text"]["body"]
                    print(f"--- [JIREH] Mensaje de {phone_number}: '{user_message}' ---")

                    # 3. LLAMAR A TU CEREBRO (Aquí está tu código original)
                    if final_chain:
                        try:
                            # Invocamos a tu IA igual que antes
                            response_object = final_chain.invoke(
                                {"input": user_message},
                                config={"configurable": {"session_id": phone_number}}
                            )
                            # Extraemos la respuesta de texto
                            ai_response_text = response_object.content
                            
                            print(f"--- [JIREH] Respuesta IA: '{ai_response_text}' ---")
                            
                            # 4. ENVIAR RESPUESTA VÍA META (Nueva función)
                            send_whatsapp_message(phone_number, ai_response_text)
                            
                        except Exception as e_ai:
                            print(f"!!! ERROR CEREBRO IA: {e_ai}")
                            send_whatsapp_message(phone_number, "Lo siento, estoy reiniciando mis neuronas. Intenta de nuevo.")
                    else:
                        print("!!! EL CEREBRO NO ESTÁ CARGADO !!!")

            return jsonify({"status": "success"}), 200
        else:
            return "No object", 404

    except Exception as e:
        print(f"Error procesando mensaje: {e}")
        return "Error", 500

# --- NUEVA FUNCIÓN DE ENVÍO (META GRAPH API) ---
def send_whatsapp_message(to_number, text_body):
    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text_body},
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print("✅ Mensaje enviado a WhatsApp")
        else:
            print(f"❌ Error enviando a WhatsApp: {response.text}")
    except Exception as e:
        print(f"Error de conexión enviando: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
