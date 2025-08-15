# pip install langchain
#导入Tavily检索工具的库
from langchain_community.tools.tavily_search import TavilySearchResults

search = TavilySearchResults(max_results=1)
print(search.invoke("今天上海天气怎么样"))