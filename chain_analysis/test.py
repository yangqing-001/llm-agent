import asyncio
import sys
from langchain.memory import ConversationBufferWindowMemory
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import SecretStr

# 初始化 ChatOpenAI 大模型客户端
# llm = ChatOpenAI(
#     model="ep-20*********02-887jj",  # 火山引擎推理接入点
#     api_key=SecretStr("b6a98d76-**********-b490f6ba59e3"),  # 火山引擎API密钥
#     base_url="https://ark.cn-beijing.volces.com/api/v3",  # 火山引擎API基础地址
#     temperature=0.3  # 降低温度值，减少随机性
# )
llm = ChatOpenAI(
    model="qwen-max",  # 指定千问模型
    temperature=0,
    api_key="sk-7b957493cc324362b63a95bcd09ef189",  # 确保环境变量正确
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"  # 兼容模式端点
)


# 初始化LLM
# llm = ChatOllama(
#     model="qwen3:14b",
#     base_url="http://localhost:11434",
#     temperature=0.3
# )

# 创建优化的提示词
def create_smart_prompt():
    """创建智能提示词，引导AI合理使用工具"""
    system_template = """你是一个专业的智能助手，具备多种工具能力，能够帮助用户完成各类任务。

可用工具及使用场景：
- terminal: 执行系统命令、文件操作、程序运行
- app_analysis: 职业分析、应用程序分析、用户画像  
- browser: 网页控制、自动化操作、信息采集
- weather: 天气查询、气象信息获取

工具使用原则：
1. 只有用户明确需要执行具体操作时才使用工具
2. 对于一般性对话、概念解释、建议咨询等，直接回答
3. 优先选择最合适的工具来完成任务
4. 如果不确定是否需要工具，优先选择直接回答

请保持自然、友好的对话风格，准确理解用户真实意图，明智地选择是否使用工具。"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_template),
        MessagesPlaceholder(variable_name="messages")
    ])

    return prompt


# 简化的结果输出函数
def print_result(agent_response):
    """输出代理响应结果"""
    messages = agent_response.get("messages", [])

    # 提取最终答案
    for message in reversed(messages):
        if message.type == "ai" and message.content:
            print(f"\n🎯 回答: {message.content}")
            break


# 主函数
async def main():
    """
    主函数 - 集成LangChain记忆功能的对话客户端

    Author: FangGL
    Date: 2024-12-19
    """
    client = None

    # 初始化MCP客户端 - 完整服务器配置
    client = MultiServerMCPClient({  # type: ignore
        "terminal": {
            "command": "python",
            "args": ["D://OrdinaryYQ/code/python/llm-agent/chain_analysis/mcp_servers/terminal_server.py"],
            "transport": "stdio",
        },
        "app_analysis": {
            "command": "python",
            "args": ["D://OrdinaryYQ/code/python/llm-agent/chain_analysis/mcp_servers/application_analysis_server.py"],
            "transport": "stdio",
        },
        "browser": {
            "command": "python",
            "args": ["D://OrdinaryYQ/code/python/llm-agent/chain_analysis/mcp_servers/browser_control_server.py"],
            "transport": "stdio",
        },
        "weather": {
            "command": "python",
            "args": ["D://OrdinaryYQ/code/python/llm-agent/chain_analysis/mcp_servers/weather_server.py"],
            "transport": "stdio",
        }
    })

    tools = await client.get_tools()
    print(tools)



if __name__ == "__main__":
    asyncio.run(main())
