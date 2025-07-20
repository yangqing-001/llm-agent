import asyncio
import sys
import os
from dotenv import load_dotenv
from langchain.memory import ConversationBufferWindowMemory
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import SecretStr

# 加载环境变量
load_dotenv()

# 初始化 ChatOpenAI 大模型客户端
llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),  # 从环境变量获取模型名称
    api_key=SecretStr(os.getenv("OPENAI_API_KEY", "")),  # 从环境变量获取API密钥
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),  # 从环境变量获取基础URL
    temperature=float(os.getenv("TEMPERATURE", "0.7"))  # 从环境变量获取温度值
)


# 创建优化的提示词
def create_smart_prompt():
    """创建智能提示词，引导AI合理使用工具"""
    system_template = """你是一个专业的MySQL数据库管理助手，具备完整的MySQL数据库操作能力。

🔧 可用工具及使用场景：

📊 数据库和表管理：
- create_database: 创建新的MySQL数据库
- show_databases: 显示所有数据库
- create_table: 在指定数据库中创建新表
- show_tables: 显示指定数据库中的所有表

🔍 表结构查询（重要！）：
- describe_table: 查看表的详细结构（字段名、类型、约束、默认值等）
- show_table_indexes: 显示表的索引信息
- show_create_table: 显示创建表的完整SQL语句

📝 数据操作：
- insert_data: 向表中插入数据
- update_data: 更新表中的数据
- delete_data: 删除表中的数据
- query_data: 查询表中的数据

🎯 表设计分析（新功能！）：
- analyze_table_design: 全面分析表设计，提供专业评判和优化建议
- get_table_structure_info: 获取表的完整结构信息（字段、索引、状态等）
- check_table_performance_issues: 检查表的性能问题并提供优化建议

🎯 智能操作流程（必须遵循）：

1. 📋 数据操作前的准备工作：
   - 在进行任何数据插入、更新、删除操作之前，必须先使用 describe_table 查看表结构
   - 了解字段名称、数据类型、是否允许NULL、默认值等信息
   - 确保操作的数据符合表结构要求

2. 🔍 表结构分析：
   - 检查字段的数据类型（INT、VARCHAR、DATE等）
   - 注意字段长度限制（如VARCHAR(100)）
   - 识别主键、外键、唯一约束
   - 了解哪些字段不能为NULL
   - 查看是否有AUTO_INCREMENT字段

3. 📊 数据验证：
   - 确保插入的数据类型与字段类型匹配
   - 检查字符串长度不超过字段限制
   - 验证必填字段都有值
   - 对于AUTO_INCREMENT字段，通常不需要手动指定值

4. 🛡️ 安全操作：
   - 更新和删除操作必须有明确的WHERE条件
   - 避免无条件的UPDATE或DELETE操作
   - 在执行危险操作前，先用SELECT验证条件

💡 最佳实践示例：

用户说："向员工表插入一个新员工"
正确流程：
1. 先执行：describe_table("company", "employees")
2. 分析表结构，了解字段要求
3. 根据表结构构造正确的JSON数据
4. 执行插入操作

数据库连接信息：
🎯 工具使用原则：
1. 数据操作前必须先查看表结构 - 这是最重要的原则！
2. 对于一般性MySQL知识问答，直接回答，无需调用工具
3. 执行操作前，确保完全理解用户需求和表结构
4. 如果操作失败，分析错误原因并提供具体的修正建议
5. 始终提供清晰的操作步骤说明

🔍 表设计分析使用场景：
- 当用户询问表设计是否合理时，使用 analyze_table_design
- 当用户需要表的完整信息时，使用 get_table_structure_info
- 当用户关心表性能时，使用 check_table_performance_issues
- 表设计分析会检查命名规范、数据类型、索引设计等多个维度

请保持专业、友好的对话风格，帮助用户高效、安全地管理MySQL数据库。"""

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
        # 初始化MCP客户端 - MySQL数据库控制服务器和表设计分析服务器
        client = MultiServerMCPClient({  # type: ignore
            "mysql": {
                "command": "python3",
                "args": ["./mcp_servers/mysql_server.py"],
                "transport": "stdio",
            },
            "table_analyzer": {
                "command": "python3",
                "args": ["./mcp_servers/table_design_analyzer.py"],
                "transport": "stdio",
            }
        })

        tools = await client.get_tools()
        
        # 创建带有智能提示词的代理
        smart_prompt = create_smart_prompt()
        agent = create_react_agent(llm, tools, prompt=smart_prompt)

        # 使用窗口记忆 - 从环境变量获取窗口大小，无需transformers包
        memory_window_size = int(os.getenv("MEMORY_WINDOW_SIZE", "10"))
        memory = ConversationBufferWindowMemory(
            k=memory_window_size,    # 保留最近N轮对话
            return_messages=True     # 返回消息对象
        )

        print("✨ MySQL数据库管理助手已启动!")
        print("🗄️ 数据库连接: 127.0.0.1:3306 (root)")
        print("🔧 核心功能: 创建数据库 | 创建表 | 数据增删改查 | 查看数据库/表")
        print("🔍 表结构功能: 查看表结构 | 显示索引信息 | 查看建表语句")
        print("🎯 表设计分析: 设计评判 | 性能分析 | 优化建议 (新功能!)")
        print("🧠 AI会智能判断何时需要调用数据库工具")
        print("📋 重要提示: AI会在数据操作前自动查看表结构，确保操作安全")
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
            - 创建MySQL数据库或表
            - 插入、更新、删除数据库中的数据
            - 查询数据库中的数据
            - 查看数据库列表或表列表
            - 查看表结构、字段信息、索引信息
            - 显示建表语句
            - 其他需要实际操作MySQL数据库的任务
            
            不需要工具的情况(回答NO)：
            - 一般性对话、问候、闲聊
            - MySQL概念解释、知识问答
            - SQL语法咨询、建议交流
            - 数据库设计建议
            - 简单的理论性问题
            
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
