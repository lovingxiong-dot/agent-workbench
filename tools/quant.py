"""
量化工具：股票数据获取（akshare）、策略回测（backtrader）
注意：pandas/akshare/backtrader 为可选依赖，仅在工具调用时动态加载
支持原生异步执行（arun），同步入口（@tool）保留兼容。
"""
import asyncio
from concurrent.futures import Executor
from datetime import datetime, timedelta
from langchain.tools import tool

# 由 AgentSession 注入的 CPU/同步任务线程池
_cpu_executor: Executor = None


def set_cpu_executor(executor: Executor):
    """注入同步任务线程池，供 akshare/backtrader 等无 async API 的库使用"""
    global _cpu_executor
    _cpu_executor = executor


@tool
def fetch_stock_data(ticker: str, start_date: str = "", end_date: str = "") -> str:
    """获取股票历史数据，支持 A股（代码如 000001）、港股（如 00700）、美股（如 AAPL）"""
    try:
        import akshare as ak
        import pandas as pd

        now = datetime.now()
        if not end_date:
            end_date = now.strftime("%Y%m%d")
        else:
            end_date = end_date.replace("-", "")
        if not start_date:
            start_date = (now - timedelta(days=90)).strftime("%Y%m%d")
        else:
            start_date = start_date.replace("-", "")

        ticker = ticker.strip().upper()

        # Determine market and fetch
        if ticker.isdigit() and len(ticker) == 6:
            # A-share
            df = ak.stock_zh_a_hist(symbol=ticker, period="daily",
                                     start_date=start_date, end_date=end_date,
                                     adjust="qfq")
            if df.empty:
                return f"未找到 A股 {ticker} 的数据"
            market = "A股"
        elif ticker.isdigit() and len(ticker) <= 5:
            # HK stock
            if not ticker.startswith("0"):
                ticker = ticker.zfill(5)
            df = ak.stock_hk_hist(symbol=ticker, period="daily",
                                   start_date=start_date, end_date=end_date,
                                   adjust="qfq")
            if df.empty:
                return f"未找到港股 {ticker} 的数据"
            market = "港股"
        else:
            # Assume US stock
            df = ak.stock_us_hist(symbol=ticker, period="daily",
                                   start_date=start_date, end_date=end_date,
                                   adjust="qfq")
            if df.empty:
                return f"未找到美股 {ticker} 的数据"
            market = "美股"

        # Get latest price info
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        change = latest.get("收盘", 0) - prev.get("收盘", 0)
        change_pct = (change / prev.get("收盘", 1)) * 100 if prev.get("收盘", 0) != 0 else 0

        direction = "📈" if change >= 0 else "📉"

        summary = f"""{direction} {market} {ticker} 最近行情:
最新价: {latest.get('收盘', 'N/A')}
最高: {latest.get('最高', 'N/A')}  最低: {latest.get('最低', 'N/A')}
成交量: {latest.get('成交量', 'N/A')}
涨跌: {direction} {change:+.2f} ({change_pct:+.2f}%)
数据范围: {start_date} 至 {end_date}，共 {len(df)} 条记录"""

        # Add brief stats
        closes = pd.to_numeric(df["收盘"], errors='coerce').dropna()
        if len(closes) >= 5:
            summary += f"\n5日均价: {closes.tail(5).mean():.2f}"
        if len(closes) >= 20:
            summary += f"\n20日均价: {closes.tail(20).mean():.2f}"

        return summary

    except ImportError:
        return "akshare 未安装。请运行: pip install akshare"
    except Exception as e:
        return f"获取数据失败: {str(e)[:300]}"


async def arun_fetch_stock_data(args: dict) -> str:
    """异步入口：akshare 调用在 _cpu_executor 中执行"""
    loop = asyncio.get_running_loop()
    executor = _cpu_executor
    if executor is None:
        raise RuntimeError("quant.set_cpu_executor() must be called before arun")
    return await loop.run_in_executor(executor, fetch_stock_data.run, args)


# arun 入口统一在 tools/__init__.py 的 ARUN_MAP 中注册


