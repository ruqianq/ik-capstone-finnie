from app.tools.market_data import MarketDataTool
from app.database import get_db, PortfolioItem, init_db
import re
from sqlalchemy.orm import Session

class PortfolioAgent:
    def __init__(self):
        self.market_tool = MarketDataTool()
        # Ensure DB tables exist
        init_db()
        
    def process_query(self, query: str) -> str:
        """
        Analyzes the query for:
        1. "Price of X" (Market Data)
        2. "Add X shares of Y" (Portfolio Write)
        3. "My Portfolio" (Portfolio Read)
        """
        query_upper = query.upper()
        
        # 1. ADD HOLDING Logic: "ADD 10 AAPL"
        add_match = re.search(r"ADD\s+(\d+)\s+([A-Z]{1,5})", query_upper)
        if add_match:
            qty = float(add_match.group(1))
            symbol = add_match.group(2)
            return self.add_holding(symbol, qty)
            
        # 2. VIEW PORTFOLIO Logic: "MY PORTFOLIO"
        if "PORTFOLIO" in query_upper:
            return self.view_portfolio()

        # 3. MARKET DATA Logic (Existing)
        # 0. Pre-process known company names to tickers
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
        
        for name, ticker in COMPANY_MAPPING.items():
            if name in query_upper:
                query_upper = query_upper.replace(name, ticker)
                
        common_words = {
            "WHAT", "HOW", "IS", "THE", "PRICE", "OF", "AND", "OR", "IN", 
            "A", "AN", "TELL", "ME", "ABOUT", "STOCK", "MARKET", "VALUE", 
            "QUOTE", "CURRENT", "NOW", "TODAY", "PLEASE", "HEY", "HI", "HELLO"
        }
        
        potential_tickers = re.findall(r'\b[A-Z]{1,5}\b', query_upper)
        tickers = [t for t in potential_tickers if t not in common_words]
        
        if not tickers:
             return "I couldn't identify any commands or symbols. Try 'Price of AAPL', 'Add 10 AAPL', or 'My Portfolio'."
            
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

    def add_holding(self, symbol: str, quantity: float):
        db = next(get_db())
        try:
            # Check if exists
            item = db.query(PortfolioItem).filter(PortfolioItem.symbol == symbol).first()
            if item:
                item.quantity += quantity
            else:
                # Fetch current price for 'avg_price' (approximation)
                price_data = self.market_tool.get_stock_price(symbol)
                price = price_data['last_price'] if price_data else 0.0
                item = PortfolioItem(symbol=symbol, quantity=quantity, avg_price=price)
                db.add(item)
            db.commit()
            return f"Successfully added {quantity} shares of {symbol} to your portfolio."
        except Exception as e:
            return f"Error adding to portfolio: {e}"
        finally:
            db.close()

    def view_portfolio(self):
        db = next(get_db())
        try:
            items = db.query(PortfolioItem).all()
            if not items:
                return "Your portfolio is empty. Add stocks with 'Add 10 AAPL'."
            
            report = ["**My Portfolio**"]
            total_value = 0.0
            
            for item in items:
                price_data = self.market_tool.get_stock_price(item.symbol)
                current_price = price_data['last_price'] if price_data else 0.0
                value = current_price * item.quantity
                total_value += value
                
                report.append(f"- **{item.symbol}**: {item.quantity} shares @ ${current_price:.2f} = ${value:.2f}")
                
            report.append(f"\n**Total Value**: ${total_value:.2f}")
            return "\n".join(report)
        except Exception as e:
            return f"Error viewing portfolio: {e}"
        finally:
            db.close()
