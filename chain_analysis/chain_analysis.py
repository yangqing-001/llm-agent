import asyncio
import json
from typing import Dict
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableSequence
# from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient

class ApplicationAnalysisChain:
    """
    应用程序分析链式调用器
    
    使用LangChain的链式调用机制实现三步骤分析流程
    
    Author: FangGL
    Date: 2024-12-19
    """
    
    def __init__(self):
        # 初始化LLM
        self.llm = ChatOllama(
            model="llama3.2",
            base_url="http://localhost:11434",
            temperature=0.3  # 降低温度，提高分析准确性
        )
        
        # MCP客户端
        self.mcp_client = None
        self.tools = None
        
        # 创建解析器
        self.json_parser = JsonOutputParser()
        self.str_parser = StrOutputParser()
    
    async def setup_mcp(self):
        """初始化MCP客户端和工具"""
        self.mcp_client = MultiServerMCPClient({
            "terminal": {
                "command": "python3",
                "args": ["./mcp_servers/terminal_server.py"],
                "transport": "stdio",
            }
        })
        
        self.tools = await self.mcp_client.get_tools()
        print("✅ MCP终端服务已连接")
    
    async def step1_get_applications(self, input_data: Dict) -> Dict:
        """
        步骤1：获取应用程序列表
        """
        print("🔍 步骤1：获取/Applications/目录下的应用程序...")
        
        # 调用终端MCP服务执行命令
        for tool in self.tools:
            if tool.name == "execute_command":
                result = await tool.ainvoke({
                    "command": "ls /Applications/",
                    "timeout": 30
                })
                
                # 解析结果 - 处理JSON字符串
                if isinstance(result, str):
                    # MCP返回的是JSON字符串，需要解析
                    try:
                        result = json.loads(result)
                    except json.JSONDecodeError as e:
                        raise Exception(f"JSON解析失败: {e}")
                
                if isinstance(result, dict) and "stdout" in result:
                    apps_output = result.get("stdout", "")
                    if apps_output.strip():  # 确保stdout不为空
                        apps_list = [app.strip() for app in apps_output.split('\n') if app.strip()]
                        
                        print(f"📱 发现 {len(apps_list)} 个应用程序")
                        return {
                            "step": 1,
                            "apps_list": apps_list,
                            "raw_output": apps_output
                        }
                    else:
                        raise Exception(f"stdout为空字符串")
                else:
                    raise Exception(f"结果格式错误: {result}")
        
        raise Exception("未找到终端执行工具")
    
    def step2_classify_applications(self, input_data: Dict) -> Dict:
        """
        步骤2：对应用程序进行分类
        """
        print("🏷️ 步骤2：对应用程序进行智能分类...")
        
        # 创建分类提示模板
        classification_prompt = ChatPromptTemplate.from_template("""
        你是一个专业的软件分类专家。请将以下应用程序按照功能类别进行分类。

        应用程序列表：
        {apps_list}

        请按以下类别进行分类，并输出JSON格式：
        - development: 开发编程类工具
        - office: 办公协作类工具  
        - design: 设计创作类工具
        - network: 网络浏览类工具
        - entertainment: 娱乐社交类工具
        - system: 系统维护类工具
        - other: 其他类型工具

        输出格式：
        {{
            "development": ["应用1", "应用2"],
            "office": ["应用3", "应用4"],
            "design": ["应用5"],
            "network": ["应用6", "应用7"],
            "entertainment": ["应用8"],
            "system": ["应用9", "应用10"],
            "other": ["应用11"]
        }}
        
        只输出JSON，不要其他文字说明。
        """)
        
        # 创建分类链
        classification_chain = classification_prompt | self.llm | self.json_parser
        
        # 执行分类
        apps_list = input_data["apps_list"]
        classification_result = classification_chain.invoke({
            "apps_list": "\n".join(apps_list)
        })
        
        print("✅ 应用分类完成")
        return {
            "step": 2,
            "apps_list": apps_list,
            "classification": classification_result
        }
    
    def step3_analyze_user_profile(self, input_data: Dict) -> Dict:
        """
        步骤3：分析用户身份和特征
        """
        print("👤 步骤3：基于应用组合分析用户身份...")
        
        # 创建用户分析提示模板
        analysis_prompt = ChatPromptTemplate.from_template("""
        你是一个专业的用户画像分析师。基于用户安装的应用程序分类，分析用户的职业身份和特征。

        应用程序分类结果：
        {classification}

        请进行深度分析，输出JSON格式：
        {{
            "primary_identity": "主要身份(如：程序员、设计师、文字工作者等)",
            "confidence_score": 0.95,
            "secondary_identities": ["次要身份1", "次要身份2"],
            "technical_level": "技术水平(初级/中级/高级/专家)",
            "work_style": "工作风格描述",
            "key_characteristics": ["特征1", "特征2", "特征3"],
            "evidence_analysis": {{
                "development_tools": "开发工具分析",
                "workflow_efficiency": "工作流效率分析", 
                "collaboration_pattern": "协作模式分析"
            }},
            "detailed_profile": "详细的用户画像描述(200字以内)"
        }}
        
        基于应用的专业度、数量、组合来判断。只输出JSON，不要其他文字。
        """)
        
        # 创建分析链
        analysis_chain = analysis_prompt | self.llm | self.json_parser
        
        # 执行分析
        classification = input_data["classification"]
        analysis_result = analysis_chain.invoke({
            "classification": json.dumps(classification, ensure_ascii=False, indent=2)
        })
        
        print("✅ 用户身份分析完成")
        return {
            "step": 3,
            "classification": classification,
            "user_profile": analysis_result
        }
    
    async def run_complete_analysis(self) -> Dict:
        """
        运行完整的三步骤链式分析
        """
        print("🚀 开始执行链式分析流程...\n")
        
        # 设置MCP连接
        await self.setup_mcp()
        
        # 创建完整的链式调用序列
        analysis_chain = RunnableSequence(
            RunnableLambda(self.step1_get_applications),      # 步骤1：获取应用列表
            RunnableLambda(self.step2_classify_applications),  # 步骤2：应用分类
            RunnableLambda(self.step3_analyze_user_profile)    # 步骤3：用户分析
        )
        
        try:
            # 执行完整链条
            final_result = await analysis_chain.ainvoke({"start": True})
            
            print("\n" + "="*60)
            print("🎯 链式分析完成！最终结果：")
            print("="*60)
            
            return final_result
            
        except Exception as e:
            print(f"❌ 链式分析过程中出错: {e}")
            return {"error": str(e)}
    
    def display_results(self, result: Dict):
        """格式化显示分析结果"""
        if "error" in result:
            print(f"❌ 分析失败: {result['error']}")
            return
        
        classification = result.get("classification", {})
        user_profile = result.get("user_profile", {})
        
        print("\n📊 应用分类结果:")
        for category, apps in classification.items():
            if apps:
                print(f"  {category}: {len(apps)}个应用")
                for app in apps[:3]:  # 显示前3个
                    print(f"    • {app}")
                if len(apps) > 3:
                    print(f"    ... 还有{len(apps)-3}个")
        
        print(f"\n👤 用户身份分析:")
        print(f"  主要身份: {user_profile.get('primary_identity', 'N/A')}")
        print(f"  置信度: {user_profile.get('confidence_score', 0):.1%}")
        print(f"  技术水平: {user_profile.get('technical_level', 'N/A')}")
        print(f"  工作风格: {user_profile.get('work_style', 'N/A')}")
        
        print(f"\n🔍 关键特征:")
        for char in user_profile.get('key_characteristics', []):
            print(f"  • {char}")
        
        print(f"\n📝 详细画像:")
        print(f"  {user_profile.get('detailed_profile', 'N/A')}")


async def main():
    """
    主函数：演示链式调用分析
    
    Author: FangGL  
    Date: 2024-12-19
    """
    analyzer = ApplicationAnalysisChain()
    
    # 执行完整的链式分析
    result = await analyzer.run_complete_analysis()
    
    # 显示结果
    analyzer.display_results(result)


if __name__ == "__main__":
    print("🔗 LangChain链式调用应用分析器")
    print("📋 将执行三步骤分析：获取应用 → 分类 → 用户画像")
    print("-" * 60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 分析被用户中断")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}") 