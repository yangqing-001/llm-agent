#引入redis聊天消息存储类
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai.chat_models import ChatOpenAI

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You're an assistant who's good at {ability}. Respond in 20 words or fewer",
        ),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ]
)
model = ChatOpenAI(model="gpt-4")
runnable = prompt | model


REDIS_URL = "redis://localhost:6379/0"

def get_message_history(session_id: str) -> RedisChatMessageHistory:
    return RedisChatMessageHistory(session_id, url=REDIS_URL)


with_message_history = RunnableWithMessageHistory(
    runnable,
    get_message_history,
    input_messages_key="input",
    history_messages_key="history",
)
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
