"""
浏览器控制MCP服务器

提供浏览器控制功能，包括打开浏览器、访问指定网址、控制不同浏览器等。

Author: FangGL
Date: 2024-12-19
"""

from mcp.server.fastmcp import FastMCP
import logging
import webbrowser
import subprocess
import platform
import os
import time
from typing import Optional, List
from urllib.parse import urlparse

# 配置日志记录器
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 创建FastMCP实例
mcp = FastMCP("BrowserControl")

# 支持的浏览器配置
SUPPORTED_BROWSERS = {
    "default": "系统默认浏览器",
    "chrome": "Google Chrome",
    "safari": "Safari", 
    "firefox": "Firefox",
    "edge": "Microsoft Edge",
    "opera": "Opera"
}

# 浏览器可执行文件路径（macOS）
BROWSER_PATHS = {
    "chrome": [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chrome.app/Contents/MacOS/Chrome"
    ],
    "safari": ["/Applications/Safari.app/Contents/MacOS/Safari"],
    "firefox": [
        "/Applications/Firefox.app/Contents/MacOS/firefox",
        "/Applications/Mozilla Firefox.app/Contents/MacOS/firefox"
    ],
    "edge": [
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Edge.app/Contents/MacOS/Edge"
    ],
    "opera": ["/Applications/Opera.app/Contents/MacOS/Opera"]
}


