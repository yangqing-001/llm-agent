from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai.chat_models import ChatOpenAI
#引入聊天消息历史记录
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

#创建一个聊天提示词模版
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You're an assistant who's good at {ability}. Respond in 20 words or fewer",
        ),
        #历史消息占位符
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ]
)
model = ChatOpenAI(model="gpt-4")
runnable = prompt | model

#用来存储会话历史记录
store = {}


#定义个获取会话历史的函数，入参是session_id，返回一个会话历史记录
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


#创建一个带会话历史记录的Runnable
with_message_history = RunnableWithMessageHistory(
    runnable,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)
#调用带会话历史记录的Runnable
response = with_message_history.invoke(
    {"ability": "math", "input": "余弦是什么意思？"},
    config={"configurable": {"session_id": "abc123"}},
)
print(response)
# content="Cosine is a trigonometric function comparing the ratio of an angle's adjacent side to its hypotenuse in a right triangle." response_metadata={'token_usage': {'completion_tokens': 27, 'prompt_tokens': 33, 'total_tokens': 60}, 'model_name': 'gpt-4-0613', 'system_fingerprint': None, 'finish_reason': 'stop', 'logprobs': None} id='run-c383660d-7195-4b36-9175-992f05739ece-0' usage_metadata={'input_tokens': 33, 'output_tokens': 27, 'total_tokens': 60}

# 记住
response = with_message_history.invoke(
    {"ability": "math", "input": "什么?"},
    config={"configurable": {"session_id": "abc123"}},
)
print(response)

# 新的 session_id --> 不记得了。
response = with_message_history.invoke(
    {"ability": "math", "input": "什么?"},
    config={"configurable": {"session_id": "def234"}},
)
print(response)
