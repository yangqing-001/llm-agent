"""
MySQL数据库控制MCP服务器

提供完整的MySQL数据库操作功能，包括创建数据库、创建表、数据增删改查等。
支持详细的错误提示和用户友好的错误处理。
"""

from mcp.server.fastmcp import FastMCP
import logging
import pymysql
import json
import os
from typing import Optional, Union, Dict, Any
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
mcp = FastMCP("MySQL Database Controller")

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
    """
    获取MySQL数据库连接
    
    Args:
        database: 可选的数据库名称
        
    Returns:
        pymysql.Connection: 数据库连接对象
        
    Raises:
        Exception: 连接失败时抛出异常
    """
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

def format_error_message(error: Exception, operation: str) -> str:
    """
    格式化错误消息，提供用户友好的错误提示
    
    Args:
        error: 异常对象
        operation: 操作类型
        
    Returns:
        str: 格式化的错误消息
    """
    error_msg = str(error)
    
    # 常见错误类型的友好提示
    if "Access denied" in error_msg:
        return f"❌ {operation}失败: 数据库访问被拒绝，请检查用户名和密码是否正确"
    elif "Can't connect to MySQL server" in error_msg:
        return f"❌ {operation}失败: 无法连接到MySQL服务器，请检查服务器是否运行在 {MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}"
    elif "Unknown database" in error_msg:
        return f"❌ {operation}失败: 数据库不存在，请先创建数据库"
    elif "Table" in error_msg and "already exists" in error_msg:
        return f"❌ {operation}失败: 表已存在，请使用不同的表名或删除现有表"
    elif "Table" in error_msg and "doesn't exist" in error_msg:
        return f"❌ {operation}失败: 表不存在，请先创建表"
    elif "Duplicate entry" in error_msg:
        return f"❌ {operation}失败: 数据重复，违反了唯一性约束"
    elif "Column" in error_msg and "cannot be null" in error_msg:
        return f"❌ {operation}失败: 必填字段不能为空"
    elif "You have an error in your SQL syntax" in error_msg:
        return f"❌ {operation}失败: SQL语法错误，请检查SQL语句格式"
    elif "Data too long for column" in error_msg:
        return f"❌ {operation}失败: 数据长度超过字段限制"
    else:
        return f"❌ {operation}失败: {error_msg}"

@mcp.tool()
def create_database(database_name: str) -> str:
    """
    创建新的MySQL数据库
    
    Args:
        database_name: 数据库名称
        
    Returns:
        str: 操作结果消息
    """
    try:
        connection = get_mysql_connection()
        cursor = connection.cursor()
        
        # 创建数据库
        sql = f"CREATE DATABASE `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        cursor.execute(sql)
        
        cursor.close()
        connection.close()
        
        logger.info(f"成功创建数据库: {database_name}")
        return f"✅ 成功创建数据库: {database_name}"
        
    except Exception as e:
        logger.error(f"创建数据库失败: {e}")
        return format_error_message(e, "创建数据库")

@mcp.tool()
def create_table(database_name: str, table_name: str, columns: str) -> str:
    """
    在指定数据库中创建新表
    
    Args:
        database_name: 数据库名称
        table_name: 表名称
        columns: 列定义，格式如: "id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100) NOT NULL, age INT"
        
    Returns:
        str: 操作结果消息
    """
    try:
        connection = get_mysql_connection(database_name)
        cursor = connection.cursor()
        
        # 创建表
        sql = f"CREATE TABLE `{table_name}` ({columns})"
        cursor.execute(sql)
        
        cursor.close()
        connection.close()
        
        logger.info(f"成功在数据库 {database_name} 中创建表: {table_name}")
        return f"✅ 成功在数据库 {database_name} 中创建表: {table_name}"
        
    except Exception as e:
        logger.error(f"创建表失败: {e}")
        return format_error_message(e, "创建表")

@mcp.tool()
def insert_data(database_name: str, table_name: str, data: Union[str, Dict[str, Any]]) -> str:
    """
    向表中插入数据

    Args:
        database_name: 数据库名称
        table_name: 表名称
        data: 插入的数据，可以是JSON格式字符串或字典，如: '{"name": "张三", "age": 25}' 或 {"name": "张三", "age": 25}

    Returns:
        str: 操作结果消息
    """
    try:
        connection = get_mysql_connection(database_name)
        cursor = connection.cursor()

        # 处理数据格式 - 支持字符串和字典两种格式
        if isinstance(data, str):
            try:
                data_dict = json.loads(data)
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}")
                return f"❌ 插入数据失败: 数据格式错误，请提供有效的JSON格式数据。错误详情: {e}"
        elif isinstance(data, dict):
            data_dict = data
        else:
            return f"❌ 插入数据失败: 数据类型错误，请提供JSON字符串或字典格式的数据"
        
        # 构建INSERT语句
        columns = ', '.join([f"`{col}`" for col in data_dict.keys()])
        placeholders = ', '.join(['%s'] * len(data_dict))
        values = list(data_dict.values())
        
        sql = f"INSERT INTO `{table_name}` ({columns}) VALUES ({placeholders})"
        cursor.execute(sql, values)
        
        affected_rows = cursor.rowcount
        cursor.close()
        connection.close()
        
        logger.info(f"成功向表 {table_name} 插入 {affected_rows} 行数据")
        return f"✅ 成功向表 {table_name} 插入 {affected_rows} 行数据"

    except Exception as e:
        logger.error(f"插入数据失败: {e}")
        return format_error_message(e, "插入数据")

