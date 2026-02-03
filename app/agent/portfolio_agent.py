```python
from app.tools.market_data import MarketDataTool
import re

class PortfolioAgent:
    def __init__(self):
        self.market_tool = MarketDataTool()
        
    def process_query(self, query: str) -> str:
        """
        Analyzes the query for stock symbols and returns their data.
        """
        # Use uppercase for extraction to handle "aapl" -> "AAPL"
        
        # 0. Pre-process known company names to tickers
        # This is a manual mapping for common requests. In production, use a Search API.
        COMPANY_MAPPING = {
            "GOOGLE": "GOOG",
            "MICROSOFT": "MSFT",
            "APPLE": "AAPL",
            "AMAZON": "AMZN",
            "META": "META",
            "FACEBOOK": "META",
            "TESLA": "TSLA",
            "NETFLIX": "NFLX",
            "NVIDIA": "NVDA"
        }
        
        upper_query = query.upper()
        for name, ticker in COMPANY_MAPPING.items():
            if name in upper_query:
                upper_query = upper_query.replace(name, ticker)
                
        # Also expands common words list to avoid false positives like "TELL"
        potential_tickers = re.findall(r'\b[A-Z]{1,5}\b', upper_query)
        
        # Filter out common uppercase words to reduce false positives
        common_words = {
            "WHAT", "HOW", "IS", "THE", "PRICE", "OF", "AND", "OR", "IN", 
            "A", "AN", "TELL", "ME", "ABOUT", "STOCK", "MARKET", "VALUE", 
            "QUOTE", "CURRENT", "NOW", "TODAY", "PLEASE", "HEY", "HI", "HELLO"
        }
        tickers = [t for t in potential_tickers if t not in common_words]
        
        if not tickers:
            return "I couldn't identify any stock symbols in your query. Try asking 'What is the price of AAPL?'"
            
        responses = []
        for ticker in tickers:
            data = self.market_tool.get_stock_price(ticker)
            if data:
                price = data['last_price']
                change = data['change_percent']
                responses.append(f"**{ticker}**: ${price:.2f} ({change:+.2f}%)")
            else:
                responses.append(f"Could not fetch data for {ticker}.")
                
        return "\n\n".join(responses)
