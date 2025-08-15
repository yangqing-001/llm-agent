from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from pydantic import BaseModel, Field

api_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=100)
class WikiInputs(BaseModel):
    """维基百科工具的输入。"""
    query: str = Field(
        description="query to look up in Wikipedia, should be 3 or less words"
    )
tool = WikipediaQueryRun(
    name="wiki-tool",
    description="look up things in wikipedia",
    args_schema=WikiInputs,
    api_wrapper=api_wrapper,
    #如果 return_direct 设置为 True，工具会直接返回查询结果，例如一个字符串或一个简单的数据结构。
    #如果 return_direct 设置为 False，工具可能会返回一个更复杂的响应对象，其中包含更多的元数据或结构化信息。
    return_direct=True,
)

print(tool.run("langchain"))
print(f"Name: {tool.name}")
print(f"Description: {tool.description}")
print(f"args schema: {tool.args}")
print(f"returns directly?: {tool.return_direct}")
