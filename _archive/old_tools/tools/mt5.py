"""MT5 交易工具"""
from langchain.tools import tool


@tool
def mt5_get_price(symbol: str) -> str:
    """获取 MT5 实时报价"""
    try:
        # Try the official MT5 Python package
        try:
            import MetaTrader5 as mt5
            
            if not mt5.initialize():
                return "MT5 初始化失败，请确认已安装并登录 MT5 客户端"
            
            symbol = symbol.strip().upper()
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                info = mt5.symbol_info(symbol)
                if info is None:
                    return f"未找到交易品种 '{symbol}'"
                return f"{symbol}: Bid {info.bid:.5f} / Ask {info.ask:.5f} (点差: {info.spread})"
            
            mt5.shutdown()
            return f"{symbol}: Bid {tick.bid:.5f} / Ask {tick.ask:.5f} | 时间: {tick.time}"
        except ImportError:
            pass
        
        # Try using external API as fallback (forex)
        import urllib.request
        import json
        
        symbol = symbol.strip().upper()
        # Try free forex API for common pairs
        forex_pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "USDCHF"]
        if symbol in forex_pairs:
            url = f"https://api.exchangerate-api.com/v4/latest/{symbol[:3]}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                rate = data.get("rates", {}).get(symbol[3:], 0)
                return f"{symbol}: {rate:.5f} (来源: ExchangeRate-API)"
        
        return f"无法获取 {symbol} 实时报价。请安装 MetaTrader5 客户端或使用支持的品种 {forex_pairs}"
    
    except Exception as e:
        return f"获取报价失败: {str(e)[:200]}"


@tool
def mt5_place_order(symbol: str, volume: float, order_type: str) -> str:
    """MT5 下单（需二次确认）"""
    try:
        import MetaTrader5 as mt5
        
        if not mt5.initialize():
            return "MT5 初始化失败，请确认 MT5 客户端已启动并登录"
        
        symbol = symbol.strip().upper()
        order_type = order_type.strip().lower()
        
        # Map order type
        mt5_order = mt5.ORDER_TYPE_BUY if order_type in ("buy", "买入") else mt5.ORDER_TYPE_SELL
        
        price = mt5.symbol_info_tick(symbol).ask if mt5_order == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": mt5_order,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": "AI Agent Workbench",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        mt5.shutdown()
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return f"订单失败: retcode={result.retcode}, comment={result.comment}"
        
        return f"✅ 订单成功: {symbol} {order_type.upper()} {volume}手 @ {price:.5f} (ticket={result.order})"
    
    except ImportError:
        return "MT5 Python 包未安装。请安装: pip install MetaTrader5，并确保 MT5 客户端已登录"
    except Exception as e:
        return f"下单失败: {str(e)[:200]}"
