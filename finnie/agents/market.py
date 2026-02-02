"""Market Analysis Agent."""

from finnie.agents.base import BaseAgent, AgentType, AgentRequest, AgentResponse
from finnie.observability import log_with_trace


class MarketAnalysisAgent(BaseAgent):
    """Agent for market data analysis and trends."""
    
    def __init__(self):
        super().__init__(AgentType.MARKET_ANALYSIS)
    
    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Process a market analysis request.
        
        Args:
            request: The agent request
            
        Returns:
            AgentResponse with market analysis
        """
        if not self.validate_request(request):
            raise ValueError("Invalid request")
        
        log_with_trace(
            f"Processing market analysis: {request.query}",
            trace_id=request.trace_id
        )
        
        # Extract ticker or market info from query
        analysis = self._analyze_market(request.query, request.context)
        
        return AgentResponse(
            response=analysis,
            agent_type=self.agent_type,
            trace_id=request.trace_id,
            metadata={
                "query": request.query,
                "market_data_source": "mock",
            },
            confidence=0.80,
        )
    
    def _analyze_market(self, query: str, context: dict) -> str:
        """
        Analyze market data based on the query.
        
        Args:
            query: User's query
            context: Additional context
            
        Returns:
            Market analysis as text
        """
        # Simple market analysis template
        # In production, this would fetch real market data via yfinance or Alpha Vantage
        
        query_lower = query.lower()
        
        if any(ticker in query_lower for ticker in ["aapl", "apple"]):
            return """Market Analysis for Apple Inc. (AAPL):

• Current Performance: Strong momentum with consistent growth
• Key Metrics: P/E ratio indicates reasonable valuation
• Sector: Technology - showing robust fundamentals
• Recommendation: Consider as part of diversified tech portfolio

Note: This is a template response. Real-time data integration coming soon."""
        
        elif any(term in query_lower for term in ["sp500", "s&p", "market index"]):
            return """S&P 500 Market Overview:

• Broad Market Trend: Monitoring key support/resistance levels
• Sector Performance: Technology and Healthcare leading
• Market Sentiment: Balanced with mixed signals
• Economic Indicators: Consider Fed policy and inflation data

For specific stocks, please provide ticker symbols."""
        
        else:
            return """Market Analysis:

To provide detailed market analysis, please specify:
• Stock ticker symbol (e.g., AAPL, GOOGL, MSFT)
• Market index (e.g., S&P 500, NASDAQ)
• Sector or industry

I can provide:
• Current price and trends
• Technical indicators
• Sector comparisons
• Market sentiment analysis"""
