"""
数据库表设计分析MCP服务器

提供专业的数据库表设计评判功能，包括：
- 表结构分析
- 命名规范检查
- 性能优化建议
- 索引设计评估
- 数据类型合理性分析
"""

from mcp.server.fastmcp import FastMCP
import logging
import pymysql
import os
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志记录器
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 创建FastMCP实例
mcp = FastMCP("Table Design Analyzer")

# MySQL连接配置 - 从环境变量获取
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', '127.0.0.1'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', '123456'),
    'charset': 'utf8mb4',
    'autocommit': True
}

def get_mysql_connection(database: Optional[str] = None) -> pymysql.Connection:
    """获取MySQL数据库连接"""
    config = MYSQL_CONFIG.copy()
    if database:
        config['database'] = database
    
    try:
        connection = pymysql.connect(**config)
        logger.info(f"成功连接到MySQL数据库: {config['host']}:{config['port']}")
        return connection
    except Exception as e:
        logger.error(f"MySQL连接失败: {e}")
        raise

def get_table_detailed_info(database_name: str, table_name: str) -> Dict[str, Any]:
    """获取表的详细信息，包括字段、索引、约束等"""
    try:
        connection = get_mysql_connection(database_name)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 获取表结构信息
        cursor.execute(f"DESCRIBE `{table_name}`")
        columns = cursor.fetchall()
        
        # 获取索引信息
        cursor.execute(f"SHOW INDEX FROM `{table_name}`")
        indexes = cursor.fetchall()
        
        # 获取表状态信息
        cursor.execute(f"SHOW TABLE STATUS LIKE '{table_name}'")
        table_status = cursor.fetchone()
        
        # 获取建表语句
        cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
        create_table = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        return {
            'columns': columns,
            'indexes': indexes,
            'table_status': table_status,
            'create_table_sql': create_table['Create Table'] if create_table else None
        }
        
    except Exception as e:
        logger.error(f"获取表详细信息失败: {e}")
        raise

def analyze_naming_conventions(table_name: str, columns: List[Dict]) -> List[str]:
    """分析命名规范"""
    issues = []
    
    # 检查表名命名规范
    if not table_name.islower():
        issues.append("❌ 表名建议使用小写字母")
    
    if ' ' in table_name:
        issues.append("❌ 表名不应包含空格")
    
    if not table_name.replace('_', '').isalnum():
        issues.append("❌ 表名应只包含字母、数字和下划线")
    
    # 检查字段命名规范
    for col in columns:
        field_name = col['Field']
        
        if not field_name.islower():
            issues.append(f"❌ 字段 '{field_name}' 建议使用小写字母")
        
        if ' ' in field_name:
            issues.append(f"❌ 字段 '{field_name}' 不应包含空格")
        
        # 检查保留字
        mysql_reserved_words = ['order', 'group', 'select', 'from', 'where', 'insert', 'update', 'delete']
        if field_name.lower() in mysql_reserved_words:
            issues.append(f"⚠️ 字段 '{field_name}' 是MySQL保留字，建议使用反引号或重命名")
    
    return issues

def analyze_data_types(columns: List[Dict]) -> List[str]:
    """分析数据类型选择的合理性"""
    suggestions = []
    
    for col in columns:
        field_name = col['Field']
        data_type = col['Type'].lower()
        
        # 检查TEXT类型使用
        if 'text' in data_type and col['Key'] != '':
            suggestions.append(f"⚠️ 字段 '{field_name}' 使用TEXT类型且有索引，可能影响性能")
        
        # 检查VARCHAR长度
        if 'varchar' in data_type:
            # 提取长度
            import re
            length_match = re.search(r'varchar\((\d+)\)', data_type)
            if length_match:
                length = int(length_match.group(1))
                if length > 255:
                    suggestions.append(f"💡 字段 '{field_name}' VARCHAR长度为{length}，考虑是否需要使用TEXT类型")
                elif length < 10 and 'id' not in field_name.lower():
                    suggestions.append(f"💡 字段 '{field_name}' VARCHAR长度较短({length})，考虑是否合适")
        
        # 检查INT类型
        if data_type.startswith('int') and 'id' in field_name.lower():
            if 'auto_increment' not in col['Extra'].lower():
                suggestions.append(f"💡 字段 '{field_name}' 看起来是ID字段，考虑添加AUTO_INCREMENT")
        
        # 检查时间字段
        if any(time_word in field_name.lower() for time_word in ['time', 'date', 'created', 'updated']):
            if not any(time_type in data_type for time_type in ['datetime', 'timestamp', 'date', 'time']):
                suggestions.append(f"💡 字段 '{field_name}' 看起来是时间字段，建议使用DATETIME或TIMESTAMP类型")
    
    return suggestions

