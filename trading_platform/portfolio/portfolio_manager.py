"""
Portfolio Manager - Track portfolio state across multiple assets
"""
from typing import Dict, List
from datetime import datetime
from ..engine.position import Position
from ..engine.execution_engine import ExecutionEngine


class PortfolioManager:
    """
    Manages overall portfolio state and provides high-level portfolio metrics.
    """
    
    def __init__(self, execution_engine: ExecutionEngine):
        """
        Initialize portfolio manager.
        
        Args:
            execution_engine: Reference to execution engine
        """
        self.engine = execution_engine
    
    def get_total_value(self, current_prices: Dict[str, float]) -> float:
        """
        Get total portfolio value.
        
        Args:
            current_prices: Dictionary of current prices
            
        Returns:
            Total portfolio value (cash + unrealized P&L)
        """
        return self.engine.get_total_portfolio_value(current_prices)
    
    def get_cash_balance(self) -> float:
        """Get current cash balance"""
        return self.engine.cash
    
    def get_equity(self, current_prices: Dict[str, float]) -> float:
        """
        Get portfolio equity (same as total value).
        
        Args:
            current_prices: Dictionary of current prices
            
        Returns:
            Portfolio equity
        """
        return self.get_total_value(current_prices)
    
    def get_total_pnl(self, current_prices: Dict[str, float]) -> float:
        """
        Get total P&L (realized + unrealized).
        
        Args:
            current_prices: Dictionary of current prices
            
        Returns:
            Total P&L
        """
        realized = self.engine.get_total_realized_pnl()
        unrealized = self.engine.get_total_unrealized_pnl(current_prices)
        return realized + unrealized
    
    def get_total_pnl_percentage(self, current_prices: Dict[str, float]) -> float:
        """
        Get total P&L as percentage of initial capital.
        
        Args:
            current_prices: Dictionary of current prices
            
        Returns:
            Total P&L percentage
        """
        total_pnl = self.get_total_pnl(current_prices)
        return (total_pnl / self.engine.initial_capital) * 100
    
    def get_position_count(self) -> int:
        """Get number of open positions"""
        return len(self.engine.positions)
    
    def get_positions(self) -> Dict[str, Position]:
        """Get all open positions"""
        return self.engine.positions.copy()
    
    def get_closed_trade_count(self) -> int:
        """Get number of closed trades"""
        return len(self.engine.closed_positions)
    
    def get_win_rate(self) -> float:
        """
        Calculate win rate from closed positions.
        
        Returns:
            Win rate as percentage (0-100)
        """
        if not self.engine.closed_positions:
            return 0.0
        
        wins = sum(1 for cp in self.engine.closed_positions if cp.is_profitable())
        return (wins / len(self.engine.closed_positions)) * 100
    
    def get_average_win(self) -> float:
        """Get average profit from winning trades"""
        wins = [cp.realized_pnl for cp in self.engine.closed_positions if cp.is_profitable()]
        return sum(wins) / len(wins) if wins else 0.0
    
    def get_average_loss(self) -> float:
        """Get average loss from losing trades"""
        losses = [cp.realized_pnl for cp in self.engine.closed_positions if not cp.is_profitable()]
        return sum(losses) / len(losses) if losses else 0.0
    
    def get_profit_factor(self) -> float:
        """
        Calculate profit factor (gross profit / gross loss).
        
        Returns:
            Profit factor (>1 means profitable overall)
        """
        gross_profit = sum(cp.realized_pnl for cp in self.engine.closed_positions if cp.is_profitable())
        gross_loss = abs(sum(cp.realized_pnl for cp in self.engine.closed_positions if not cp.is_profitable()))
        
        return gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    def get_portfolio_summary(self, current_prices: Dict[str, float]) -> dict:
        """
        Get comprehensive portfolio summary.
        
        Args:
            current_prices: Dictionary of current prices
            
        Returns:
            Dictionary with portfolio metrics
        """
        total_value = self.get_total_value(current_prices)
        realized_pnl = self.engine.get_total_realized_pnl()
        unrealized_pnl = self.engine.get_total_unrealized_pnl(current_prices)
        total_pnl = self.get_total_pnl(current_prices)
        total_pnl_pct = self.get_total_pnl_percentage(current_prices)
        
        return {
            'initial_capital': self.engine.initial_capital,
            'cash': self.engine.cash,
            'total_value': total_value,
            'realized_pnl': realized_pnl,
            'unrealized_pnl': unrealized_pnl,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'open_positions': self.get_position_count(),
            'closed_trades': self.get_closed_trade_count(),
            'win_rate': self.get_win_rate(),
            'profit_factor': self.get_profit_factor()
        }

