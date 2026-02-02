"""Portfolio Analysis Agent."""

from finnie.agents.base import BaseAgent, AgentType, AgentRequest, AgentResponse
from finnie.observability import log_with_trace


class PortfolioAnalysisAgent(BaseAgent):
    """Agent for analyzing investment portfolios."""
    
    def __init__(self):
        super().__init__(AgentType.PORTFOLIO_ANALYSIS)
    
    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Process a portfolio analysis request.
        
        Args:
            request: The agent request
            
        Returns:
            AgentResponse with portfolio analysis
        """
        if not self.validate_request(request):
            raise ValueError("Invalid request")
        
        log_with_trace(
            f"Processing portfolio analysis: {request.query}",
            trace_id=request.trace_id
        )
        
        # Extract portfolio data from context
        portfolio = request.context.get("portfolio", {})
        
        # Perform analysis
        analysis = self._analyze_portfolio(portfolio, request.query)
        
        return AgentResponse(
            response=analysis,
            agent_type=self.agent_type,
            trace_id=request.trace_id,
            metadata={
                "portfolio_size": len(portfolio),
                "query": request.query,
            },
            confidence=0.85,
        )
    
    def _analyze_portfolio(self, portfolio: dict, query: str) -> str:
        """
        Analyze a portfolio based on the query.
        
        Args:
            portfolio: Portfolio data
            query: User's query
            
        Returns:
            Analysis result as text
        """
        if not portfolio:
            return """To analyze your portfolio, please provide your holdings in the following format:
            
Portfolio:
- Stock: AAPL, Shares: 10, Price: $150
- Stock: GOOGL, Shares: 5, Price: $120
- Bond: US Treasury, Value: $10,000

I can then provide:
• Asset allocation analysis
• Risk assessment
• Diversification recommendations
• Performance metrics"""
        
        # Simple portfolio analysis template
        total_stocks = portfolio.get("stocks", [])
        total_bonds = portfolio.get("bonds", [])
        
        analysis_parts = [
            "Portfolio Analysis Summary:",
            f"\n• Total Stock Positions: {len(total_stocks)}",
            f"• Total Bond Positions: {len(total_bonds)}",
            "\n\nKey Insights:",
            "• Consider diversification across sectors",
            "• Review asset allocation based on risk tolerance",
            "• Monitor portfolio performance regularly",
        ]
        
        return "\n".join(analysis_parts)
