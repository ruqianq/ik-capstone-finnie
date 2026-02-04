import yfinance as yf
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class MarketAnalysisAgent:
    """
    Agent for market analysis, trends, sector performance, and technical indicators.
    """

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        # Major market indices
        self.indices = {
            "S&P 500": "^GSPC",
            "Dow Jones": "^DJI",
            "NASDAQ": "^IXIC",
            "Russell 2000": "^RUT",
            "VIX": "^VIX"
        }

        # Sector ETFs for sector analysis
        self.sectors = {
            "Technology": "XLK",
            "Healthcare": "XLV",
            "Financials": "XLF",
            "Energy": "XLE",
            "Consumer Discretionary": "XLY",
            "Consumer Staples": "XLP",
            "Industrials": "XLI",
            "Materials": "XLB",
            "Utilities": "XLU",
            "Real Estate": "XLRE",
            "Communication Services": "XLC"
        }

    def process_query(self, query: str) -> str:
        """
        Routes market queries to appropriate analysis functions.
        """
        query_lower = query.lower()

        # Market overview
        if any(k in query_lower for k in ["market overview", "market summary", "how is the market", "market today"]):
            return self.get_market_overview()

        # Sector analysis
        if any(k in query_lower for k in ["sector", "sectors", "industry", "industries"]):
            return self.get_sector_analysis()

        # Technical analysis for specific stock
        if any(k in query_lower for k in ["technical", "moving average", "rsi", "analysis"]):
            # Try to extract ticker
            ticker = self._extract_ticker(query)
            if ticker:
                return self.get_technical_analysis(ticker)
            return "Please specify a stock symbol for technical analysis (e.g., 'technical analysis for AAPL')."

        # Market trends
        if any(k in query_lower for k in ["trend", "trending", "momentum"]):
            return self.get_market_trends()

        # Default: provide market overview with LLM interpretation
        return self.get_market_overview_with_insights(query)

    def get_market_overview(self) -> str:
        """
        Returns current market indices performance.
        """
        report = ["**Market Overview**\n"]

        for name, symbol in self.indices.items():
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.fast_info
                price = info.last_price
                prev_close = info.previous_close
                change_pct = ((price - prev_close) / prev_close) * 100

                # Format with arrow indicator
                arrow = "▲" if change_pct >= 0 else "▼"
                color_indicator = "+" if change_pct >= 0 else ""

                report.append(f"**{name}**: {price:,.2f} {arrow} ({color_indicator}{change_pct:.2f}%)")
            except Exception as e:
                report.append(f"**{name}**: Data unavailable")

        report.append(f"\n*Data as of {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        return "\n".join(report)

    def get_sector_analysis(self) -> str:
        """
        Returns sector performance analysis.
        """
        report = ["**Sector Performance**\n"]
        sector_data = []

        for sector, symbol in self.sectors.items():
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.fast_info
                price = info.last_price
                prev_close = info.previous_close
                change_pct = ((price - prev_close) / prev_close) * 100
                sector_data.append((sector, change_pct))
            except Exception:
                sector_data.append((sector, None))

        # Sort by performance
        sector_data.sort(key=lambda x: x[1] if x[1] is not None else -999, reverse=True)

        for sector, change in sector_data:
            if change is not None:
                arrow = "▲" if change >= 0 else "▼"
                color_indicator = "+" if change >= 0 else ""
                report.append(f"- **{sector}**: {arrow} {color_indicator}{change:.2f}%")
            else:
                report.append(f"- **{sector}**: Data unavailable")

        report.append(f"\n*Data as of {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        return "\n".join(report)

    def get_technical_analysis(self, symbol: str) -> str:
        """
        Returns technical analysis for a specific stock.
        """
        try:
            ticker = yf.Ticker(symbol)

            # Get historical data for calculations
            hist = ticker.history(period="3mo")
            if hist.empty:
                return f"Could not fetch historical data for {symbol}."

            # Current price
            current_price = hist['Close'].iloc[-1]

            # Calculate moving averages
            ma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            ma_50 = hist['Close'].rolling(window=50).mean().iloc[-1]

            # Calculate RSI (14-day)
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]

            # Calculate volatility (20-day standard deviation)
            volatility = hist['Close'].pct_change().rolling(window=20).std().iloc[-1] * 100

            # 52-week high/low
            hist_1y = ticker.history(period="1y")
            high_52w = hist_1y['High'].max() if not hist_1y.empty else None
            low_52w = hist_1y['Low'].min() if not hist_1y.empty else None

            # Build report
            report = [f"**Technical Analysis: {symbol.upper()}**\n"]
            report.append(f"**Current Price**: ${current_price:.2f}")
            report.append(f"\n**Moving Averages**:")
            report.append(f"- 20-day MA: ${ma_20:.2f} {'(Above)' if current_price > ma_20 else '(Below)'}")
            report.append(f"- 50-day MA: ${ma_50:.2f} {'(Above)' if current_price > ma_50 else '(Below)'}")

            report.append(f"\n**RSI (14-day)**: {current_rsi:.1f}")
            if current_rsi > 70:
                report.append("  → *Potentially overbought*")
            elif current_rsi < 30:
                report.append("  → *Potentially oversold*")
            else:
                report.append("  → *Neutral zone*")

            report.append(f"\n**Volatility (20-day)**: {volatility:.2f}%")

            if high_52w and low_52w:
                report.append(f"\n**52-Week Range**: ${low_52w:.2f} - ${high_52w:.2f}")
                position = ((current_price - low_52w) / (high_52w - low_52w)) * 100
                report.append(f"  → Currently at {position:.0f}% of range")

            return "\n".join(report)

        except Exception as e:
            return f"Error performing technical analysis for {symbol}: {e}"

    def get_market_trends(self) -> str:
        """
        Analyzes current market trends based on index movements.
        """
        report = ["**Market Trends Analysis**\n"]

        # Get S&P 500 trend data
        try:
            spy = yf.Ticker("SPY")
            hist = spy.history(period="1mo")

            if not hist.empty:
                # Calculate trend
                start_price = hist['Close'].iloc[0]
                end_price = hist['Close'].iloc[-1]
                month_change = ((end_price - start_price) / start_price) * 100

                # Calculate 5-day trend
                if len(hist) >= 5:
                    week_start = hist['Close'].iloc[-5]
                    week_change = ((end_price - week_start) / week_start) * 100
                else:
                    week_change = 0

                report.append(f"**S&P 500 Trends**:")
                report.append(f"- 1-Week Change: {'+' if week_change >= 0 else ''}{week_change:.2f}%")
                report.append(f"- 1-Month Change: {'+' if month_change >= 0 else ''}{month_change:.2f}%")

                # Trend interpretation
                if month_change > 5:
                    report.append("\n**Trend**: Strong bullish momentum")
                elif month_change > 0:
                    report.append("\n**Trend**: Mild bullish trend")
                elif month_change > -5:
                    report.append("\n**Trend**: Mild bearish trend")
                else:
                    report.append("\n**Trend**: Strong bearish momentum")
        except Exception as e:
            report.append(f"Error analyzing trends: {e}")

        # VIX (Fear index)
        try:
            vix = yf.Ticker("^VIX")
            vix_info = vix.fast_info
            vix_level = vix_info.last_price

            report.append(f"\n**VIX (Volatility Index)**: {vix_level:.2f}")
            if vix_level < 15:
                report.append("  → *Low volatility - Market calm*")
            elif vix_level < 25:
                report.append("  → *Normal volatility*")
            elif vix_level < 35:
                report.append("  → *Elevated volatility - Caution advised*")
            else:
                report.append("  → *High volatility - Market fear*")
        except Exception:
            pass

        return "\n".join(report)

    def get_market_overview_with_insights(self, query: str) -> str:
        """
        Combines market data with LLM insights.
        """
        # Get raw market data
        market_data = self.get_market_overview()
        sector_data = self.get_sector_analysis()

        # Use LLM to provide insights
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a market analyst. Based on the market data provided,
            answer the user's question with clear insights. Be concise and helpful.
            Focus on what matters for retail investors."""),
            ("user", """Current Market Data:
{market_data}

{sector_data}

User Question: {query}

Provide a helpful analysis:""")
        ])

        chain = prompt | self.llm | StrOutputParser()

        try:
            insights = chain.invoke({
                "market_data": market_data,
                "sector_data": sector_data,
                "query": query
            })
            return f"{market_data}\n\n---\n\n**Analysis**:\n{insights}"
        except Exception as e:
            return market_data

    def _extract_ticker(self, query: str) -> Optional[str]:
        """
        Extracts stock ticker from query.
        """
        import re

        # Common company to ticker mapping
        company_mapping = {
            "GOOGLE": "GOOG", "MICROSOFT": "MSFT", "APPLE": "AAPL",
            "AMAZON": "AMZN", "META": "META", "TESLA": "TSLA",
            "NETFLIX": "NFLX", "NVIDIA": "NVDA"
        }

        query_upper = query.upper()
        for company, ticker in company_mapping.items():
            if company in query_upper:
                return ticker

        # Try to find ticker pattern
        common_words = {"WHAT", "HOW", "IS", "THE", "FOR", "OF", "AND", "TECHNICAL", "ANALYSIS"}
        potential = re.findall(r'\b[A-Z]{1,5}\b', query_upper)
        tickers = [t for t in potential if t not in common_words]

        return tickers[0] if tickers else None
