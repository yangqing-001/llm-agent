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

from langchain_core.messages import HumanMessage

tools = [search, retriever_tool]
model_with_tools = model.bind_tools(tools)


response = model_with_tools.invoke([HumanMessage(content="你好")])
print(f"ContentString: {response.content}")
print(f"ToolCalls: {response.tool_calls}")


print("------------------------------------------------------------------------------")

response = model_with_tools.invoke([HumanMessage(content="今天上海天气怎么样")])
print(f"ContentString: {response.content}")
print(f"ToolCalls: {response.tool_calls}")