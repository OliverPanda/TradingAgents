# TradingAgents/graph/propagation.py

from typing import Dict, Any
from tradingagents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)


class Propagator:
    """Handles state initialization and propagation through the graph."""

    def __init__(self, max_recur_limit=100):
        """Initialize with configuration parameters."""
        self.max_recur_limit = max_recur_limit

    def create_initial_state(
        self, company_name: str, trade_date: str, stock_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create the initial state for the agent graph."""
        # 如果有股票信息，使用正确的公司名称
        if stock_info and 'name' in stock_info:
            actual_company_name = stock_info['name']
            company_description = f"{actual_company_name} ({company_name})"
        else:
            actual_company_name = company_name
            company_description = company_name
        
        return {
            "messages": [("human", company_description)],
            "company_of_interest": company_description,
            "ticker": company_name,  # 添加股票代码字段
            "company_name": actual_company_name,  # 添加公司名称字段
            "trade_date": str(trade_date),
            "investment_debate_state": InvestDebateState(
                {"history": "", "current_response": "", "count": 0}
            ),
            "risk_debate_state": RiskDebateState(
                {
                    "history": "",
                    "current_risky_response": "",
                    "current_safe_response": "",
                    "current_neutral_response": "",
                    "count": 0,
                }
            ),
            "market_report": "",
            "fundamentals_report": "",
            "sentiment_report": "",
            "news_report": "",
        }

    def get_graph_args(self) -> Dict[str, Any]:
        """Get arguments for the graph invocation."""
        return {
            "stream_mode": "values",
            "config": {"recursion_limit": self.max_recur_limit},
        }
