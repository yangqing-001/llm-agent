"""
终端命令执行MCP服务器

提供安全的本地终端命令执行功能，支持AI调用各种系统命令。

Author: FangGL
Date: 2024-12-19
"""

from mcp.server.fastmcp import FastMCP
import logging
import subprocess
import shlex
import os
from typing import Optional, List

# 配置日志记录器
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 创建FastMCP实例
mcp = FastMCP("Terminal")

# 危险命令黑名单 - 防止执行危险操作
DANGEROUS_COMMANDS = {
    'rm', 'rmdir', 'del', 'format', 'fdisk', 'mkfs', 
    'dd', 'shutdown', 'reboot', 'halt', 'poweroff',
    'sudo', 'su', 'passwd', 'chmod', 'chown',
    'mv', 'cp', 'rsync'  # 移动和复制也可能危险
}

# 允许的安全命令白名单
SAFE_COMMANDS = {
    'ls', 'dir', 'pwd', 'cd', 'echo', 'cat', 'head', 'tail',
    'grep', 'find', 'locate', 'which', 'whereis', 'type',
    'ps', 'top', 'htop', 'df', 'du', 'free', 'uptime',
    'date', 'whoami', 'id', 'uname', 'hostname',
    'ping', 'curl', 'wget', 'git', 'npm', 'pip',
    'python', 'node', 'java', 'javac', 'gcc', 'make'
}


def is_command_safe(command: str) -> tuple[bool, str]:
    """
    检查命令是否安全
    
    Args:
        command: 要执行的命令字符串
        
    Returns:
        tuple: (是否安全, 原因说明)
    """
    if not command.strip():
        return False, "空命令"
    
    # 解析命令的第一个部分（实际命令名）
    try:
        args = shlex.split(command)
        cmd_name = args[0].lower()
        
        # 移除路径前缀，只检查命令名
        cmd_base = os.path.basename(cmd_name)
        
        # 检查是否在危险命令列表中
        if cmd_base in DANGEROUS_COMMANDS:
            return False, f"命令 '{cmd_base}' 被列为危险命令"
        
        # 检查是否包含危险字符
        dangerous_chars = ['>', '>>', '|', '&', ';', '`', '$', '!']
        for char in dangerous_chars:
            if char in command:
                return False, f"命令包含危险字符: '{char}'"
        
        return True, "命令通过安全检查"
        
    except ValueError as e:
        return False, f"命令解析失败: {e}"


@mcp.tool()
def execute_command(command: str, timeout: int = 30, working_dir: Optional[str] = None) -> dict:
    """
    这是一个执行终端命令的工具，当用户需要使用终端工具或执行命令时，可以使用该工具执行对应终端命令
    
    Args:
        command: 要执行的命令字符串
        timeout: 命令超时时间(秒)，默认30秒
        working_dir: 工作目录，默认为当前目录
        
    Returns:
        dict: 包含执行结果的字典
            - success: 是否成功执行
            - stdout: 标准输出
            - stderr: 错误输出  
            - return_code: 返回码
            - command: 执行的命令
    """
    logger.info(f"收到命令执行请求: {command}")
    
    # 安全检查
    is_safe, reason = is_command_safe(command)
    if not is_safe:
        logger.warning(f"命令被拒绝: {command}, 原因: {reason}")
        return {
            "success": False,
            "stdout": "",
            "stderr": f"安全检查失败: {reason}",
            "return_code": -1,
            "command": command
        }
    
    try:
        # 设置工作目录
        cwd = working_dir if working_dir and os.path.exists(working_dir) else None
        
        # 执行命令
        logger.info(f"执行命令: {command} (工作目录: {cwd or '当前目录'})")
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd
        )
        
        logger.info(f"命令执行完成，返回码: {result.returncode}")
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "command": command
        }
        
    except subprocess.TimeoutExpired:
        logger.error(f"命令执行超时: {command}")
        return {
            "success": False,
            "stdout": "",
            "stderr": f"命令执行超时 ({timeout}秒)",
            "return_code": -1,
            "command": command
        }
        
    except Exception as e:
        logger.error(f"命令执行异常: {command}, 错误: {e}")
        return {
            "success": False,
            "stdout": "",
            "stderr": f"执行异常: {str(e)}",
            "return_code": -1,
            "command": command
        }


@mcp.tool()
def get_current_directory() -> dict:
    """
    获取当前工作目录
    
    Returns:
        dict: 包含当前目录信息
    """
    try:
        current_dir = os.getcwd()
        logger.info(f"获取当前目录: {current_dir}")
        return {
            "success": True,
            "current_directory": current_dir,
            "exists": os.path.exists(current_dir)
        }
    except Exception as e:
        logger.error(f"获取当前目录失败: {e}")
        return {
            "success": False,
            "current_directory": "",
            "error": str(e)
        }


@mcp.tool()
def list_safe_commands() -> dict:
    """
    列出推荐的安全命令
    
    Returns:
        dict: 包含安全命令列表
    """
    logger.info("返回安全命令列表")
    return {
        "safe_commands": sorted(list(SAFE_COMMANDS)),
        "dangerous_commands": sorted(list(DANGEROUS_COMMANDS)),
        "note": "建议使用safe_commands中的命令，避免使用dangerous_commands中的命令"
    }


if __name__ == "__main__":
    logger.info("启动终端命令执行MCP服务器")
    logger.info(f"支持 {len(SAFE_COMMANDS)} 个推荐安全命令")
    logger.info(f"禁止 {len(DANGEROUS_COMMANDS)} 个危险命令")
    mcp.run(transport="stdio") 