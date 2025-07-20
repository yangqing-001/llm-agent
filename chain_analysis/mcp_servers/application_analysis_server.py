"""
应用程序分析MCP服务器

提供智能应用分析功能，包括获取应用列表、分类和用户画像分析。

Author: FangGL
Date: 2024-12-19
"""
from langchain_openai import ChatOpenAI
from mcp.server.fastmcp import FastMCP
import logging
import subprocess
import json
import asyncio
from typing import Dict, List
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import SecretStr

# 配置日志记录器
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 创建FastMCP实例
mcp = FastMCP("ApplicationAnalysis")

# 初始化LLM
# llm = ChatOpenAI(
#     model="ep-2025*****5702-887jj",  # 火山引擎推理接入点
#     api_key=SecretStr("b6a98d76-33e6-*****b490f6ba59e3"),  # 火山引擎API密钥
#     base_url="https://ark.cn-beijing.volces.com/api/v3",  # 火山引擎API基础地址
#     temperature=0.3  # 降低温度值，减少随机性
# )
llm = ChatOpenAI(
    model="qwen-max",  # 指定千问模型
    temperature=0,
    api_key="sk-7b957493cc324362b63a95bcd09ef189",  # 确保环境变量正确
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"  # 兼容模式端点
)
# JSON解析器
json_parser = JsonOutputParser()



def get_applications_list(directory: str = "/Applications/") -> dict:
    """
    获取指定目录下的应用程序列表，可以直接获取该用户的应用列表以便分析用户职业，这是第一步
    如果用户问题不包含职业分析等内容不要调用该工具
    Args:
        directory: 要扫描的目录路径，默认为/Applications/

    Returns:
        dict: 包含应用列表的结果
    """
    logger.info(f"获取应用列表: {directory}")

    try:
        # 执行ls命令获取应用列表
        result = subprocess.run(
            f"ls {directory}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            apps_output = result.stdout
            apps_list = [app.strip() for app in apps_output.split('\n') if app.strip()]

            logger.info(f"发现 {len(apps_list)} 个应用程序")
            return {
                "success": True,
                "apps_count": len(apps_list),
                "apps_list": apps_list,
                "directory": directory
            }
        else:
            return {
                "success": False,
                "error": f"命令执行失败: {result.stderr}",
                "directory": directory
            }

    except Exception as e:
        logger.error(f"获取应用列表异常: {e}")
        return {
            "success": False,
            "error": str(e),
            "directory": directory
        }



def classify_applications(apps_list: List[str]) -> dict:
    """
    对应用程序进行智能分类，执行该工具前必须获取应用列表必须执行get_applications_list获取应用列表
    如果用户问题不包含职业分析等内容不要调用该工具
    Args:
        apps_list: 应用程序名称列表

    Returns:
        dict: 分类结果
    """
    logger.info(f"对 {len(apps_list)} 个应用进行分类")

    try:
        # 创建分类提示模板
        classification_prompt = ChatPromptTemplate.from_template("""
        你是一个专业的软件分类专家。请将以下应用程序按照功能类别进行分类。

        应用程序列表：
        {apps_list}

        请按以下类别进行分类，并输出JSON格式：
        - development: 开发编程类工具（IDE、编程语言、开发框架等）
        - office: 办公协作类工具（文档编辑、会议、邮件等）
        - design: 设计创作类工具（图形设计、视频编辑、绘图等）
        - network: 网络浏览类工具（浏览器、下载工具、网络服务等）
        - entertainment: 娱乐社交类工具（游戏、社交、视频娱乐等）
        - system: 系统维护类工具（清理工具、系统监控、压缩工具等）
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
        classification_chain = classification_prompt | llm | json_parser

        # 执行分类
        classification_result = classification_chain.invoke({
            "apps_list": "\n".join(apps_list)
        })

        # 统计各类别数量
        category_stats = {}
        total_classified = 0
        for category, apps in classification_result.items():
            count = len(apps) if apps else 0
            category_stats[category] = count
            total_classified += count

        logger.info("应用分类完成")
        return {
            "success": True,
            "total_apps": len(apps_list),
            "total_classified": total_classified,
            "classification": classification_result,
            "category_stats": category_stats
        }

    except Exception as e:
        logger.error(f"应用分类异常: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_apps": len(apps_list)
        }



def analyze_user_profile(classification: Dict) -> dict:
    """
    基于应用分类结果分析用户画像，执行该工具前必须先进行应用分类执行classify_applications函数
    如果用户问题不包含职业分析等内容不要调用该工具
    Args:
        classification: 应用分类结果字典

    Returns:
        dict: 用户画像分析结果
    """
    logger.info("开始用户画像分析")

    try:
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
            "detailed_profile": "详细的用户画像描述(200字以内)",
            "industry_recommendations": ["推荐行业1", "推荐行业2", "推荐行业3"]
        }}
        
        基于应用的专业度、数量、组合来判断。置信度要基于证据强度。只输出JSON，不要其他文字。
        """)

        # 创建分析链
        analysis_chain = analysis_prompt | llm | json_parser

        # 执行分析
        analysis_result = analysis_chain.invoke({
            "classification": json.dumps(classification, ensure_ascii=False, indent=2)
        })

        logger.info("用户画像分析完成")
        return {
            "success": True,
            "user_profile": analysis_result,
            "analysis_timestamp": str(asyncio.get_event_loop().time())
        }

    except Exception as e:
        logger.error(f"用户画像分析异常: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def run_complete_analysis(directory: str = "/Applications/") -> dict:
    """
    如果用户需要分析自己的职业可以调用该工具：获取应用 → 分类 → 用户画像分析
    如果用户问题不包含职业分析等内容不要调用该工具
    
    Args:
        directory: 要分析的应用目录，默认为/Applications/
        
    Returns:
        dict: 完整分析结果
    """
    logger.info(f"开始完整应用分析流程: {directory}")
    
    try:
        # 步骤1：获取应用列表
        apps_result = get_applications_list(directory)
        if not apps_result["success"]:
            return {
                "success": False,
                "step": "get_applications",
                "error": apps_result["error"]
            }
        
        apps_list = apps_result["apps_list"]
        logger.info(f"步骤1完成：发现 {len(apps_list)} 个应用")
        
        # 步骤2：应用分类
        classification_result = classify_applications(apps_list)
        if not classification_result["success"]:
            return {
                "success": False,
                "step": "classify_applications", 
                "error": classification_result["error"],
                "apps_result": apps_result
            }
        
        classification = classification_result["classification"]
        logger.info("步骤2完成：应用分类成功")
        
        # 步骤3：用户画像分析
        profile_result = analyze_user_profile(classification)
        if not profile_result["success"]:
            return {
                "success": False,
                "step": "analyze_user_profile",
                "error": profile_result["error"],
                "apps_result": apps_result,
                "classification_result": classification_result
            }
        
        logger.info("步骤3完成：用户画像分析成功")
        
        # 整合最终结果
        return {
            "success": True,
            "directory": directory,
            "total_steps": 3,
            "apps_summary": {
                "total_count": apps_result["apps_count"],
                "apps_list": apps_list
            },
            "classification_summary": {
                "category_stats": classification_result["category_stats"],
                "classification": classification
            },
            "user_profile": profile_result["user_profile"],
            "complete_analysis": True
        }
        
    except Exception as e:
        logger.error(f"完整分析流程异常: {e}")
        return {
            "success": False,
            "error": str(e),
            "directory": directory
        }


if __name__ == "__main__":
    logger.info("启动应用程序分析MCP服务器")
    logger.info("提供智能应用分析、分类和用户画像功能")
    logger.info("支持的工具: 应用列表获取、智能分类、画像分析、完整流程")
    mcp.run(transport="stdio") 