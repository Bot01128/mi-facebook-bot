@app.route('/webhook', methods=['POST'])
def webhook():
    # Twilio envía los datos de forma diferente a Facebook
    incoming_data = request.values
    print(f"--- Datos recibidos de Twilio: {incoming_data} ---")

    sender_id = incoming_data.get('From')
    message_text = incoming_data.get('Body')
    
    # Quitamos el prefijo "messenger:" que añade Twilio al sender_id
    if sender_id and sender_id.startswith('messenger:'):
        sender_id = sender_id.replace('messenger:', '')

    if sender_id and message_text:
        print(f"--- Mensaje procesado de {sender_id}: '{message_text}' ---")

        final_chain = create_chatbot(session_id=sender_id)

        if final_chain is None:
            print(f"!!! ERROR: No se pudo crear el cerebro para {sender_id}.")
            return "OK", 200

        try:
            response_text = final_chain.invoke({"question": message_text})
            print(f"--- Respuesta generada por la IA: {response_text} ---")
            
            # Ahora enviamos la respuesta usando la librería de Twilio
            send_message_via_twilio(sender_id, response_text)
            print(f"--- Respuesta enviada a {sender_id} vía Twilio ---")
        
        except Exception as e:
            print(f"!!! ERROR AL PROCESAR EL MENSAJE: {e} !!!")
    
    return "OK", 200
