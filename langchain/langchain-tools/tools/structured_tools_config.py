from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
import asyncio

class CalculatorInput(BaseModel):
    a: int = Field(description="first number")
    b: int = Field(description="second number")

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

# 创建一个异步包装器函数
async def async_addition(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a + b
async def main():
    calculator = StructuredTool.from_function(
        func=multiply,
        name="Calculator",
        description="multiply numbers",
        args_schema=CalculatorInput,
        return_direct=True,
        #coroutine= async_addition
        # coroutine= ... <- 如果需要，也可以指定异步方法
    )
    print(calculator.invoke({"a": 2, "b": 3}))
    #print(await calculator.ainvoke({"a": 2, "b": 5}))
    print(calculator.name)
    print(calculator.description)
    print(calculator.args)


# 运行异步主函数
asyncio.run(main())
