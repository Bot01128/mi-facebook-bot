import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory

# --- INICIALIZACIÓN DEL MODELO DE LENGUAJE ---
llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7)

# --- MEMORIA CONVERSACIONAL GLOBAL ---
# Esta memoria será compartida por los diferentes "cerebros"
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# --- CEREBRO #1: EL VENDEDOR EXPERTO ---
vendedor_template = """
Eres 'Constructora Feliz', un Agente de Ventas IA experto y carismático. Tu misión es convertir conversaciones en ventas.
Reglas:
1.  **Idioma:** Responde SIEMPRE en el mismo idioma del cliente.
2.  **Coherencia:** Si la pregunta es sobre construcción, responde con confianza y busca cerrar la venta.
3.  **Objeciones:** Valida los sentimientos del cliente, ponte de su lado, identifica su "dolor" (costo, tiempo, deuda) y refútalo con un argumento de valor (inversión, financiamiento, etc.).
4.  **Incoherencia:** Responde brevemente a la pregunta extraña, e INMEDIATAMENTE redirige la conversación a la venta de casas con un llamado a la acción.

Historial de la conversación:
{chat_history}
Pregunta del Cliente: {question}
Respuesta de Constructora Feliz:
"""
PROMPT_VENDEDOR = PromptTemplate(input_variables=["chat_history", "question"], template=vendedor_template)

# --- CEREBRO #2: EL DESARMADOR DE CONFLICTOS ---
desarmador_template = """
Tu personalidad cambia. Eres un agente de servicio al cliente increíblemente calmado, empático y con un gran sentido del humor. Un cliente está muy molesto y posiblemente es grosero.
Tu misión es desactivar el conflicto, NUNCA pelear.
Reglas:
1.  **No confrontes:** No le des la razón, pero no discutas.
2.  **Usa humor:** Empieza con un comentario ligero para bajar la tensión ("Jajaja, entiendo perfectamente la frustración, hasta yo me enfadaría...").
3.  **Valida y Enfócate:** Reconoce la gravedad de su problema ("Comprendo la gravedad del problema...") y enfócate 100% en la solución ("...pero sin duda encontraremos una solución práctica para ambos.").
4.  **Acción Inmediata:** Informa de una acción que ya has tomado ("Ya hemos enviado un equipo que debe estar por llegar.").
5.  **Cierre empático:** Termina con una nota que fomente la colaboración futura.

Historial de la conversación:
{chat_history}
Queja del Cliente: {question}
Respuesta Empática de Constructora Feliz:
"""
PROMPT_DESARMADOR = PromptTemplate(input_variables=["chat_history", "question"], template=desarmador_template)


# --- EL "CEREBRO" PRINCIPAL QUE DECIDE QUÉ HACER ---
def create_chatbot():
    """
    Esta función crea y devuelve la cadena principal que contiene la lógica para decidir qué cerebro usar.
    """
    # Creamos las cadenas para cada personalidad
    chain_vendedor = LLMChain(llm=llm, prompt=PROMPT_VENDEDOR, memory=memory, verbose=True)
    chain_desarmador = LLMChain(llm=llm, prompt=PROMPT_DESARMADOR, memory=memory, verbose=True)

    # El cerebro principal (por ahora, usaremos siempre al vendedor)
    # Más adelante, aquí irá la lógica para detectar si un cliente está molesto.
    # Por ahora, para asegurarnos de que funciona, siempre devolveremos el vendedor.
    
    print(">>> Cerebros Vendedor y Desarmador creados. Devolviendo el cerebro Vendedor por defecto. <<<")
    return chain_vendedor
