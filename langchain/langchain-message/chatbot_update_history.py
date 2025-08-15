from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

temp_chat_history = ChatMessageHistory()
temp_chat_history.add_user_message("我叫Jack，你好")
temp_chat_history.add_ai_message("你好")
temp_chat_history.add_user_message("我今天心情挺开心")
temp_chat_history.add_ai_message("你今天心情怎么样")
temp_chat_history.add_user_message("我下午在打篮球")
temp_chat_history.add_ai_message("你下午在做什么")
temp_chat_history.messages

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是一个乐于助人的助手。尽力回答所有问题。提供的聊天历史包括与您交谈的用户的事实。",
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ]
)
chat = ChatOpenAI(model="gpt-4")
chain = prompt | chat
chain_with_message_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: temp_chat_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)
response = chain_with_message_history.invoke(
    {"input": "我今天心情如何?"},
    {"configurable": {"session_id": "unused"}},
)
print(response)
print(temp_chat_history.messages)