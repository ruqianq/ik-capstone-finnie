"""Goal Planning Agent."""

from finnie.agents.base import BaseAgent, AgentType, AgentRequest, AgentResponse
from finnie.observability import log_with_trace


class GoalPlanningAgent(BaseAgent):
    """Agent for financial goal planning and tracking."""
    
    def __init__(self):
        super().__init__(AgentType.GOAL_PLANNING)
    
    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Process a goal planning request.
        
        Args:
            request: The agent request
            
        Returns:
            AgentResponse with goal planning advice
        """
        if not self.validate_request(request):
            raise ValueError("Invalid request")
        
        log_with_trace(
            f"Processing goal planning: {request.query}",
            trace_id=request.trace_id
        )
        
        # Extract goal information from context
        goals = request.context.get("goals", [])
        
        # Generate planning advice
        advice = self._generate_goal_plan(request.query, goals)
        
        return AgentResponse(
            response=advice,
            agent_type=self.agent_type,
            trace_id=request.trace_id,
            metadata={
                "num_goals": len(goals),
                "query": request.query,
            },
            confidence=0.85,
        )
    
    def _generate_goal_plan(self, query: str, goals: list) -> str:
        """
        Generate a goal planning response.
        
        Args:
            query: User's query
            goals: User's financial goals
            
        Returns:
            Goal planning advice as text
        """
        query_lower = query.lower()
        
        if "retirement" in query_lower:
            return """Retirement Planning Guide:

**Key Steps:**
1. Calculate Target Amount
   • Estimate annual expenses in retirement
   • Multiply by expected years (typically 25-30)
   • Factor in inflation (3% average)

2. Retirement Accounts
   • 401(k): Maximize employer match
   • IRA/Roth IRA: Additional tax-advantaged savings
   • Target Date Funds: Age-appropriate allocation

3. Investment Strategy
   • Early Career: 80-90% stocks, 10-20% bonds
   • Mid Career: 70-80% stocks, 20-30% bonds
   • Near Retirement: 50-60% stocks, 40-50% bonds

4. Action Items
   • Review annually and adjust contributions
   • Rebalance portfolio quarterly
   • Monitor progress toward target"""
        
        elif any(term in query_lower for term in ["house", "home", "property"]):
            return """Home Purchase Planning:

**Financial Preparation:**
1. Down Payment Goal
   • Target: 20% of home price (avoid PMI)
   • Example: $400k home = $80k down payment
   
2. Credit Score
   • Target: 740+ for best rates
   • Check credit report regularly
   
3. Monthly Budget
   • Housing: Max 28% of gross income
   • Total Debt: Max 36% of gross income
   
4. Emergency Fund
   • Save 6 months expenses first
   • Separate from down payment savings
   
5. Timeline
   • Set realistic target date
   • Automate savings monthly
   • Consider high-yield savings account"""
        
        elif "education" in query_lower or "college" in query_lower:
            return """Education Savings Planning:

**Savings Options:**
1. 529 Plan
   • Tax-advantaged education savings
   • State tax deductions available
   • Flexible beneficiary changes

2. Investment Timeline
   • 0-10 years: Aggressive growth
   • 10-15 years: Balanced approach
   • 15-18 years: Conservative preservation

3. Contribution Strategy
   • Start early - compound growth matters
   • Regular monthly contributions
   • Consider gift contributions

4. Estimated Costs
   • Public University: ~$25k/year
   • Private University: ~$55k/year
   • Factor in 5% annual inflation"""
        
        else:
            return """Financial Goal Planning Framework:

**Common Financial Goals:**
• Emergency Fund (3-6 months expenses)
• Retirement Savings
• Home Purchase
• Education Funding
• Debt Payoff
• Vacation/Travel

**Planning Process:**
1. Define specific goals with timelines
2. Calculate required amount
3. Determine monthly savings needed
4. Choose appropriate investment vehicles
5. Monitor progress regularly
6. Adjust as circumstances change

Please specify your goal for personalized guidance:
• "retirement planning"
• "buying a house"
• "education savings"
• "building emergency fund" """
