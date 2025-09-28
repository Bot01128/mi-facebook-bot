import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_message_histories import PostgresChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)

def get_chat_history(session_id: str):
    db_url = os.environ.get("DATABASE_URL")
    return PostgresChatMessageHistory(
        session_id=session_id,
        connection_string=db_url,
        table_name="message_store"
    )

PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Tu prompt va aquí..."),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
])

def create_chatbot():
    chain = PROMPT | llm
    return RunnableWithMessageHistory(
        chain,
        get_chat_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )
