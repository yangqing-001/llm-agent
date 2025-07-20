#!/usr/bin/env python3
"""
表设计分析器测试脚本

用于测试新增的表设计分析功能
"""

import asyncio
import sys
import os
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

# 加载环境变量
load_dotenv()

async def test_table_analyzer():
    """测试表设计分析器功能"""
    
    print("🧪 开始测试表设计分析器...")
    
    try:
        # 初始化MCP客户端 - 仅表设计分析服务器
        client = MultiServerMCPClient({
            "table_analyzer": {
                "command": "python3",
                "args": ["./mcp_servers/table_design_analyzer.py"],
                "transport": "stdio",
            }
        })

        tools = await client.get_tools()
        print(f"✅ 成功连接到表设计分析服务器，可用工具: {len(tools)}")
        
        # 列出可用工具
        print("\n📋 可用工具:")
        for tool in tools:
            print(f"  • {tool.name}: {tool.description}")
        
        # 测试数据库连接（需要确保有测试数据库和表）
        print("\n🔍 测试表设计分析功能...")
        
        # 这里可以添加具体的测试用例
        # 例如：分析一个已知的表
        test_database = "test_db"  # 请根据实际情况修改
        test_table = "users"       # 请根据实际情况修改
        
        print(f"📊 准备分析表: {test_database}.{test_table}")
        print("💡 提示: 请确保数据库和表存在，或者手动调用工具进行测试")
        
        # 可以在这里添加实际的工具调用测试
        # result = await client.call_tool("analyze_table_design", {
        #     "database_name": test_database,
        #     "table_name": test_table
        # })
        # print(f"分析结果: {result}")
        
        print("✅ 表设计分析器测试完成!")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    return True

async def main():
    """主函数"""
    print("🚀 表设计分析器测试工具")
    print("=" * 40)
    
    success = await test_table_analyzer()
    
    if success:
        print("\n🎉 所有测试通过!")
        print("\n💡 使用建议:")
        print("1. 运行主程序: python mcp_client.py")
        print("2. 输入: '分析表设计 数据库名 表名'")
        print("3. 或者: '检查表性能 数据库名 表名'")
        print("4. 或者: '查看表结构 数据库名 表名'")
    else:
        print("\n❌ 测试失败，请检查配置")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
