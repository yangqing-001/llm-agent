#导入工具装饰器库
from langchain_core.tools import tool


@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b


# 让我们检查与该工具关联的一些属性。
print(multiply.name)
print(multiply.description)
print(multiply.args)
