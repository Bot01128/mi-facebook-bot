import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableBranch, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

# --- NUEVA FUNCIÓN PARA CARGAR DATOS DESDE GOOGLE SHEETS ---
def load_data_from_google_sheet():
    print("--- Cargando datos desde Google Sheets... ---")

    creds_json_str = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
    if not creds_json_str:
        raise ValueError("El Secret 'GOOGLE_SHEETS_CREDENTIALS' no fue encontrado.")

    creds_dict = json.loads(creds_json_str)

    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    try:
        sheet_file = client.open("Client_Knowledge_Base_Template")
        business_info_sheet = sheet_file.worksheet("Business_Info")
        business_info_data = business_info_sheet.get_all_records()

        catalog_sheet = sheet_file.worksheet("Catalog")
        catalog_data = catalog_sheet.get_all_records()

        faqs_sheet = sheet_file.worksheet("FAQs")
        faqs_data = faqs_sheet.get_all_records()

        print(">>> Datos cargados exitosamente desde Google Sheets. <<<")
    except gspread.exceptions.SpreadsheetNotFound:
        raise ValueError("Hoja de cálculo 'Client_Knowledge_Base_Template' no encontrada. Asegúrate de que el nombre es correcto y que has compartido la hoja con el email del bot.")
    except gspread.exceptions.WorksheetNotFound as e:
        raise ValueError(f"Una de las pestañas requeridas no se encontró. Error: {e}")

    knowledge_base_text = ""

    business_name = "our store"
    for item in business_info_data:
        if item.get('Key') == 'Business_Name':
            business_name = item.get('Value', 'our store')
        knowledge_base_text += f"{item.get('Key', '')}: {item.get('Value', '')}\n"
    knowledge_base_text += "\n"

    knowledge_base_text += "Product Catalog:\n"
    for item in catalog_data:
        knowledge_base_text += f"- Product: {item.get('Product', '')}, Description: {item.get('Description', '')}, Price: {item.get('Price', '')}\n"
    knowledge_base_text += "\n"

    knowledge_base_text += "Frequently Asked Questions:\n"
    for item in faqs_data:
        knowledge_base_text += f"Question: {item.get('Question', '')}\nAnswer: {item.get('Answer', '')}\n\n"

    return knowledge_base_text, business_name


# Función para determinar si la pregunta es relevante
def is_question_relevant(input_dict):
    question = input_dict["question"]
    retriever = input_dict["retriever"]
    llm = input_dict["llm"]
    retrieved_docs = retriever.invoke(question)
    context = "\n\n".join(doc.page_content for doc in retrieved_docs)
    prompt = ChatPromptTemplate.from_template(
        """Based on the following CONTEXT from a hardware store, is the user's QUESTION related to this topic?
        Answer only with "YES" or "NO".

        CONTEXT:
        {context}

        QUESTION:
        {question}

        ANSWER (YES/NO):"""
    )
    chain = prompt | llm | StrOutputParser()
    result = chain.invoke({"context": context, "question": question})
    is_relevant = result.strip().upper() == "YES"
    print(f"--- Relevance Triage: Is the question '{question}' relevant? -> {'YES' if is_relevant else 'NO'}")
    return is_relevant

# --- FUNCIÓN PRINCIPAL QUE main.py VA A IMPORTAR ---
def create_chatbot():
    print("Initializing chatbot configuration (v. Google Sheets)...")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Google API key not found.")

    print("Google API Key loaded.")

    knowledge_base_content, business_name_from_sheet = load_data_from_google_sheet()
    docs = [Document(page_content=knowledge_base_content)]

    vector_store = Chroma.from_documents(
        documents=docs, 
        embedding=GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key, task_type="retrieval_query")
    )
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    print("Vector database created from Google Sheets data.")

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0.5, google_api_key=api_key)

    # --- Cerebro 1: Cadena para preguntas relevantes ---
    relevant_prompt = ChatPromptTemplate.from_template(
        """You are an expert sales assistant for "{business_name}".
        Use the following CONTEXT to answer the user's QUESTION completely and helpfully.
        Your goal is to resolve their query and encourage them to visit the store.

        CONTEXT:
        {context}

        QUESTION:
        {question}

        HELPFUL ANSWER:"""
    )
    relevant_chain = (
        RunnablePassthrough.assign(
            context=lambda x: retriever.invoke(x["question"]),
            business_name=lambda x: business_name_from_sheet 
        )
        | relevant_prompt
        | llm
        | StrOutputParser()
    )

    # --- Cerebro 2: Cadena para preguntas irrelevantes ---
    irrelevant_prompt = ChatPromptTemplate.from_template(
        """A user has asked a question unrelated to our business (a hardware store). Follow these 3 steps:
        1. Answer their question briefly, usefully, and in a friendly tone.
        2. Touch on a common "pain point" or frustration related to their question.
        3. Connect that "pain point" to products or solutions a hardware store could offer, inviting them to visit.

        USER'S QUESTION:
        {question}

        STRATEGIC RESPONSE:"""
    )
    irrelevant_chain = irrelevant_prompt | llm | StrOutputParser()

    # --- El "Cableado" Correcto que decide qué cerebro usar ---
    branch = RunnableBranch(
        (is_question_relevant, relevant_chain),
        irrelevant_chain
    )

    # --- La Cadena Completa ---
    full_chain = RunnablePassthrough.assign(
        retriever=lambda x: retriever,
        llm=lambda x: llm
    ) | branch

    print("Chatbot configured and ready!")

    # --- CORRECCIÓN FINAL: Devolvemos la cadena completa que espera un diccionario de entrada ---
    # `main.py` le dará a esta cadena un diccionario que contiene la "question".
    return full_chain