@mcp.tool()
def update_data(database_name: str, table_name: str, set_data: Union[str, Dict[str, Any]], where_condition: str) -> str:
    """
    更新表中的数据

    Args:
        database_name: 数据库名称
        table_name: 表名称
        set_data: 要更新的数据，可以是JSON格式字符串或字典，如: '{"name": "李四", "age": 30}' 或 {"name": "李四", "age": 30}
        where_condition: WHERE条件，如: "id = 1" 或 "name = '张三'"

    Returns:
        str: 操作结果消息
    """
    try:
        connection = get_mysql_connection(database_name)
        cursor = connection.cursor()

        # 处理数据格式 - 支持字符串和字典两种格式
        if isinstance(set_data, str):
            try:
                data_dict = json.loads(set_data)
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}")
                return f"❌ 更新数据失败: 数据格式错误，请提供有效的JSON格式数据。错误详情: {e}"
        elif isinstance(set_data, dict):
            data_dict = set_data
        else:
            return f"❌ 更新数据失败: 数据类型错误，请提供JSON字符串或字典格式的数据"
        
        # 构建UPDATE语句
        set_clause = ', '.join([f"`{col}` = %s" for col in data_dict.keys()])
        values = list(data_dict.values())
        
        sql = f"UPDATE `{table_name}` SET {set_clause} WHERE {where_condition}"
        cursor.execute(sql, values)
        
        affected_rows = cursor.rowcount
        cursor.close()
        connection.close()
        
        logger.info(f"成功更新表 {table_name} 中的 {affected_rows} 行数据")
        return f"✅ 成功更新表 {table_name} 中的 {affected_rows} 行数据"

    except Exception as e:
        logger.error(f"更新数据失败: {e}")
        return format_error_message(e, "更新数据")

@mcp.tool()
def delete_data(database_name: str, table_name: str, where_condition: str) -> str:
    """
    删除表中的数据
    
    Args:
        database_name: 数据库名称
        table_name: 表名称
        where_condition: WHERE条件，如: "id = 1" 或 "name = '张三'"
        
    Returns:
        str: 操作结果消息
    """
    try:
        connection = get_mysql_connection(database_name)
        cursor = connection.cursor()
        
        # 构建DELETE语句
        sql = f"DELETE FROM `{table_name}` WHERE {where_condition}"
        cursor.execute(sql)
        
        affected_rows = cursor.rowcount
        cursor.close()
        connection.close()
        
        logger.info(f"成功从表 {table_name} 删除 {affected_rows} 行数据")
        return f"✅ 成功从表 {table_name} 删除 {affected_rows} 行数据"
        
    except Exception as e:
        logger.error(f"删除数据失败: {e}")
        return format_error_message(e, "删除数据")

@mcp.tool()
def query_data(database_name: str, table_name: str, where_condition: str = "", limit: int = 10) -> str:
    """
    查询表中的数据
    
    Args:
        database_name: 数据库名称
        table_name: 表名称
        where_condition: 可选的WHERE条件，如: "age > 18"
        limit: 限制返回的行数，默认10行
        
    Returns:
        str: 查询结果
    """
    try:
        connection = get_mysql_connection(database_name)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 构建SELECT语句
        sql = f"SELECT * FROM `{table_name}`"
        if where_condition:
            sql += f" WHERE {where_condition}"
        sql += f" LIMIT {limit}"
        
        cursor.execute(sql)
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        if not results:
            return f"📋 查询完成，表 {table_name} 中没有符合条件的数据"
        
        # 格式化结果
        result_str = f"📋 查询结果 (共 {len(results)} 行):\n"
        for i, row in enumerate(results, 1):
            result_str += f"\n第 {i} 行: {json.dumps(row, ensure_ascii=False, indent=2)}"
        
        logger.info(f"成功查询表 {table_name}，返回 {len(results)} 行数据")
        return result_str
        
    except Exception as e:
        logger.error(f"查询数据失败: {e}")
        return format_error_message(e, "查询数据")

@mcp.tool()
def show_databases() -> str:
    """
    显示所有数据库
    
    Returns:
        str: 数据库列表
    """
    try:
        connection = get_mysql_connection()
        cursor = connection.cursor()
        
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        db_list = [db[0] for db in databases]
        result = f"📊 MySQL服务器中的数据库列表:\n" + "\n".join([f"  • {db}" for db in db_list])
        
        logger.info(f"成功获取数据库列表，共 {len(db_list)} 个数据库")
        return result
        
    except Exception as e:
        logger.error(f"获取数据库列表失败: {e}")
        return format_error_message(e, "获取数据库列表")

