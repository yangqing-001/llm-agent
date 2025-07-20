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
    
    try:
        # 初始化MCP客户端 - 完整服务器配置  
        client = MultiServerMCPClient({  # type: ignore
            "terminal": {
                "command": "python",
                "args": ["./mcp_servers/terminal_server.py"],
                "transport": "stdio",
            },
            "app_analysis": {
                "command": "python",
                "args": ["./mcp_servers/application_analysis_server.py"],
                "transport": "stdio",
            },
            "browser": {
                "command": "python",
                "args": ["./mcp_servers/browser_control_server.py"],
                "transport": "stdio",
            },
            "weather": {
                "command": "python",
                "args": ["./mcp_servers/weather_server.py"],
                "transport": "stdio",
            }
        })

        tools = await client.get_tools()
        
        # 创建带有智能提示词的代理
        smart_prompt = create_smart_prompt()
        agent = create_react_agent(llm, tools, prompt=smart_prompt)

        # 使用窗口记忆 - 保留最近10轮对话，无需transformers包
        memory = ConversationBufferWindowMemory(
            k=10,                    # 保留最近10轮对话  
            return_messages=True     # 返回消息对象
        )

        print("✨ 全功能智能助手已启动!")
        print("🔧 完整工具: 系统命令 | 职业分析 | 浏览器控制 | 天气查询")
        print("🧠 AI会智能判断何时需要调用工具")
        print("💬 支持流式对话，体验更自然")
        print("输入 'exit' 退出\n")

        # 对话循环
        while True:
            user_input = input("💬 问题: ").strip()
            
            if user_input.lower() == "exit":
                print("👋 再见!")
                break
            
            if not user_input:
                continue
            
            # 获取历史消息并添加当前用户输入
            messages = memory.chat_memory.messages.copy()
            messages.append(HumanMessage(content=user_input))
            
            # 先用LLM判断是否需要工具
            print("🤔 分析问题中...")
            
            # 创建判断提示
            judge_prompt = f"""
            用户问题: {user_input}
            
            请判断这个问题是否需要调用工具来完成任务。
            
            需要调用工具的情况(回答YES)：
            - 执行系统命令、文件操作、程序运行
            - 职业分析、应用程序分析、了解职业匹配度
            - 网页控制、信息采集、打开浏览器
            - 天气查询、气象信息、天气预报
            - 其他需要实际执行操作的任务
            
            不需要工具的情况(回答NO)：
            - 一般性对话、问候、闲聊
            - 概念解释、知识问答
            - 建议咨询、意见交流
            - 创意写作、故事创作
            - 简单数学计算
            
            只回答YES或NO，不要其他内容。
            """
            
            judge_response = await llm.ainvoke([HumanMessage(content=judge_prompt)])
            need_tools = "YES" in str(judge_response.content).upper()
            
            if need_tools:
                print("🔧 检测到需要工具调用，启动增强模式...")
                ai_response = ""
                tool_used = False
                
                # 使用agent处理工具调用
                async for chunk in agent.astream({"messages": messages}):
                    for node_name, node_output in chunk.items():
                        if node_name == "agent":
                            messages_in_chunk = node_output.get("messages", [])
                            for msg in messages_in_chunk:
                                if msg.type == "ai":
                                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                                        tool_used = True
                                        for tool_call in msg.tool_calls:
                                            print(f"🔧 调用工具: {tool_call['name']}")
                                            print(f"📝 参数: {tool_call['args']}")
                                    elif msg.content:
                                        ai_response = msg.content
                        
                        elif node_name == "tools":
                            messages_in_chunk = node_output.get("messages", [])
                            for msg in messages_in_chunk:
                                if msg.type == "tool":
                                    print(f"✅ 工具 '{msg.name}' 执行完成")
                                    try:
                                        import json
                                        result = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                                        if isinstance(result, dict):
                                            if result.get("success"):
                                                stdout = result.get("stdout", "").strip()
                                                if stdout:
                                                    print(f"📄 命令输出:\n{stdout}")
                                            else:
                                                stderr = result.get("stderr", "")
                                                print(f"❌ 错误: {stderr}")
                                    except:
                                        print(f"📄 原始结果: {msg.content}")
                
                if ai_response:
                    print(f"\n🎯 最终回答: {ai_response}")
                    
            else:
                print("💭 使用流式回答模式...")
                print("\n🎯 AI回答: ", end="", flush=True)
                
                # 直接使用LLM流式生成
                ai_response = ""
                async for chunk in llm.astream(messages):
                    if chunk.content:
                        content_str = str(chunk.content)
                        print(content_str, end="", flush=True)
                        ai_response += content_str
                
                print()  # 换行
            
            # 保存对话到记忆
            if ai_response:
                memory.save_context(
                    {"input": user_input},
                    {"output": str(ai_response)}
                )
                print("✓ 对话已保存到记忆")
            else:
                print("⚠️ 未获取到AI回复")

    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 程序已退出")
    except Exception as e:
        print(f"❌ 程序异常退出: {e}")
