"""
Execution Engine - Core trading execution logic
"""
from datetime import datetime
from typing import Dict, List, Optional
from .order import Order, OrderType, OrderSide, OrderStatus
from .position import Position, ClosedPosition


class ExecutionEngine:
    """
    Handles order execution and position management.
    Simulates trade execution with configurable slippage.
    """
    
    def __init__(self, 
                 initial_capital: float = 10000.0,
                 max_leverage: float = 1.0,
                 slippage_pct: float = 0.001,
                 commission_pct: float = 0.001):
        """
        Initialize execution engine.
        
        Args:
            initial_capital: Starting capital
            max_leverage: Maximum leverage allowed
            slippage_pct: Simulated slippage as percentage (0.001 = 0.1%)
            commission_pct: Commission as percentage per trade
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.max_leverage = max_leverage
        self.slippage_pct = slippage_pct
        self.commission_pct = commission_pct
        
        # Positions and orders tracking
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[ClosedPosition] = []
        self.pending_orders: List[Order] = []
        self.filled_orders: List[Order] = []
        self.all_orders: List[Order] = []
    
    def get_current_position(self, symbol: str) -> Optional[Position]:
        """Get current position for symbol"""
        return self.positions.get(symbol)
    
    def get_position_quantity(self, symbol: str) -> int:
        """Get position quantity for symbol (0 if no position)"""
        pos = self.positions.get(symbol)
        return pos.quantity if pos else 0
    
    def calculate_available_capital(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate available capital for new trades.
        
        Args:
            current_prices: Dictionary of current prices {symbol: price}
            
        Returns:
            Available capital after accounting for margin requirements
        """
        # Calculate total margin used by open positions
        margin_used = 0.0
        for symbol, position in self.positions.items():
            current_price = current_prices.get(symbol, position.entry_price)
            margin_used += position.get_margin_required(current_price)
        
        # Available = cash - margin_used (with leverage consideration)
        # With leverage, we can use more than our cash
        max_buying_power = self.cash * self.max_leverage
        available = max_buying_power - margin_used
        
        return max(available, 0.0)
    
    def apply_slippage(self, price: float, side: OrderSide) -> float:
        """
        Apply slippage to price.
        
        Args:
            price: Original price
            side: Order side
            
        Returns:
            Price with slippage applied
        """
        if side == OrderSide.BUY:
            # Buy orders execute at slightly higher price
            return price * (1 + self.slippage_pct)
        else:
            # Sell orders execute at slightly lower price
            return price * (1 - self.slippage_pct)
    
    def calculate_commission(self, quantity: int, price: float) -> float:
        """
        Calculate trading commission.
        
        Args:
            quantity: Number of shares
            price: Price per share
            
        Returns:
            Commission amount
        """
        trade_value = abs(quantity) * price
        return trade_value * self.commission_pct
    
    def submit_order(self, order: Order) -> bool:
        """
        Submit order for execution.
        
        Args:
            order: Order to submit
            
        Returns:
            True if order accepted, False if rejected
        """
        self.all_orders.append(order)
        self.pending_orders.append(order)
        return True
    
    def execute_market_order(self, 
                            order: Order, 
                            current_price: float,
                            current_prices: Dict[str, float],
                            timestamp: datetime) -> bool:
        """
        Execute market order immediately.
        
        Args:
            order: Order to execute
            current_price: Current market price for this symbol
            current_prices: All current prices for capital calculation
            timestamp: Execution timestamp
            
        Returns:
            True if executed, False if rejected
        """
        # Apply slippage
        execution_price = self.apply_slippage(current_price, order.side)
        
        # Calculate trade value and commission
        trade_value = abs(order.quantity) * execution_price
        commission = self.calculate_commission(order.quantity, execution_price)
        total_cost = trade_value + commission
        
        # Check if we have enough capital
        if order.side == OrderSide.BUY:
            # Buying requires capital
            required_margin = total_cost / self.max_leverage
            available = self.calculate_available_capital(current_prices)
            
            if required_margin > available:
                order.reject()
                return False
        
        # Execute the order
        order.fill(price=execution_price, timestamp=timestamp)
        self.filled_orders.append(order)
        
        if order in self.pending_orders:
            self.pending_orders.remove(order)
        
        # Update positions
        self._update_position_from_order(order, commission)
        
        return True
    
    def _update_position_from_order(self, order: Order, commission: float):
        """Update positions based on filled order"""
        symbol = order.symbol
        quantity = order.quantity if order.side == OrderSide.BUY else -order.quantity
        
        current_pos = self.positions.get(symbol)
        
        if current_pos is None:
            # New position
            self.positions[symbol] = Position(
                symbol=symbol,
                quantity=quantity,
                entry_price=order.fill_price,
                entry_timestamp=order.fill_timestamp,
                leverage=self.max_leverage
            )
            
            # Deduct cost from cash
            cost = abs(quantity) * order.fill_price + commission
            if order.side == OrderSide.BUY:
                self.cash -= cost / self.max_leverage
            else:
                # Short sale adds to cash (minus commission)
                self.cash += (abs(quantity) * order.fill_price - commission) / self.max_leverage
        
        else:
            # Existing position - check if closing or adding
            new_quantity = current_pos.quantity + quantity
            
            if (current_pos.quantity > 0 and quantity < 0) or \
               (current_pos.quantity < 0 and quantity > 0):
                # Closing or reversing position
                
                if abs(quantity) >= abs(current_pos.quantity):
                    # Fully closing or reversing
                    closed = current_pos.close(
                        exit_price=order.fill_price,
                        exit_timestamp=order.fill_timestamp
                    )
                    self.closed_positions.append(closed)
                    
                    # Update cash with realized P&L
                    self.cash += closed.realized_pnl - commission
                    
                    # Remove position
                    del self.positions[symbol]
                    
                    # If reversing, create new position in opposite direction
                    if abs(quantity) > abs(current_pos.quantity):
                        remaining_qty = new_quantity
                        self.positions[symbol] = Position(
                            symbol=symbol,
                            quantity=remaining_qty,
                            entry_price=order.fill_price,
                            entry_timestamp=order.fill_timestamp,
                            leverage=self.max_leverage
                        )
                        # Deduct margin for new position
                        self.cash -= (abs(remaining_qty) * order.fill_price) / self.max_leverage
                else:
                    # Partially closing
                    # Calculate partial P&L
                    partial_pnl = (order.fill_price - current_pos.entry_price) * abs(quantity)
                    if current_pos.quantity < 0:  # Short position
                        partial_pnl = -partial_pnl
                    
                    self.cash += partial_pnl - commission
                    
                    # Update position quantity
                    current_pos.quantity = new_quantity
            else:
                # Adding to position - calculate new average entry price
                old_cost = abs(current_pos.quantity) * current_pos.entry_price
                new_cost = abs(quantity) * order.fill_price
                total_quantity = abs(current_pos.quantity) + abs(quantity)
                
                current_pos.entry_price = (old_cost + new_cost) / total_quantity
                current_pos.quantity = new_quantity
                
                # Deduct additional margin
                self.cash -= (abs(quantity) * order.fill_price + commission) / self.max_leverage
    
    def get_total_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate total portfolio value including unrealized P&L.
        
        Args:
            current_prices: Dictionary of current prices
            
        Returns:
            Total portfolio value
        """
        total_unrealized = 0.0
        for symbol, position in self.positions.items():
            current_price = current_prices.get(symbol, position.entry_price)
            total_unrealized += position.calculate_unrealized_pnl(current_price)
        
        return self.cash + total_unrealized
    
    def get_total_realized_pnl(self) -> float:
        """Get total realized P&L from all closed trades"""
        return sum(cp.realized_pnl for cp in self.closed_positions)
    
    def get_total_unrealized_pnl(self, current_prices: Dict[str, float]) -> float:
        """Get total unrealized P&L from all open positions"""
        total = 0.0
        for symbol, position in self.positions.items():
            current_price = current_prices.get(symbol, position.entry_price)
            total += position.calculate_unrealized_pnl(current_price)
        return total