@tool
def run_backtest(strategy_code: str) -> str:
    """运行量化策略回测（基于 backtrader 引擎）"""
    try:
        import akshare as ak
        import backtrader as bt
        import pandas as pd
        from io import StringIO

        code = strategy_code.strip()

        # Default strategy if code is too short
        if len(code) < 20 or code.lower() in ("sma", "ma", "均线", "test"):
            result = _run_sma_backtest()
            return result

        # Execute user strategy
        try:
            # Prepare a basic Cerebro setup with user code
            cerebro = bt.Cerebro()
            cerebro.addstrategy(type('UserStrategy', (bt.Strategy,), {
                'next': eval(f"lambda self: ({code})")
            }))

            # Fetch data for backtest
            df = ak.stock_zh_a_hist(symbol="000001", period="daily",
                                     start_date="20240101", end_date="20250624",
                                     adjust="qfq")
            if df.empty:
                return "无法获取回测数据"

            df["date"] = pd.to_datetime(df["日期"])
            df.set_index("date", inplace=True)
            data = bt.feeds.PandasData(dataname=df, open="开盘", high="最高",
                                        low="最低", close="收盘", volume="成交量")
            cerebro.adddata(data)
            cerebro.broker.setcash(100000)
            cerebro.broker.setcommission(commission=0.001)

            start_value = cerebro.broker.getvalue()
            result = cerebro.run()
            end_value = cerebro.broker.getvalue()

            profit = end_value - start_value
            profit_pct = (profit / start_value) * 100

            return f"""📊 回测结果:
初始资金: ¥{start_value:,.2f}
最终资金: ¥{end_value:,.2f}
收益: ¥{profit:,.2f} ({profit_pct:+.2f}%)
标的: 平安银行 (000001)
回测周期: 2024-01-01 至 2025-06-24"""

        except SyntaxError as se:
            return f"策略代码语法错误: {str(se)}"
        except Exception as e:
            return f"回测执行失败: {str(e)[:300]}"

    except ImportError as e:
        missing = str(e).split("'")[1] if "'" in str(e) else str(e)
        return f"缺少依赖 {missing}。运行: pip install akshare backtrader"
    except Exception as e:
        return f"回测失败: {str(e)[:300]}"


# run_backtest 保持同步，不附加 arun，由 _call_tool 第 3 步进入 _cpu_executor


def _run_sma_backtest() -> str:
    """内置均线交叉回测示例"""
    try:
        import akshare as ak
        import backtrader as bt
        import pandas as pd

        class SMACross(bt.Strategy):
            params = (('fast', 5), ('slow', 20))

            def __init__(self):
                self.fast_ma = bt.indicators.SMA(self.data.close, period=self.params.fast)
                self.slow_ma = bt.indicators.SMA(self.data.close, period=self.params.slow)
                self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
                self.trades = []

            def next(self):
                if not self.position and self.crossover > 0:
                    self.buy()
                    self.trades.append(('买', self.data.datetime.date(), self.data.close[0]))
                elif self.position and self.crossover < 0:
                    self.sell()
                    self.trades.append(('卖', self.data.datetime.date(), self.data.close[0]))

        df = ak.stock_zh_a_hist(symbol="000001", period="daily",
                                 start_date="20240101", end_date="20250624", adjust="qfq")
        df["date"] = pd.to_datetime(df["日期"])
        df.set_index("date", inplace=True)

        cerebro = bt.Cerebro()
        cerebro.addstrategy(SMACross)
        data = bt.feeds.PandasData(dataname=df, open="开盘", high="最高",
                                    low="最低", close="收盘", volume="成交量")
        cerebro.adddata(data)
        cerebro.broker.setcash(100000)
        cerebro.broker.setcommission(commission=0.001)

        start_val = cerebro.broker.getvalue()
        results = cerebro.run()
        end_val = cerebro.broker.getvalue()
        strategy = results[0]

        profit = end_val - start_val
        profit_pct = (profit / start_val) * 100

        trade_list = "".join([f"\n  {t[0]} {t[1]} @ ¥{t[2]:.2f}" for t in strategy.trades[:10]])
        if len(strategy.trades) > 10:
            trade_list += f"\n  ... 共 {len(strategy.trades)} 笔交易"

        return f"""📊 均线交叉策略回测 (5/20 MA):

标   的: 平安银行 (000001)
初始资金: ¥{start_val:,.2f}
最终资金: ¥{end_val:,.2f}
总收益: ¥{profit:,.2f} ({profit_pct:+.2f}%)
交易记录:{trade_list if trade_list else '\n  无交易信号'}"""
    except ImportError:
        return "需要安装依赖: pip install akshare backtrader"
    except Exception as e:
        return f"回测失败: {str(e)[:300]}"
