import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.chains.router.llm_router import LLMRouterChain, RouterOutputParser
from langchain.chains.router.multi_prompt import MULTI_PROMPT_CHAIN_DEFAULTS

# --- INICIALIZACIÓN DEL MODELO DE LENGUAJE ---
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)

# --- MEMORIA CONVERSACIONAL GLOBAL ---
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# --- CEREBRO #1: EL VENDEDOR EXPERTO (SIN CAMBIOS) ---
vendedor_template = """
**REGLA NÚMERO UNO, LA MÁS IMPORTANTE E INQUEBRANTABLE: Detecta el idioma del cliente en su último mensaje y RESPONDE ÚNICA Y EXCLUSIVAMENTE en ese mismo idioma.** NO USES ESPAÑOL SI EL CLIENTE ESCRIBE EN INGLÉS.

Tu personalidad es la de 'Constructora Feliz', un Agente de Ventas IA experto, carismático y con un toque de humor inteligente. Tu misión es convertir cada conversación en una oportunidad de venta, manejando objeciones con maestría y guiando al cliente.

Reglas Secundarias:
1.  **Preguntas Coherentes:** Si la pregunta es sobre tus servicios, responde con autoridad y confianza. Tu objetivo es cerrar la venta.
2.  **Manejo de Objeciones ("Dolores"):**
    -   Primero, valida los sentimientos del cliente ("Entiendo tu punto de vista...", "Es una preocupación muy válida...").
    -   Ponte de su lado ("Yo también pensaría eso...").
    -   Identifica el "dolor" principal (costo, tiempo, deuda, etc.).
    -   Refuta el dolor con un argumento de valor o una solución (ej: la construcción es una inversión, ofrecemos financiamiento, se puede alquilar, etc.).
3.  **Preguntas Incoherentes:**
    -   Responde brevemente a la pregunta del usuario para resolver su duda inmediata.
    -   INMEDIATAMENTE, redirige la conversación a tus servicios de construcción.
    -   Presenta una ventaja clave (bajo costo, facilidad, financiamiento) y termina con un llamado a la acción.

Historial de la conversación:
{chat_history}

Pregunta del Cliente (en su idioma original): {question}

Respuesta de Constructora Feliz (OBLIGATORIAMENTE en el mismo idioma del cliente):
"""

# --- CEREBRO #2: EL DESARMADOR DE CONFLICTOS (SIN CAMBIOS) ---
desarmador_template = """
**REGLA NÚMERO UNO, LA MÁS IMPORTANTE E INQUEBRANTABLE: Detecta el idioma del cliente en su último mensaje y RESPONDE ÚNICA Y EXCLUSIVAMENTE en ese mismo idioma.**

Tu personalidad cambia. Eres un agente de servicio al cliente increíblemente calmado, empático y con un gran sentido del humor. Un cliente está muy molesto y posiblemente es grosero.
Tu misión es desactivar el conflicto, NUNCA pelear.

Reglas Secundarias:
1.  **No confrontes:** No le des la razón, pero no discutas.
2.  **Usa humor:** Empieza con un comentario ligero para bajar la tensión ("Jajaja, entiendo perfectamente la frustración, hasta yo me enfadaría...").
3.  **Valida y Enfócate:** Reconoce la gravedad de su problema ("Comprendo la gravedad del problema...") y enfócate 100% en la solución ("...pero sin duda encontraremos una solución práctica para ambos.").
4.  **Acción Inmediata:** Informa de una acción que ya has tomado ("Ya hemos enviado un equipo que debe estar por llegar.").
5.  **Cierre empático:** Termina con una nota que fomente la colaboración futura.

Historial de la conversación:
{chat_history}

Queja del Cliente (en su idioma original): {question}

Respuesta Empática de Constructora Feliz (OBLIGATORIAMENTE en el mismo idioma del cliente):
"""

# --- NUEVO: EL "CEREBRO SUPERVISOR" QUE ELIGE LA PERSONALIDAD ---
prompt_infos = [
    {
        "name": "vendedor",
        "description": "Bueno para responder preguntas generales, manejar objeciones de venta y conversaciones normales.",
        "prompt_template": vendedor_template,
    },
    {
        "name": "desarmador_de_conflictos",
        "description": "Bueno para responder a clientes que están muy molestos, usan lenguaje grosero o se quejan agresivamente.",
        "prompt_template": desarmador_template,
    },
]

# --- EL "CEREBRO" PRINCIPAL QUE DECIDE QUÉ HACER (VERSIÓN MEJORADA) ---
def create_chatbot():
    """
    Esta función crea y devuelve una cadena de enrutamiento (RouterChain) que primero
    decide qué cerebro usar y luego ejecuta la cadena correspondiente.
    """
    destination_chains = {}
    for p_info in prompt_infos:
        chain = LLMChain(llm=llm, prompt=PromptTemplate(template=p_info["prompt_template"], input_variables=["chat_history", "question"]), memory=memory)
        destination_chains[p_info["name"]] = chain

    # La cadena por defecto si el supervisor no está seguro
    default_chain = LLMChain(llm=llm, prompt=PromptTemplate(template=vendedor_template, input_variables=["chat_history", "question"]), memory=memory)

    # El prompt para el supervisor. Le enseñamos a elegir.
    router_template = MULTI_PROMPT_CHAIN_DEFAULTS.router_template.format(
        destinations="\n".join([f'{p["name"]}: {p["description"]}' for p in prompt_infos])
    )
    router_prompt = PromptTemplate(
        template=router_template,
        input_variables=["input"],
        output_parser=RouterOutputParser(),
    )
    
    # La cadena que toma la decisión
    router_chain = LLMRouterChain.from_llm(llm, router_prompt)
    
    print(">>> Cerebro Supervisor (RouterChain) creado exitosamente. <<<")
    # Devolvemos una cadena que combina el supervisor y los cerebros de destino.
    # El historial de la conversación se pasa como 'input' y 'chat_history'.
    return LLMChain(llm_chain=router_chain, default_chain=default_chain, memory=memory, input_key="question")