def analyze_indexes(indexes: List[Dict], columns: List[Dict]) -> List[str]:
    """分析索引设计"""
    suggestions = []
    
    # 统计索引信息
    index_info = {}
    for idx in indexes:
        key_name = idx['Key_name']
        if key_name not in index_info:
            index_info[key_name] = {
                'columns': [],
                'unique': idx['Non_unique'] == 0,
                'type': idx['Index_type']
            }
        index_info[key_name]['columns'].append(idx['Column_name'])
    
    # 检查主键
    if 'PRIMARY' not in index_info:
        suggestions.append("❌ 表缺少主键，强烈建议添加主键")
    
    # 检查过多索引
    non_primary_indexes = [k for k in index_info.keys() if k != 'PRIMARY']
    if len(non_primary_indexes) > 5:
        suggestions.append(f"⚠️ 表有{len(non_primary_indexes)}个非主键索引，过多索引可能影响写入性能")
    
    # 检查重复索引
    column_sets = []
    for idx_name, idx_info in index_info.items():
        if idx_name != 'PRIMARY':
            col_set = tuple(sorted(idx_info['columns']))
            if col_set in column_sets:
                suggestions.append(f"⚠️ 可能存在重复索引，请检查索引 '{idx_name}'")
            column_sets.append(col_set)
    
    # 检查外键字段是否有索引
    for col in columns:
        field_name = col['Field']
        if field_name.endswith('_id') and field_name != 'id':
            # 检查是否有索引
            has_index = any(field_name in idx_info['columns'] for idx_info in index_info.values())
            if not has_index:
                suggestions.append(f"💡 外键字段 '{field_name}' 建议添加索引以提高查询性能")
    
    return suggestions

@mcp.tool()
def analyze_table_design(database_name: str, table_name: str) -> str:
    """
    分析数据库表设计，提供专业的评判和优化建议，可以分析用户传入的表结构设计如何
    
    Args:
        database_name: 数据库名称
        table_name: 表名称
        
    Returns:
        str: 详细的表设计分析报告
    """
    try:
        # 获取表的详细信息
        table_info = get_table_detailed_info(database_name, table_name)
        
        columns = table_info['columns']
        indexes = table_info['indexes']
        table_status = table_info['table_status']
        
        if not columns:
            return f"❌ 表 {table_name} 不存在或无法访问"
        
        # 开始分析
        analysis_result = []
        analysis_result.append(f"🔍 表设计分析报告: {database_name}.{table_name}")
        analysis_result.append("=" * 60)
        
        # 基本信息
        analysis_result.append(f"\n📊 基本信息:")
        analysis_result.append(f"  • 字段数量: {len(columns)}")
        analysis_result.append(f"  • 索引数量: {len(set(idx['Key_name'] for idx in indexes))}")
        if table_status:
            analysis_result.append(f"  • 存储引擎: {table_status.get('Engine', 'Unknown')}")
            analysis_result.append(f"  • 字符集: {table_status.get('Collation', 'Unknown')}")
        
        # 命名规范分析
        naming_issues = analyze_naming_conventions(table_name, columns)
        analysis_result.append(f"\n📝 命名规范检查:")
        if naming_issues:
            for issue in naming_issues:
                analysis_result.append(f"  {issue}")
        else:
            analysis_result.append("  ✅ 命名规范良好")
        
        # 数据类型分析
        datatype_suggestions = analyze_data_types(columns)
        analysis_result.append(f"\n🔧 数据类型分析:")
        if datatype_suggestions:
            for suggestion in datatype_suggestions:
                analysis_result.append(f"  {suggestion}")
        else:
            analysis_result.append("  ✅ 数据类型选择合理")
        
        # 索引设计分析
        index_suggestions = analyze_indexes(indexes, columns)
        analysis_result.append(f"\n🚀 索引设计分析:")
        if index_suggestions:
            for suggestion in index_suggestions:
                analysis_result.append(f"  {suggestion}")
        else:
            analysis_result.append("  ✅ 索引设计良好")
        
        # 总体评分和建议
        total_issues = len(naming_issues) + len(datatype_suggestions) + len(index_suggestions)
        analysis_result.append(f"\n📈 总体评估:")
        
        if total_issues == 0:
            analysis_result.append("  🌟 优秀! 表设计非常规范，没有发现明显问题")
        elif total_issues <= 3:
            analysis_result.append("  👍 良好! 表设计基本合理，有少量优化空间")
        elif total_issues <= 6:
            analysis_result.append("  ⚠️ 一般! 表设计存在一些问题，建议优化")
        else:
            analysis_result.append("  ❌ 需要改进! 表设计存在较多问题，强烈建议重构")
        
        analysis_result.append(f"  • 发现问题/建议数量: {total_issues}")
        
        logger.info(f"成功分析表设计: {database_name}.{table_name}")
        return "\n".join(analysis_result)
        
    except Exception as e:
        logger.error(f"表设计分析失败: {e}")
        return f"❌ 表设计分析失败: {str(e)}"

