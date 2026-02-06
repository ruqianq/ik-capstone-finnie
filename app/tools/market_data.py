import yfinance as yf
from typing import Dict, Any, Optional

class MarketDataTool:
    def get_stock_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetches real-time stock price and basic info for a given symbol.
        """
        try:
            ticker = yf.Ticker(symbol)
            # fast_info is suitable for realtime prices
            info = ticker.fast_info
            
            # Create a simplified dictionary
            data = {
                "symbol": symbol.upper(),
                "last_price": info.last_price,
                "previous_close": info.previous_close,
                "change_percent": ((info.last_price - info.previous_close) / info.previous_close) * 100
            }
            return data
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None

    def get_company_info(self, symbol: str) -> str:
        """
        Fetches company summary.
        """
        try:
            ticker = yf.Ticker(symbol)
            return ticker.info.get("longBusinessSummary", "No summary available.")
        except Exception as e:
            return f"Error fetching info: {e}"
