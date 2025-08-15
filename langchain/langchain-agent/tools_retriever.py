# pip install langchain
from langchain.tools.retriever import create_retriever_tool
from langchain_community.document_loaders import WebBaseLoader
#pip install faiss-cpu
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

loader = WebBaseLoader("https://zh.wikipedia.org/wiki/%E7%8C%AB")
docs = loader.load()
documents = RecursiveCharacterTextSplitter(
    # chunk_size 参数在 RecursiveCharacterTextSplitter 中用于指定每个文档块的最大字符数。它的作用主要有以下几个方面：
    # chunk_overlap 参数用于指定每个文档块之间的重叠字符数。这意味着，当文档被拆分成较小的块时，每个块的末尾部分会与下一个块的开头部分有一定数量的重叠字符。
    # 第一个块包含字符 1 到 1000。第二个块包含字符 801 到 1800。第三个块包含字符 1601 到 2600。
    chunk_size=1000, chunk_overlap=200
).split_documents(docs)
#将网页文本转换为向量并存储
vector = FAISS.from_documents(documents, OpenAIEmbeddings())
retriever = vector.as_retriever()

print(retriever.invoke("猫的特征")[0])

retriever_tool = create_retriever_tool(
    retriever,
    "wiki_search",
    "搜索维基百科",
)