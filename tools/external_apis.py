"""外部 API：新闻、情绪分析、宏观经济数据（支持原生异步）"""
import asyncio
from concurrent.futures import Executor
from langchain.tools import tool

# 由 AgentSession 注入的 CPU/同步任务线程池
_cpu_executor: Executor = None


def set_cpu_executor(executor: Executor):
    """注入同步任务线程池，供 akshare 等无 async API 的库使用"""
    global _cpu_executor
    _cpu_executor = executor


@tool
def fetch_financial_news(query: str = "", limit: int = 5) -> str:
    """获取财经新闻"""
    try:
        import akshare as ak

        if query:
            df = ak.stock_info_global_futu(symbol=query)
            if not df.empty:
                headlines = df.head(limit).to_string(index=False)
                return f"📰 {query} 相关新闻:\n{headlines}"

        # General market news
        df = ak.stock_info_global_em()
        if not df.empty:
            return f"📰 全球市场快讯 (最近{limit}条):\n{df.head(limit).to_string(index=False)}"

        return "暂无新闻数据"
    except ImportError:
        return "需要 akshare: pip install akshare"
    except Exception as e:
        return f"获取新闻失败: {str(e)[:200]}"


async def arun_fetch_financial_news(args: dict) -> str:
    """异步入口：akshare 调用在 _cpu_executor 中执行"""
    loop = asyncio.get_running_loop()
    executor = _cpu_executor
    if executor is None:
        raise RuntimeError("external_apis.set_cpu_executor() must be called before arun")
    return await loop.run_in_executor(executor, fetch_financial_news.run, args)


# arun 入口统一在 tools/__init__.py 的 ARUN_MAP 中注册


@tool
def fetch_macro_data(indicator: str = "cpi") -> str:
    """获取宏观经济数据: cpi, gdp, pmi, money_supply"""
    try:
        import akshare as ak

        indicator = indicator.lower().strip()

        if indicator == "cpi":
            df = ak.macro_china_cpi_yearly()
            latest = df.tail(5).to_string(index=False)
            return f"中国 CPI (最近5条):\n{latest}"
        elif indicator == "gdp":
            df = ak.macro_china_gdp_yearly()
            latest = df.tail(8).to_string(index=False)
            return f"中国 GDP (最近8条):\n{latest}"
        elif indicator == "pmi":
            df = ak.macro_china_pmi()
            latest = df.tail(5).to_string(index=False)
            return f"中国 PMI (最近5条):\n{latest}"
        else:
            return f"支持的指标: cpi, gdp, pmi"
    except ImportError:
        return "需要 akshare: pip install akshare"
    except Exception as e:
        return f"获取宏观数据失败: {str(e)[:200]}"


async def arun_fetch_macro_data(args: dict) -> str:
    loop = asyncio.get_running_loop()
    executor = _cpu_executor
    if executor is None:
        raise RuntimeError("external_apis.set_cpu_executor() must be called before arun")
    return await loop.run_in_executor(executor, fetch_macro_data.run, args)


# arun 入口统一在 tools/__init__.py 的 ARUN_MAP 中注册