def is_valid_url(url: str) -> bool:
    """
    验证URL是否有效
    
    Args:
        url: 要验证的URL
        
    Returns:
        bool: URL是否有效
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def get_browser_executable(browser_name: str) -> Optional[str]:
    """
    获取浏览器可执行文件路径
    
    Args:
        browser_name: 浏览器名称
        
    Returns:
        str: 可执行文件路径，如果未找到返回None
    """
    if browser_name not in BROWSER_PATHS:
        return None
    
    for path in BROWSER_PATHS[browser_name]:
        if os.path.exists(path):
            return path
    
    return None


@mcp.tool()
def open_browser(url: str = "https://www.google.com", browser: str = "default") -> dict:
    """
    打开浏览器并访问指定网址
    
    Args:
        url: 要访问的网址，默认为Google
        browser: 浏览器类型，支持: default, chrome, safari, firefox, edge, opera
        
    Returns:
        dict: 操作结果
    """
    logger.info(f"打开浏览器: {browser}, 访问: {url}")
    
    try:
        # URL验证
        if not url.startswith(('http://', 'https://', 'file://')):
            url = 'https://' + url
        
        if not is_valid_url(url) and not url.startswith('file://'):
            return {
                "success": False,
                "error": f"无效的URL格式: {url}",
                "url": url,
                "browser": browser
            }
        
        # 使用默认浏览器
        if browser == "default":
            webbrowser.open(url)
            logger.info(f"使用默认浏览器打开: {url}")
            return {
                "success": True,
                "message": f"已使用默认浏览器打开: {url}",
                "url": url,
                "browser": "系统默认浏览器"
            }
        
        # 使用指定浏览器
        if browser in BROWSER_PATHS:
            browser_path = get_browser_executable(browser)
            if browser_path:
                try:
                    subprocess.Popen([browser_path, url])
                    logger.info(f"使用{browser}打开: {url}")
                    return {
                        "success": True,
                        "message": f"已使用{SUPPORTED_BROWSERS[browser]}打开: {url}",
                        "url": url,
                        "browser": SUPPORTED_BROWSERS[browser],
                        "executable": browser_path
                    }
                except Exception as e:
                    logger.error(f"启动{browser}失败: {e}")
                    # 回退到默认浏览器
                    webbrowser.open(url)
                    return {
                        "success": True,
                        "message": f"{browser}启动失败，已使用默认浏览器打开: {url}",
                        "url": url,
                        "browser": "默认浏览器（回退）",
                        "warning": f"指定浏览器启动失败: {str(e)}"
                    }
            else:
                return {
                    "success": False,
                    "error": f"未找到{browser}浏览器",
                    "url": url,
                    "browser": browser,
                    "suggestion": "请检查浏览器是否已安装"
                }
        else:
            return {
                "success": False,
                "error": f"不支持的浏览器: {browser}",
                "url": url,
                "supported_browsers": list(SUPPORTED_BROWSERS.keys())
            }
            
    except Exception as e:
        logger.error(f"打开浏览器异常: {e}")
        return {
            "success": False,
            "error": str(e),
            "url": url,
            "browser": browser
        }


@mcp.tool()
def open_multiple_tabs(urls: List[str], browser: str = "default", delay: float = 0.5) -> dict:
    """
    在同一浏览器中打开多个标签页
    
    Args:
        urls: 要打开的网址列表
        browser: 浏览器类型
        delay: 打开标签页之间的延迟（秒）
        
    Returns:
        dict: 操作结果
    """
    logger.info(f"批量打开{len(urls)}个标签页")
    
    try:
        if not urls:
            return {
                "success": False,
                "error": "URL列表为空"
            }
        
        opened_urls = []
        failed_urls = []
        
        for i, url in enumerate(urls):
            try:
                if i > 0 and delay > 0:
                    time.sleep(delay)
                
                result = open_browser(url, browser)
                if result["success"]:
                    opened_urls.append(url)
                else:
                    failed_urls.append({"url": url, "error": result["error"]})
                    
            except Exception as e:
                failed_urls.append({"url": url, "error": str(e)})
        
        return {
            "success": len(opened_urls) > 0,
            "total_urls": len(urls),
            "opened_count": len(opened_urls),
            "failed_count": len(failed_urls),
            "opened_urls": opened_urls,
            "failed_urls": failed_urls,
            "browser": browser
        }
        
    except Exception as e:
        logger.error(f"批量打开标签页异常: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_urls": len(urls) if urls else 0
        }


@mcp.tool()
def open_search(query: str, search_engine: str = "google", browser: str = "default") -> dict:
    """
    打开搜索引擎并搜索指定内容
    
    Args:
        query: 搜索关键词
        search_engine: 搜索引擎，支持: google, bing, baidu, duckduckgo, yahoo
        browser: 浏览器类型
        
    Returns:
        dict: 操作结果
    """
    logger.info(f"搜索: {query} (引擎: {search_engine})")
    
    # 搜索引擎URL模板
    search_engines = {
        "google": "https://www.google.com/search?q={}",
        "bing": "https://www.bing.com/search?q={}",
        "baidu": "https://www.baidu.com/s?wd={}",
        "duckduckgo": "https://duckduckgo.com/?q={}",
        "yahoo": "https://search.yahoo.com/search?p={}"
    }
    
    try:
        if search_engine not in search_engines:
            return {
                "success": False,
                "error": f"不支持的搜索引擎: {search_engine}",
                "supported_engines": list(search_engines.keys())
            }
        
        # 构建搜索URL
        import urllib.parse
        encoded_query = urllib.parse.quote_plus(query)
        search_url = search_engines[search_engine].format(encoded_query)
        
        # 打开浏览器搜索
        result = open_browser(search_url, browser)
        
        if result["success"]:
            result["search_query"] = query
            result["search_engine"] = search_engine
            result["message"] = f"已在{search_engine}上搜索: {query}"
        
        return result
        
    except Exception as e:
        logger.error(f"搜索异常: {e}")
        return {
            "success": False,
            "error": str(e),
            "query": query,
            "search_engine": search_engine
        }


@mcp.tool()
def check_browser_availability() -> dict:
    """
    检查系统中可用的浏览器
    
    Returns:
        dict: 浏览器可用性报告
    """
    logger.info("检查浏览器可用性")
    
    try:
        available_browsers = []
        unavailable_browsers = []
        
        for browser_name, display_name in SUPPORTED_BROWSERS.items():
            if browser_name == "default":
                available_browsers.append({
                    "name": browser_name,
                    "display_name": display_name,
                    "status": "available",
                    "executable": "系统默认"
                })
            else:
                executable = get_browser_executable(browser_name)
                if executable:
                    available_browsers.append({
                        "name": browser_name,
                        "display_name": display_name,
                        "status": "available",
                        "executable": executable
                    })
                else:
                    unavailable_browsers.append({
                        "name": browser_name,
                        "display_name": display_name,
                        "status": "not_found"
                    })
        
        return {
            "success": True,
            "total_browsers": len(SUPPORTED_BROWSERS),
            "available_count": len(available_browsers),
            "unavailable_count": len(unavailable_browsers),
            "available_browsers": available_browsers,
            "unavailable_browsers": unavailable_browsers,
            "system": platform.system()
        }
        
    except Exception as e:
        logger.error(f"检查浏览器可用性异常: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def open_local_file(file_path: str, browser: str = "default") -> dict:
    """
    在浏览器中打开本地文件
    
    Args:
        file_path: 本地文件路径
        browser: 浏览器类型
        
    Returns:
        dict: 操作结果
    """
    logger.info(f"在浏览器中打开本地文件: {file_path}")
    
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"文件不存在: {file_path}",
                "file_path": file_path
            }
        
        # 检查文件类型
        _, ext = os.path.splitext(file_path)
        web_extensions = ['.html', '.htm', '.xml', '.svg', '.pdf', '.txt', '.md']
        
        if ext.lower() not in web_extensions:
            logger.warning(f"文件类型可能不适合在浏览器中打开: {ext}")
        
        # 转换为file:// URL
        if platform.system() == "Windows":
            file_url = f"file:///{file_path.replace(os.sep, '/')}"
        else:
            file_url = f"file://{file_path}"
        
        result = open_browser(file_url, browser)
        
        if result["success"]:
            result["file_path"] = file_path
            result["file_extension"] = ext
            result["message"] = f"已在浏览器中打开本地文件: {file_path}"
        
        return result
        
    except Exception as e:
        logger.error(f"打开本地文件异常: {e}")
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path
        }


@mcp.tool()
def get_browser_capabilities() -> dict:
    """
    获取浏览器控制服务的功能说明
    
    Returns:
        dict: 服务功能描述
    """
    return {
        "service_name": "浏览器控制服务",
        "version": "1.0.0", 
        "author": "FangGL",
        "capabilities": [
            "打开默认浏览器",
            "打开指定浏览器",
            "访问网址",
            "搜索功能",
            "批量打开标签页",
            "打开本地文件",
            "浏览器可用性检查"
        ],
        "supported_browsers": SUPPORTED_BROWSERS,
        "supported_search_engines": [
            "google", "bing", "baidu", "duckduckgo", "yahoo"
        ],
        "available_tools": [
            "open_browser - 打开浏览器访问网址",
            "open_multiple_tabs - 批量打开标签页",
            "open_search - 搜索功能",
            "check_browser_availability - 检查浏览器可用性",
            "open_local_file - 在浏览器中打开本地文件",
            "get_browser_capabilities - 获取服务功能"
        ],
        "examples": [
            "open_browser('https://www.github.com', 'chrome')",
            "open_search('Python教程', 'google')",
            "open_multiple_tabs(['https://google.com', 'https://github.com'])",
            "check_browser_availability()"
        ]
    }


if __name__ == "__main__":
    logger.info("启动浏览器控制MCP服务器")
    logger.info(f"支持的浏览器: {list(SUPPORTED_BROWSERS.keys())}")
    logger.info("提供功能: 浏览器打开、网址访问、搜索、本地文件打开等")
    mcp.run(transport="stdio") 