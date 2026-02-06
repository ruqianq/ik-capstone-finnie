import yfinance as yf
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import List, Dict, Optional
from datetime import datetime
import re


class NewsSynthesizerAgent:
    """
    Agent for aggregating and synthesizing financial news.
    Uses yfinance for stock-specific news and LLM for summarization.
    """

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        # Major tickers to track for general market news
        self.market_tickers = ["SPY", "QQQ", "DIA", "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]

    def process_query(self, query: str) -> str:
        """
        Routes news queries to appropriate functions.
        """
        query_lower = query.lower()

        # Stock-specific news
        ticker = self._extract_ticker(query)
        if ticker:
            return self.get_stock_news(ticker)

        # Market news
        if any(k in query_lower for k in ["market news", "today's news", "latest news", "financial news"]):
            return self.get_market_news()

        # Sector news
        if "sector" in query_lower:
            return self.get_sector_news(query)

        # Default: general market news
        return self.get_market_news()

    def _extract_news_fields(self, item: Dict) -> Dict:
        """
        Extracts news fields handling both old and new yfinance formats.
        """
        # Try new format first (yfinance >= 0.2.40)
        if 'content' in item:
            content = item.get('content', {})
            title = content.get('title', 'No title')
            provider = content.get('provider', {})
            publisher = provider.get('displayName', 'Unknown')
            link = content.get('canonicalUrl', {}).get('url', '')
            pub_date_str = content.get('pubDate', '')

            # Parse ISO date string
            if pub_date_str:
                try:
                    pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                    timestamp = pub_date.timestamp()
                except Exception:
                    timestamp = 0
            else:
                timestamp = 0

            return {
                'title': title,
                'publisher': publisher,
                'link': link,
                'timestamp': timestamp
            }

        # Fall back to old format
        return {
            'title': item.get('title', 'No title'),
            'publisher': item.get('publisher', 'Unknown'),
            'link': item.get('link', ''),
            'timestamp': item.get('providerPublishTime', 0)
        }

    def get_stock_news(self, symbol: str, limit: int = 5) -> str:
        """
        Fetches and summarizes news for a specific stock.
        """
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news

            if not news:
                return f"No recent news found for {symbol.upper()}."

            # Get top news items
            news_items = news[:limit]

            report = [f"**Latest News for {symbol.upper()}**\n"]

            articles_text = []
            for i, item in enumerate(news_items, 1):
                fields = self._extract_news_fields(item)
                title = fields['title']
                publisher = fields['publisher']
                link = fields['link']
                timestamp = fields['timestamp']

                # Format timestamp
                if timestamp:
                    pub_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
                else:
                    pub_date = 'Unknown date'

                report.append(f"**{i}. {title}**")
                report.append(f"   *{publisher} - {pub_date}*")
                if link:
                    report.append(f"   [Read more]({link})")
                report.append("")

                articles_text.append(f"- {title}")

            # Add LLM synthesis
            if articles_text:
                synthesis = self._synthesize_news(symbol, articles_text)
                if synthesis:
                    report.append("---")
                    report.append(f"\n**Summary**: {synthesis}")

            return "\n".join(report)

        except Exception as e:
            return f"Error fetching news for {symbol}: {e}"

    def get_market_news(self) -> str:
        """
        Aggregates news from major market tickers for a market overview.
        """
        report = ["**Market News Summary**\n"]
        all_news = []

        # Collect news from major tickers
        for symbol in self.market_tickers[:4]:  # Limit to avoid too many API calls
            try:
                ticker = yf.Ticker(symbol)
                news = ticker.news
                if news:
                    for item in news[:2]:  # Top 2 from each
                        fields = self._extract_news_fields(item)
                        fields['related_symbol'] = symbol
                        all_news.append(fields)
            except Exception:
                continue

        if not all_news:
            return "Unable to fetch market news at this time."

        # Sort by timestamp (most recent first)
        all_news.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

        # Deduplicate by title
        seen_titles = set()
        unique_news = []
        for item in all_news:
            title = item.get('title', '')
            if title and title != 'No title' and title not in seen_titles:
                seen_titles.add(title)
                unique_news.append(item)

        # Display top news
        for i, item in enumerate(unique_news[:8], 1):
            title = item.get('title', 'No title')
            publisher = item.get('publisher', 'Unknown')
            related = item.get('related_symbol', '')

            timestamp = item.get('timestamp', 0)
            if timestamp:
                pub_date = datetime.fromtimestamp(timestamp).strftime('%m/%d %H:%M')
            else:
                pub_date = ''

            report.append(f"**{i}.** {title}")
            report.append(f"   *{publisher}* | {pub_date} | ${related}")
            report.append("")

        # Add market sentiment summary
        sentiment = self._analyze_market_sentiment(unique_news[:8])
        if sentiment:
            report.append("---")
            report.append(f"\n**Market Sentiment**: {sentiment}")

        report.append(f"\n*Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
        return "\n".join(report)

    def get_sector_news(self, query: str) -> str:
        """
        Gets news for a specific sector based on sector ETFs.
        """
        # Map query to sector ETF
        sector_etfs = {
            "tech": "XLK", "technology": "XLK",
            "health": "XLV", "healthcare": "XLV",
            "finance": "XLF", "financial": "XLF", "bank": "XLF",
            "energy": "XLE", "oil": "XLE",
            "consumer": "XLY",
            "industrial": "XLI",
            "real estate": "XLRE", "realty": "XLRE"
        }

        query_lower = query.lower()
        selected_etf = None
        sector_name = None

        for keyword, etf in sector_etfs.items():
            if keyword in query_lower:
                selected_etf = etf
                sector_name = keyword.title()
                break

        if selected_etf:
            # Get news for representative stocks in that sector
            sector_stocks = {
                "XLK": ["AAPL", "MSFT", "NVDA"],
                "XLV": ["JNJ", "UNH", "PFE"],
                "XLF": ["JPM", "BAC", "GS"],
                "XLE": ["XOM", "CVX", "COP"],
                "XLY": ["AMZN", "TSLA", "HD"],
                "XLI": ["CAT", "BA", "HON"],
                "XLRE": ["PLD", "AMT", "SPG"]
            }

            stocks = sector_stocks.get(selected_etf, [])
            report = [f"**{sector_name} Sector News**\n"]

            all_news = []
            for stock in stocks:
                try:
                    ticker = yf.Ticker(stock)
                    news = ticker.news
                    if news:
                        for item in news[:2]:
                            fields = self._extract_news_fields(item)
                            fields['related_symbol'] = stock
                            all_news.append(fields)
                except Exception:
                    continue

            if not all_news:
                return f"No recent news found for {sector_name} sector."

            # Deduplicate and sort
            seen = set()
            unique = []
            for item in sorted(all_news, key=lambda x: x.get('timestamp', 0), reverse=True):
                title = item.get('title', '')
                if title and title != 'No title' and title not in seen:
                    seen.add(title)
                    unique.append(item)

            for i, item in enumerate(unique[:6], 1):
                title = item.get('title', 'No title')
                publisher = item.get('publisher', 'Unknown')
                related = item.get('related_symbol', '')
                report.append(f"**{i}.** {title}")
                report.append(f"   *{publisher}* | ${related}")
                report.append("")

            return "\n".join(report)

        return "Please specify a sector (e.g., 'tech sector news', 'healthcare sector news')."

    def _synthesize_news(self, symbol: str, articles: List[str]) -> Optional[str]:
        """
        Uses LLM to synthesize news headlines into a brief summary.
        """
        if not articles:
            return None

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a financial news analyst. Summarize the following news headlines
            for {symbol} in 2-3 sentences. Focus on the key themes and potential market impact.
            Be objective and concise."""),
            ("user", "Headlines:\n{headlines}")
        ])

        chain = prompt | self.llm | StrOutputParser()

        try:
            return chain.invoke({
                "symbol": symbol,
                "headlines": "\n".join(articles)
            })
        except Exception:
            return None

    def _analyze_market_sentiment(self, news_items: List[Dict]) -> Optional[str]:
        """
        Analyzes overall market sentiment from news headlines.
        """
        if not news_items:
            return None

        headlines = [item.get('title', '') for item in news_items if item.get('title')]
        if not headlines:
            return None

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a market sentiment analyst. Based on these headlines,
            provide a brief (1-2 sentence) assessment of the current market sentiment.
            Categorize as Bullish, Bearish, or Mixed, then explain briefly."""),
            ("user", "Headlines:\n{headlines}")
        ])

        chain = prompt | self.llm | StrOutputParser()

        try:
            return chain.invoke({"headlines": "\n".join(headlines)})
        except Exception:
            return None

    def _extract_ticker(self, query: str) -> Optional[str]:
        """
        Extracts stock ticker from query.
        """
        # Company name mapping
        company_mapping = {
            "GOOGLE": "GOOGL", "MICROSOFT": "MSFT", "APPLE": "AAPL",
            "AMAZON": "AMZN", "META": "META", "TESLA": "TSLA",
            "NETFLIX": "NFLX", "NVIDIA": "NVDA", "FACEBOOK": "META"
        }

        query_upper = query.upper()
        for company, ticker in company_mapping.items():
            if company in query_upper:
                return ticker

        # Try to find ticker pattern
        common_words = {
            "NEWS", "WHAT", "HOW", "IS", "THE", "FOR", "OF", "AND",
            "LATEST", "RECENT", "TODAY", "ABOUT", "SHOW", "GET", "ME"
        }
        potential = re.findall(r'\b[A-Z]{1,5}\b', query_upper)
        tickers = [t for t in potential if t not in common_words]

        return tickers[0] if tickers else None
