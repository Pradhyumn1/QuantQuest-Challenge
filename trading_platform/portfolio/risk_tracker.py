"""
Risk Tracker - Track risk metrics and margin usage
"""
from typing import Dict, List, Tuple
from datetime import datetime
from ..engine.position import Position
from ..engine.execution_engine import ExecutionEngine


class RiskTracker:
    """
    Tracks portfolio risk metrics including margin usage, exposure, and drawdown.
    """
    
    def __init__(self, execution_engine: ExecutionEngine):
        """
        Initialize risk tracker.
        
        Args:
            execution_engine: Reference to execution engine
        """
        self.engine = execution_engine
        self.peak_equity = execution_engine.initial_capital
        self.equity_history: List[Tuple[datetime, float]] = []
    
    def update_equity_history(self, timestamp: datetime, current_prices: Dict[str, float]):
        """
        Update equity history for drawdown calculation.
        
        Args:
            timestamp: Current timestamp
            current_prices: Dictionary of current prices
        """
        equity = self.engine.get_total_portfolio_value(current_prices)
        self.equity_history.append((timestamp, equity))
        
        # Update peak equity
        if equity > self.peak_equity:
            self.peak_equity = equity
    
    def get_margin_used(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate total margin used by open positions.
        
        Args:
            current_prices: Dictionary of current prices
            
        Returns:
            Total margin used in dollars
        """
        margin_used = 0.0
        for symbol, position in self.engine.positions.items():
            current_price = current_prices.get(symbol, position.entry_price)
            margin_used += position.get_margin_required(current_price)
        
        return margin_used
    
    def get_available_margin(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate available margin for new trades.
        
        Args:
            current_prices: Dictionary of current prices
            
        Returns:
            Available margin in dollars
        """
        return self.engine.calculate_available_capital(current_prices)
    
    def get_margin_utilization(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate margin utilization percentage.
        
        Args:
            current_prices: Dictionary of current prices
            
        Returns:
            Margin utilization as percentage (0-100+)
        """
        margin_used = self.get_margin_used(current_prices)
        total_capital = self.engine.cash * self.engine.max_leverage
        
        if total_capital == 0:
            return 0.0
        
        return (margin_used / total_capital) * 100
    
    def get_total_exposure(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate total portfolio exposure (sum of all position values).
        
        Args:
            current_prices: Dictionary of current prices
            
        Returns:
            Total exposure in dollars
        """
        total_exposure = 0.0
        for symbol, position in self.engine.positions.items():
            current_price = current_prices.get(symbol, position.entry_price)
            total_exposure += position.get_position_value(current_price)
        
        return total_exposure
    
    def get_exposure_by_asset(self, current_prices: Dict[str, float]) -> Dict[str, float]:
        """
        Get exposure breakdown by asset.
        
        Args:
            current_prices: Dictionary of current prices
            
        Returns:
            Dictionary mapping symbol to exposure
        """
        exposure = {}
        for symbol, position in self.engine.positions.items():
            current_price = current_prices.get(symbol, position.entry_price)
            exposure[symbol] = position.get_position_value(current_price)
        
        return exposure
    
    def get_unrealized_pnl(self, current_prices: Dict[str, float]) -> float:
        """
        Get total unrealized P&L.
        
        Args:
            current_prices: Dictionary of current prices
            
        Returns:
            Total unrealized P&L
        """
        return self.engine.get_total_unrealized_pnl(current_prices)
    
    def get_unrealized_pnl_by_asset(self, current_prices: Dict[str, float]) -> Dict[str, float]:
        """
        Get unrealized P&L breakdown by asset.
        
        Args:
            current_prices: Dictionary of current prices
            
        Returns:
            Dictionary mapping symbol to unrealized P&L
        """
        pnl = {}
        for symbol, position in self.engine.positions.items():
            current_price = current_prices.get(symbol, position.entry_price)
            pnl[symbol] = position.calculate_unrealized_pnl(current_price)
        
        return pnl
    
    def get_realized_pnl(self) -> float:
        """
        Get total realized P&L.
        
        Returns:
            Total realized P&L
        """
        return self.engine.get_total_realized_pnl()
    
    def get_max_drawdown(self) -> Tuple[float, float]:
        """
        Calculate maximum drawdown from equity history.
        
        Returns:
            Tuple of (max_drawdown_dollars, max_drawdown_percentage)
        """
        if not self.equity_history:
            return (0.0, 0.0)
        
        max_dd_dollars = 0.0
        max_dd_pct = 0.0
        peak = self.engine.initial_capital
        
        for timestamp, equity in self.equity_history:
            if equity > peak:
                peak = equity
            
            drawdown = peak - equity
            drawdown_pct = (drawdown / peak * 100) if peak > 0 else 0.0
            
            if drawdown > max_dd_dollars:
                max_dd_dollars = drawdown
                max_dd_pct = drawdown_pct
        
        return (max_dd_dollars, max_dd_pct)
    
    def get_current_drawdown(self, current_prices: Dict[str, float]) -> Tuple[float, float]:
        """
        Calculate current drawdown from peak equity.
        
        Args:
            current_prices: Dictionary of current prices
            
        Returns:
            Tuple of (current_drawdown_dollars, current_drawdown_percentage)
        """
        current_equity = self.engine.get_total_portfolio_value(current_prices)
        drawdown = self.peak_equity - current_equity
        drawdown_pct = (drawdown / self.peak_equity * 100) if self.peak_equity > 0 else 0.0
        
        return (drawdown, drawdown_pct)
    
    def get_risk_summary(self, current_prices: Dict[str, float]) -> dict:
        """
        Get comprehensive risk summary.
        
        Args:
            current_prices: Dictionary of current prices
            
        Returns:
            Dictionary with risk metrics
        """
        margin_used = self.get_margin_used(current_prices)
        available_margin = self.get_available_margin(current_prices)
        margin_utilization = self.get_margin_utilization(current_prices)
        total_exposure = self.get_total_exposure(current_prices)
        exposure_by_asset = self.get_exposure_by_asset(current_prices)
        unrealized_pnl = self.get_unrealized_pnl(current_prices)
        unrealized_pnl_by_asset = self.get_unrealized_pnl_by_asset(current_prices)
        realized_pnl = self.get_realized_pnl()
        max_dd = self.get_max_drawdown()
        current_dd = self.get_current_drawdown(current_prices)
        
        return {
            'margin_used': margin_used,
            'available_margin': available_margin,
            'margin_utilization_pct': margin_utilization,
            'total_exposure': total_exposure,
            'exposure_by_asset': exposure_by_asset,
            'unrealized_pnl_total': unrealized_pnl,
            'unrealized_pnl_by_asset': unrealized_pnl_by_asset,
            'realized_pnl': realized_pnl,
            'max_drawdown_dollars': max_dd[0],
            'max_drawdown_pct': max_dd[1],
            'current_drawdown_dollars': current_dd[0],
            'current_drawdown_pct': current_dd[1]
        }
    
    def print_risk_report(self, current_prices: Dict[str, float]):
        """
        Print formatted risk report.
        
        Args:
            current_prices: Dictionary of current prices
        """
        summary = self.get_risk_summary(current_prices)
        
        print("=" * 60)
        print("RISK METRICS REPORT")
        print("=" * 60)
        
        print("\n--- Margin Status ---")
        print(f"Margin Used:        ${summary['margin_used']:>12,.2f}")
        print(f"Available Margin:   ${summary['available_margin']:>12,.2f}")
        print(f"Margin Utilization: {summary['margin_utilization_pct']:>12.2f}%")
        
        print("\n--- Portfolio Exposure ---")
        print(f"Total Exposure:     ${summary['total_exposure']:>12,.2f}")
        
        if summary['exposure_by_asset']:
            print("\nPer-Asset Exposure:")
            for symbol, exposure in summary['exposure_by_asset'].items():
                print(f"  {symbol:8s} ${exposure:>12,.2f}")
        
        print("\n--- Profit & Loss ---")
        unrealized_sign = "+" if summary['unrealized_pnl_total'] >= 0 else ""
        realized_sign = "+" if summary['realized_pnl'] >= 0 else ""
        print(f"Unrealized P&L:     {unrealized_sign}${summary['unrealized_pnl_total']:>12,.2f}")
        print(f"Realized P&L:       {realized_sign}${summary['realized_pnl']:>12,.2f}")
        
        if summary['unrealized_pnl_by_asset']:
            print("\nPer-Asset Unrealized P&L:")
            for symbol, pnl in summary['unrealized_pnl_by_asset'].items():
                sign = "+" if pnl >= 0 else ""
                print(f"  {symbol:8s} {sign}${pnl:>12,.2f}")
        
        print("\n--- Drawdown ---")
        print(f"Max Drawdown:       ${summary['max_drawdown_dollars']:>12,.2f} ({summary['max_drawdown_pct']:.2f}%)")
        print(f"Current Drawdown:   ${summary['current_drawdown_dollars']:>12,.2f} ({summary['current_drawdown_pct']:.2f}%)")
        
        print("=" * 60)

