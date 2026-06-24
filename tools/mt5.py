from langchain.tools import tool

@tool
def mt5_get_price(symbol: str) -> str:
    """获取 MT5 实时报价（占位）"""
    return f"[占位] {symbol} 当前价格: 0.0"

@tool
def mt5_place_order(symbol: str, volume: float, order_type: str) -> str:
    """MT5 下单（占位，需二次确认）"""
    return f"[占位] 订单: {symbol} {order_type} {volume} 手"