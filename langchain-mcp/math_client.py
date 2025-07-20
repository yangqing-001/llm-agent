import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
# from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="qwen-max",  # 指定千问模型
    temperature=0,
    api_key="sk-7b957493cc324362b63a95bcd09ef189",  # 确保环境变量正确
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"  # 兼容模式端点
)
# 初始化 Ollama 大模型客户端
# llm = ChatOllama(
#     model="llama3.2",  # 使用支持工具调用的模型
#     base_url="http://localhost:11434",  # Ollama 服务地址
#     temperature=0.7
# )

# 解析并输出结果
def print_optimized_result(agent_response):
    """
    解析代理响应并输出优化后的结果。
    :param agent_response: 代理返回的完整响应
    """
    messages = agent_response.get("messages", [])
    steps = []  # 用于记录计算步骤
    final_answer = None  # 最终答案

    for message in messages:
        if hasattr(message, "additional_kwargs") and "tool_calls" in message.additional_kwargs:
            # 提取工具调用信息
            tool_calls = message.additional_kwargs["tool_calls"]
            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]
                tool_args = tool_call["function"]["arguments"]
                steps.append(f"调用工具: {tool_name}({tool_args})")
        elif message.type == "tool":
            # 提取工具执行结果
            tool_name = message.name
            tool_result = message.content
            steps.append(f"{tool_name} 的结果是: {tool_result}")
        elif message.type == "ai":
            # 提取最终答案
            final_answer = message.content

    # 打印优化后的结果
    print("\n计算过程:")
    for step in steps:
        print(f"- {step}")
    if final_answer:
        print(f"\n最终答案: {final_answer}")

# 定义异步主函数
async def main():
    # MultiServerMCPClient 是用于连接多个 MCP 服务器的客户端。
    client = MultiServerMCPClient(
        {
            "math": {
                "command": "python",
                "args": ["./math_server.py"],
                "transport": "stdio",
            },
            "weather": {
                "url": "http://localhost:8000/sse",
                "transport": "sse",
            }
        }
    )

    try:
        # 获取工具
        tools = await client.get_tools()
        # 创建一个智能代理，思考 → 行动 → 观察 → 思考 → 行动 → ... → 最终答案
        agent = create_react_agent(llm, tools)

        # 循环接收用户输入
        while True:
            try:
                # 提示用户输入问题
                user_input = input("\n请输入您的问题（或输入 'exit' 退出）：")
                if user_input.lower() == "exit":
                    print("感谢使用！再见！")
                    break

                # 调用代理处理问题
                agent_response = await agent.ainvoke({"messages": user_input})

                # 调用抽取的方法处理输出结果
                print_optimized_result(agent_response)

            except Exception as e:
                print(f"发生错误：{e}")
                continue

    finally:
        # 清理资源
        if hasattr(client, 'close'):
            await client.close()

# 使用 asyncio 运行异步主函数
if __name__ == "__main__":
    asyncio.run(main())
