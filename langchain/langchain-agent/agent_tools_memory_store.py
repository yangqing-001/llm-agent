from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults

search = TavilySearchResults(max_results=1)

# pip install langchain
from langchain.tools.retriever import create_retriever_tool
from langchain_community.document_loaders import WebBaseLoader
# pip install faiss-cpu
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

loader = WebBaseLoader("https://zh.wikipedia.org/wiki/%E7%8C%AB")
docs = loader.load()
documents = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=200
).split_documents(docs)
vector = FAISS.from_documents(documents, OpenAIEmbeddings())
retriever = vector.as_retriever()

retriever_tool = create_retriever_tool(
    retriever,
    "wiki_search",
    "搜索维基百科",
)

model = ChatOpenAI(model="gpt-4")

tools = [search, retriever_tool]

from langchain import hub
# 获取要使用的提示 - 您可以修改这个！
prompt = hub.pull("hwchase17/openai-functions-agent")

from langchain.agents import create_tool_calling_agent
agent = create_tool_calling_agent(model, tools, prompt)

from langchain.agents import AgentExecutor
agent_executor = AgentExecutor(agent=agent, tools=tools)


from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

agent_with_chat_history = RunnableWithMessageHistory(
    agent_executor,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)

response = agent_with_chat_history.invoke(
    {"input": "Hi，我的名字是Jack"},
    config={"configurable": {"session_id": "123"}},
)

print(response)

response = agent_with_chat_history.invoke(
    {"input": "我叫什么名字?"},
    config={"configurable": {"session_id": "123"}},
)

print(response)

response = agent_with_chat_history.invoke(
    {"input": "我叫什么名字?"},
    config={"configurable": {"session_id": "456"}},
)

print(response)