@mcp.tool()
def show_tables(database_name: str) -> str:
    """
    显示指定数据库中的所有表

    Args:
        database_name: 数据库名称

    Returns:
        str: 表列表
    """
    try:
        connection = get_mysql_connection(database_name)
        cursor = connection.cursor()

        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        cursor.close()
        connection.close()

        table_list = [table[0] for table in tables]
        if not table_list:
            return f"📋 数据库 {database_name} 中没有表"

        result = f"📋 数据库 {database_name} 中的表列表:\n" + "\n".join([f"  • {table}" for table in table_list])

        logger.info(f"成功获取数据库 {database_name} 的表列表，共 {len(table_list)} 个表")
        return result

    except Exception as e:
        logger.error(f"获取表列表失败: {e}")
        return format_error_message(e, "获取表列表")

@mcp.tool()
def describe_table(database_name: str, table_name: str) -> str:
    """
    查看表的结构信息，包括字段名、数据类型、是否为空、键信息、默认值等

    Args:
        database_name: 数据库名称
        table_name: 表名称

    Returns:
        str: 表结构详细信息
    """
    try:
        connection = get_mysql_connection(database_name)
        cursor = connection.cursor()

        # 使用DESCRIBE命令获取表结构
        cursor.execute(f"DESCRIBE `{table_name}`")
        columns = cursor.fetchall()

        cursor.close()
        connection.close()

        if not columns:
            return f"📋 表 {table_name} 不存在或没有字段"

        # 格式化表结构信息
        result = f"📋 表 {database_name}.{table_name} 的结构信息:\n"
        result += "=" * 80 + "\n"
        result += f"{'字段名':<20} {'数据类型':<20} {'允许NULL':<10} {'键':<10} {'默认值':<15} {'额外信息'}\n"
        result += "-" * 80 + "\n"

        for column in columns:
            field = column[0]
            type_info = column[1]
            null_info = column[2]
            key_info = column[3] if column[3] else ""
            default_value = str(column[4]) if column[4] is not None else "NULL"
            extra_info = column[5] if column[5] else ""

            result += f"{field:<20} {type_info:<20} {null_info:<10} {key_info:<10} {default_value:<15} {extra_info}\n"

        result += "=" * 80 + "\n"
        result += f"📊 共 {len(columns)} 个字段"

        logger.info(f"成功获取表 {database_name}.{table_name} 的结构信息")
        return result

    except Exception as e:
        logger.error(f"获取表结构失败: {e}")
        return format_error_message(e, "获取表结构")

@mcp.tool()
def show_table_indexes(database_name: str, table_name: str) -> str:
    """
    显示表的索引信息

    Args:
        database_name: 数据库名称
        table_name: 表名称

    Returns:
        str: 表的索引信息
    """
    try:
        connection = get_mysql_connection(database_name)
        cursor = connection.cursor()

        # 获取表的索引信息
        cursor.execute(f"SHOW INDEX FROM `{table_name}`")
        indexes = cursor.fetchall()

        cursor.close()
        connection.close()

        if not indexes:
            return f"📋 表 {database_name}.{table_name} 没有索引"

        # 格式化索引信息
        result = f"📋 表 {database_name}.{table_name} 的索引信息:\n"
        result += "=" * 100 + "\n"
        result += f"{'索引名':<20} {'字段名':<20} {'唯一性':<10} {'索引类型':<15} {'注释'}\n"
        result += "-" * 100 + "\n"

        for index in indexes:
            key_name = index[2]
            column_name = index[4]
            non_unique = "否" if index[1] == 0 else "是"
            index_type = index[10] if len(index) > 10 else ""
            comment = index[11] if len(index) > 11 and index[11] else ""

            result += f"{key_name:<20} {column_name:<20} {non_unique:<10} {index_type:<15} {comment}\n"

        result += "=" * 100 + "\n"
        result += f"📊 共 {len(indexes)} 个索引项"

        logger.info(f"成功获取表 {database_name}.{table_name} 的索引信息")
        return result

    except Exception as e:
        logger.error(f"获取表索引失败: {e}")
        return format_error_message(e, "获取表索引")

@mcp.tool()
def show_create_table(database_name: str, table_name: str) -> str:
    """
    显示创建表的完整SQL语句

    Args:
        database_name: 数据库名称
        table_name: 表名称

    Returns:
        str: 创建表的SQL语句
    """
    try:
        connection = get_mysql_connection(database_name)
        cursor = connection.cursor()

        # 获取创建表的SQL语句
        cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        if not result:
            return f"❌ 无法获取表 {database_name}.{table_name} 的创建语句"

        table_name_result = result[0]
        create_sql = result[1]

        # 格式化输出
        formatted_result = f"📋 表 {database_name}.{table_name} 的创建语句:\n"
        formatted_result += "=" * 80 + "\n"
        formatted_result += create_sql
        formatted_result += "\n" + "=" * 80

        logger.info(f"成功获取表 {database_name}.{table_name} 的创建语句")
        return formatted_result

    except Exception as e:
        logger.error(f"获取表创建语句失败: {e}")
        return format_error_message(e, "获取表创建语句")

if __name__ == "__main__":
    # 启动MCP服务器
    mcp.run()
