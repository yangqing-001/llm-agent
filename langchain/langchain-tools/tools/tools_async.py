from langchain_core.tools import tool


@tool
async def amultiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b


# 让我们检查与该工具关联的一些属性。
print(amultiply.name)
print(amultiply.description)
print(amultiply.args)

