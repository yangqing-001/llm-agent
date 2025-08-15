from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai.chat_models import ChatOpenAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
#引入langchain 的配置
from langchain_core.runnables import ConfigurableFieldSpec

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
store = {}


def get_session_history(user_id: str, conversation_id: str) -> BaseChatMessageHistory:
    if (user_id, conversation_id) not in store:
        store[(user_id, conversation_id)] = ChatMessageHistory()
    return store[(user_id, conversation_id)]


with_message_history = RunnableWithMessageHistory(
    runnable,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
    history_factory_config=[
        ConfigurableFieldSpec(
            id="user_id",
            annotation=str,
            name="User ID",
            description="用户的唯一标识符。",
            default="",
            is_shared=True,
        ),
        ConfigurableFieldSpec(
            id="conversation_id",
            annotation=str,
            name="Conversation ID",
            description="对话的唯一标识符。",
            default="",
            is_shared=True,
        ),
    ],
)

response = with_message_history.invoke(
    {"ability": "math", "input": "余弦是什么意思？"},
    config={"configurable": {"user_id": "123", "conversation_id": "1"}},
)
print(response)
#content='余弦是一个三角函数，它表示直角三角形的邻边长度和斜边长度的比值。' response_metadata={'token_usage': {'completion_tokens': 33, 'prompt_tokens': 38, 'total_tokens': 71}, 'model_name': 'gpt-4-0613', 'system_fingerprint': None, 'finish_reason': 'stop', 'logprobs': None} id='run-2d1eba02-4709-4db5-ab6b-0fd03ab4c68a-0' usage_metadata={'input_tokens': 38, 'output_tokens': 33, 'total_tokens': 71}


# 记住
response = with_message_history.invoke(
    {"ability": "math", "input": "什么?"},
    config={"configurable": {"user_id": "123", "conversation_id": "1"}},
)
print(response)
#content='余弦是一个数学术语，代表在一个角度下的邻边和斜边的比例。' response_metadata={'token_usage': {'completion_tokens': 32, 'prompt_tokens': 83, 'total_tokens': 115}, 'model_name': 'gpt-4-0613', 'system_fingerprint': None, 'finish_reason': 'stop', 'logprobs': None} id='run-99368d03-c2ed-4dda-a32f-677c036ad676-0' usage_metadata={'input_tokens': 83, 'output_tokens': 32, 'total_tokens': 115}


# 新的 user_id --> 不记得了。
response = with_message_history.invoke(
    {"ability": "math", "input": "什么?"},
    config={"configurable": {"user_id": "123", "conversation_id": "2"}},
)
print(response)
#content='对不起，我没明白您的问题。你能更明确地表达你的数学问题吗？' response_metadata={'token_usage': {'completion_tokens': 29, 'prompt_tokens': 32, 'total_tokens': 61}, 'model_name': 'gpt-4-0613', 'system_fingerprint': None, 'finish_reason': 'stop', 'logprobs': None} id='run-48ff0adf-8f7d-48bc-a137-680c31d6e6ab-0' usage_metadata={'input_tokens': 32, 'output_tokens': 29, 'total_tokens': 61}