@mcp.tool()
def get_table_structure_info(database_name: str, table_name: str) -> str:
    """
    获取表的详细结构信息，包括字段、索引、约束等

    Args:
        database_name: 数据库名称
        table_name: 表名称

    Returns:
        str: 表结构的详细信息
    """
    try:
        table_info = get_table_detailed_info(database_name, table_name)

        columns = table_info['columns']
        indexes = table_info['indexes']
        table_status = table_info['table_status']
        create_sql = table_info['create_table_sql']

        if not columns:
            return f"❌ 表 {table_name} 不存在或无法访问"

        result = []
        result.append(f"📋 表结构信息: {database_name}.{table_name}")
        result.append("=" * 50)

        # 字段信息
        result.append(f"\n🔧 字段信息 ({len(columns)} 个字段):")
        for col in columns:
            null_info = "NULL" if col['Null'] == 'YES' else "NOT NULL"
            key_info = f" [{col['Key']}]" if col['Key'] else ""
            default_info = f" DEFAULT: {col['Default']}" if col['Default'] is not None else ""
            extra_info = f" {col['Extra']}" if col['Extra'] else ""

            result.append(f"  • {col['Field']}: {col['Type']} {null_info}{key_info}{default_info}{extra_info}")

        # 索引信息
        index_info = {}
        for idx in indexes:
            key_name = idx['Key_name']
            if key_name not in index_info:
                index_info[key_name] = {
                    'columns': [],
                    'unique': idx['Non_unique'] == 0,
                    'type': idx['Index_type']
                }
            index_info[key_name]['columns'].append(idx['Column_name'])

        result.append(f"\n🚀 索引信息 ({len(index_info)} 个索引):")
        for idx_name, idx_details in index_info.items():
            unique_info = "UNIQUE" if idx_details['unique'] else "NON-UNIQUE"
            columns_str = ", ".join(idx_details['columns'])
            result.append(f"  • {idx_name}: ({columns_str}) - {unique_info} {idx_details['type']}")

        # 表状态信息
        if table_status:
            result.append(f"\n📊 表状态信息:")
            result.append(f"  • 存储引擎: {table_status.get('Engine', 'Unknown')}")
            result.append(f"  • 字符集: {table_status.get('Collation', 'Unknown')}")
            result.append(f"  • 行数: {table_status.get('Rows', 'Unknown')}")
            result.append(f"  • 数据长度: {table_status.get('Data_length', 'Unknown')} bytes")
            result.append(f"  • 索引长度: {table_status.get('Index_length', 'Unknown')} bytes")

        # 建表语句
        if create_sql:
            result.append(f"\n📝 建表语句:")
            result.append(f"```sql\n{create_sql}\n```")

        logger.info(f"成功获取表结构信息: {database_name}.{table_name}")
        return "\n".join(result)

    except Exception as e:
        logger.error(f"获取表结构信息失败: {e}")
        return f"❌ 获取表结构信息失败: {str(e)}"

