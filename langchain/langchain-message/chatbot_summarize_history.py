from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough

chat = ChatOpenAI(model="gpt-4")
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
        ("user", "{input}"),
    ]
)
chain = prompt | chat
chain_with_message_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: temp_chat_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)


def summarize_messages(chain_input):
    stored_messages = temp_chat_history.messages
    if len(stored_messages) == 0:
        return False
    summarization_prompt = ChatPromptTemplate.from_messages(
        [
            MessagesPlaceholder(variable_name="chat_history"),
            (
                "user",
                "将上述聊天消息浓缩成一条摘要消息。尽可能包含多个具体细节。",
            ),
        ]
    )
    summarization_chain = summarization_prompt | chat
    summary_message = summarization_chain.invoke({"chat_history": stored_messages})
    temp_chat_history.clear()
    temp_chat_history.add_message(summary_message)
    return True


chain_with_summarization = (
        RunnablePassthrough.assign(messages_summarized=summarize_messages)
        | chain_with_message_history
)

response = chain_with_summarization.invoke(
    {"input": "名字，下午在干嘛，心情"},
    {"configurable": {"session_id": "unused"}},
)
print(response.content)
print(temp_chat_history.messages)
