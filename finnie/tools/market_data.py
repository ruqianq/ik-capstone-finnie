"""Market data API integrations."""

from typing import Optional, Dict, Any
import yfinance as yf

from finnie.tools.base import ToolWrapper, cached, rate_limited, with_retry
from finnie.config import config
from finnie.observability import log_with_trace


class YFinanceAPI(ToolWrapper):
    """Wrapper for yFinance API with caching and rate limiting."""
    
    def __init__(self):
        super().__init__("yfinance")
        self.enabled = config.market_data.yfinance_enabled
    
    @cached(ttl=300)  # Cache for 5 minutes
    @rate_limited
    @with_retry(max_attempts=3)
    def get_stock_info(self, ticker: str, trace_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get stock information for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            trace_id: Trace ID for observability
            
        Returns:
            Dictionary with stock information
        """
        if not self.enabled:
            log_with_trace(
                "yFinance is disabled",
                trace_id=trace_id,
                level="warning"
            )
            return {"error": "yFinance is disabled"}
        
        try:
            log_with_trace(
                f"Fetching stock info for {ticker}",
                trace_id=trace_id
            )
            
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Extract relevant information
            result = {
                "symbol": ticker,
                "name": info.get("longName", "N/A"),
                "price": info.get("currentPrice", info.get("regularMarketPrice", "N/A")),
                "currency": info.get("currency", "USD"),
                "market_cap": info.get("marketCap", "N/A"),
                "pe_ratio": info.get("trailingPE", "N/A"),
                "dividend_yield": info.get("dividendYield", "N/A"),
                "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
                "52_week_low": info.get("fiftyTwoWeekLow", "N/A"),
            }
            
            self.record_call()
            return result
            
        except Exception as e:
            self.record_error()
            log_with_trace(
                f"Error fetching stock info for {ticker}: {e}",
                trace_id=trace_id,
                level="error"
            )
            return {"error": str(e)}
    
    @cached(ttl=300)
    @rate_limited
    @with_retry(max_attempts=3)
    def get_historical_data(
        self,
        ticker: str,
        period: str = "1mo",
        trace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get historical price data for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            trace_id: Trace ID for observability
            
        Returns:
            Dictionary with historical data
        """
        if not self.enabled:
            return {"error": "yFinance is disabled"}
        
        try:
            log_with_trace(
                f"Fetching historical data for {ticker} (period: {period})",
                trace_id=trace_id
            )
            
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            
            result = {
                "symbol": ticker,
                "period": period,
                "data": hist.to_dict('records') if not hist.empty else [],
                "success": True,
            }
            
            self.record_call()
            return result
            
        except Exception as e:
            self.record_error()
            log_with_trace(
                f"Error fetching historical data for {ticker}: {e}",
                trace_id=trace_id,
                level="error"
            )
            return {"error": str(e), "success": False}


class AlphaVantageAPI(ToolWrapper):
    """Wrapper for Alpha Vantage API with caching and rate limiting."""
    
    def __init__(self):
        super().__init__("alpha_vantage")
        self.api_key = config.market_data.alpha_vantage_key
        self.enabled = bool(self.api_key)
    
    @cached(ttl=300)
    @rate_limited
    @with_retry(max_attempts=3)
    def get_quote(self, symbol: str, trace_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get real-time quote for a symbol.
        
        Args:
            symbol: Stock symbol
            trace_id: Trace ID for observability
            
        Returns:
            Dictionary with quote data
        """
        if not self.enabled:
            log_with_trace(
                "Alpha Vantage is disabled (no API key)",
                trace_id=trace_id,
                level="warning"
            )
            return {"error": "Alpha Vantage API key not configured"}
        
        # Alpha Vantage integration would go here
        # For now, return a placeholder
        log_with_trace(
            f"Alpha Vantage quote request for {symbol}",
            trace_id=trace_id
        )
        
        return {
            "symbol": symbol,
            "message": "Alpha Vantage integration placeholder",
        }


# Global API instances
yfinance_api = YFinanceAPI()
alphavantage_api = AlphaVantageAPI()
