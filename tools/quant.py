from langchain.tools import tool

@tool
def fetch_stock_data(ticker: str, start_date: str = "2024-01-01", end_date: str = "2024-12-31") -> str:
    """获取股票历史数据（占位）"""
    return f"[占位] 获取 {ticker} 数据 ({start_date} 至 {end_date})"

@tool
def run_backtest(strategy_code: str) -> str:
    """运行回测（占位）"""
    return f"[占位] 回测策略: {strategy_code[:50]}..."