@mcp.tool()
def check_table_performance_issues(database_name: str, table_name: str) -> str:
    """
    检查表的性能问题并提供优化建议

    Args:
        database_name: 数据库名称
        table_name: 表名称

    Returns:
        str: 性能问题分析和优化建议
    """
    try:
        table_info = get_table_detailed_info(database_name, table_name)

        columns = table_info['columns']
        indexes = table_info['indexes']
        table_status = table_info['table_status']

        if not columns:
            return f"❌ 表 {table_name} 不存在或无法访问"

        performance_issues = []
        performance_issues.append(f"⚡ 性能分析报告: {database_name}.{table_name}")
        performance_issues.append("=" * 50)

        issues_found = []

        # 检查主键
        has_primary_key = any(idx['Key_name'] == 'PRIMARY' for idx in indexes)
        if not has_primary_key:
            issues_found.append("❌ 缺少主键 - 这会严重影响复制和性能")

        # 检查过长的VARCHAR字段
        for col in columns:
            if 'varchar' in col['Type'].lower():
                import re
                length_match = re.search(r'varchar\((\d+)\)', col['Type'].lower())
                if length_match and int(length_match.group(1)) > 500:
                    issues_found.append(f"⚠️ 字段 '{col['Field']}' VARCHAR长度过长，可能影响内存使用")

        # 检查TEXT/BLOB字段的索引
        for col in columns:
            if any(t in col['Type'].lower() for t in ['text', 'blob']):
                # 检查是否有索引
                has_index = any(col['Field'] in idx['Column_name'] for idx in indexes)
                if has_index:
                    issues_found.append(f"⚠️ TEXT/BLOB字段 '{col['Field']}' 有索引，可能影响性能")

        # 检查索引数量
        unique_indexes = set(idx['Key_name'] for idx in indexes)
        if len(unique_indexes) > 6:
            issues_found.append(f"⚠️ 索引过多 ({len(unique_indexes)}个)，可能影响写入性能")

        # 检查表大小
        if table_status:
            data_length = table_status.get('Data_length', 0)
            index_length = table_status.get('Index_length', 0)

            if isinstance(data_length, (int, float)) and data_length > 100 * 1024 * 1024:  # 100MB
                issues_found.append(f"📊 表数据较大 ({data_length / 1024 / 1024:.1f}MB)，考虑分区或归档")

            if isinstance(index_length, (int, float)) and isinstance(data_length, (int, float)) and data_length > 0:
                index_ratio = index_length / data_length
                if index_ratio > 0.5:
                    issues_found.append(f"📊 索引大小占数据大小的 {index_ratio:.1%}，可能过多")

        # 输出结果
        if issues_found:
            performance_issues.append(f"\n🔍 发现的性能问题:")
            for issue in issues_found:
                performance_issues.append(f"  {issue}")

            performance_issues.append(f"\n💡 优化建议:")
            performance_issues.append("  • 确保每个表都有主键")
            performance_issues.append("  • 避免在TEXT/BLOB字段上创建索引")
            performance_issues.append("  • 合理控制VARCHAR字段长度")
            performance_issues.append("  • 定期分析表使用情况，删除不必要的索引")
            performance_issues.append("  • 对于大表考虑分区策略")
        else:
            performance_issues.append(f"\n✅ 未发现明显的性能问题")

        logger.info(f"成功分析表性能: {database_name}.{table_name}")
        return "\n".join(performance_issues)

    except Exception as e:
        logger.error(f"性能分析失败: {e}")
        return f"❌ 性能分析失败: {str(e)}"

if __name__ == "__main__":
    # 启动MCP服务器
    mcp.run()
