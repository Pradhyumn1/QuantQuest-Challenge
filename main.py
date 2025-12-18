"""Trading Platform - Unified International & Indian Markets"""

import argparse
from datetime import datetime, timedelta
import time
from typing import List, Dict
from tabulate import tabulate

from trading_platform.data.market_generator import MarketDataGenerator
from trading_platform.strategies import (
    RSIStrategy, MACrossoverStrategy, EMAStrategy, CombinedStrategy
)
from trading_platform.engine import ExecutionEngine, Order, OrderType, OrderSide
from trading_platform.portfolio import PortfolioManager, RiskTracker
from trading_platform.market_config import (
    get_lot_size, get_currency_symbol, get_market_type,
    get_all_symbols_by_category, get_symbol_info, MarketType
)


def display_symbol_selection_menu():
    print("\n" + "=" * 80)
    print(" TRADING PLATFORM - SYMBOL SELECTION MENU")
    print("=" * 80)
    print("\nSelect symbols to trade from the following categories:\n")
    
    categories = get_all_symbols_by_category()
    
    for idx, (category, symbols) in enumerate(categories.items(), 1):
        print(f"{idx}. {category}")
        print(f"   Available: {', '.join(symbols)}")
        print()
    
    print("6. Custom Entry (enter your own symbols)")
    print("7. Quick Start - Indian Indices (NIFTY50, SENSEX, BANKNIFTY)")
    print("8. Quick Start - US Stocks (AAPL, GOOGL, MSFT, TSLA)")
    print()
    
    return categories


def get_user_symbol_selection():
    categories = display_symbol_selection_menu()
    category_list = list(categories.items())
    
    while True:
        try:
            choice = input("Enter your choice (1-8): ").strip()
            
            if choice == '6':
                custom = input("Enter comma-separated symbols (e.g., AAPL,TSLA,NIFTY50): ").strip()
                symbols = [s.strip().upper() for s in custom.split(',') if s.strip()]
                if symbols:
                    return symbols
                print("No symbols entered. Try again.\n")
                continue
                    
            elif choice == '7':
                return ['NIFTY50', 'SENSEX', 'BANKNIFTY']
                
            elif choice == '8':
                return ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
                
            elif choice in ['1', '2', '3', '4', '5']:
                idx = int(choice) - 1
                category_name, available_symbols = category_list[idx]
                
                print(f"\nYou selected: {category_name}")
                print(f"Available: {', '.join(available_symbols)}\n")
                
                while True:
                    sub_choice = input("Enter:\n  [1] Trade ALL symbols\n  [2] Choose specific symbols\nYour choice: ").strip()
                    
                    if sub_choice == '1':
                        return available_symbols
                    elif sub_choice == '2':
                        print(f"\nExample: {available_symbols[0]},{available_symbols[1] if len(available_symbols) > 1 else ''}")
                        selected = input(f"Enter symbols from list above (comma-separated): ").strip()
                        symbols = [s.strip().upper() for s in selected.split(',') if s.strip()]
                        valid_symbols = [s for s in symbols if s in available_symbols]
                        
                        if valid_symbols:
                            return valid_symbols
                        
                        invalid = [s for s in symbols if s not in available_symbols]
                        print(f"\nInvalid symbols: {', '.join(invalid)}")
                        print(f"Valid options are: {', '.join(available_symbols)}\n")
                    else:
                        print("Enter 1 or 2\n")
            else:
                print("Invalid choice. Enter 1-8.\n")
                
        except (ValueError, KeyError) as e:
            print(f"Invalid input: {e}\n")
        except KeyboardInterrupt:
            print("\n\nSelection cancelled.")
            exit(0)


def display_market_analysis(symbols):
    """Display market analysis for symbols"""
    from trading_platform.analysis.market_regime import MarketRegimeAnalyzer
    from trading_platform.data.market_generator import OptionChainGenerator, MarketDataGenerator
    from trading_platform.market_config import get_market_type, get_currency_symbol
    
    print("\n" + "=" * 80)
    print("MARKET ANALYSIS - Analyzing Current Conditions...")
    print("=" * 80)
    
    for symbol in symbols:
        generator = MarketDataGenerator(
            initial_price=100.0 + len(symbol) * 10,
            drift=0.0001, volatility=0.02, seed=hash(symbol) % 10000)
        
        initial_data = []
        for i in range(60):
            price = generator.generate_price_tick()
            initial_data.append({
                'timestamp': datetime.now(), 'open': price,
                'high': price * 1.001, 'low': price * 0.999,
                'close': price, 'volume': 1000
            })
        
        analyzer = MarketRegimeAnalyzer(lookback_period=60)
        conditions = analyzer.get_market_conditions(initial_data)
        
        print(f"\n{symbol} - Market Conditions:")
        print(f"   Trend: {conditions['trend']} | ADX: {conditions['adx']:.1f}")
        print(f"   Volatility: {conditions['volatility']:.1f}% | Volume: {conditions['volume']}")
        
        market_type = get_market_type(symbol)
        option_gen = OptionChainGenerator()
        spot = initial_data[-1]['close']
        atm_data = option_gen.get_atm_data(spot, days_to_expiry=30, market_type=market_type)
        currency = get_currency_symbol(symbol)
        
        print(f"\nOptions Greeks (ATM, 30 DTE):")
        print(f"   Spot: {currency}{spot:.2f} | Strike: {currency}{atm_data['atm_strike']:.2f}")
        print(f"   Call: {currency}{atm_data['atm_call_price']:.2f} | Put: {currency}{atm_data['atm_put_price']:.2f}")
        print(f"   Delta: {atm_data['delta']:.4f} | Gamma: {atm_data['gamma']:.6f}")
        print(f"   Vega: {atm_data['vega']:.2f} | Theta: {atm_data['theta']:.2f} | IV: {atm_data['iv']:.1f}%")
    
    print("\n" + "=" * 80)


def get_strategy_selection():
    print(" SELECT TRADING STRATEGY")
    print("=" * 80)
    print("\n1. RSI Strategy - Oversold/Overbought signals")
    print("2. MA Crossover - Moving Average crossovers")
    print("3. EMA Strategy - Exponential MA crossovers")
    print("4. Combined Strategy - Multiple confirmations")
    print("5. Stochastic Oscillator - Perfect for sideways markets")
    print("6. Adaptive Strategy - Auto-selects based on market conditions\n")
    
    while True:
        choice = input("Enter your choice (1-6) or press Enter for Adaptive [6]: ").strip()
        
        if not choice or choice == '6':
            return 'adaptive'
        elif choice == '1':
            return 'rsi'
        elif choice == '2':
            return 'ma'
        elif choice == '3':
            return 'ema'
        elif choice == '4':
            return 'combined'
        elif choice == '5':
            return 'stochastic'
        else:
            print("Invalid choice. Enter 1-6.\n")


def display_symbol_summary(symbols: List[str]):
    """Display summary of selected symbols"""
    print("\n" + "=" * 80)
    print(" SELECTED SYMBOLS - SUMMARY")
    print("=" * 80)
    
    # Group by market type
    indian_symbols = []
    intl_symbols = []
    
    for symbol in symbols:
        market_type = get_market_type(symbol)
        if market_type == MarketType.INDIAN:
            indian_symbols.append(symbol)
        else:
            intl_symbols.append(symbol)
    
    # Display table
    table_data = []
    for symbol in symbols:
        info = get_symbol_info(symbol)
        table_data.append([
            info['symbol'],
            info['market_type'],
            info['lot_size'],
            info['currency'],
            f"{info['margin_requirement']*100:.1f}%",
            info['description'] if info['description'] else 'Index/Stock'
        ])
    
    headers = ["Symbol", "Market", "Lot Size", "Currency", "Margin", "Description"]
    print("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Summary stats
    print(f"\nTotal Symbols: {len(symbols)}")
    print(f"   • Indian Market: {len(indian_symbols)} ({', '.join(indian_symbols) if indian_symbols else 'None'})")
    print(f"   • International: {len(intl_symbols)} ({', '.join(intl_symbols) if intl_symbols else 'None'})")
    print()


class TradingSimulator:
    
    def __init__(self, symbols: List[str], strategy_name: str = "combined",
                 initial_capital: float = 10000.0, max_leverage: float = 2.0,
                 simulation_ticks: int = 500, display_interval: int = 50):
      
        self.symbols = symbols
        self.simulation_ticks = simulation_ticks
        self.display_interval = display_interval
        self.primary_market = get_market_type(symbols[0]) if symbols else MarketType.INDIAN
        self.primary_currency = get_currency_symbol(symbols[0]) if symbols else '₹'
        
        self.engine = ExecutionEngine(
            initial_capital=initial_capital,
            max_leverage=max_leverage,
            slippage_pct=0.001,
            commission_pct=0.001
        )
        self.portfolio = PortfolioManager(self.engine)
        self.risk = RiskTracker(self.engine)
        self.strategy = self._create_strategy(strategy_name)
        
        self.generators = {}
        for symbol in symbols:
            self.generators[symbol] = MarketDataGenerator(
                initial_price=100.0 + len(symbol) * 10,
                drift=0.0001,
                volatility=0.02,
                seed=hash(symbol) % 10000
            )
        
        self.market_data = {symbol: [] for symbol in symbols}
        self.current_prices = {}
    
    def _create_strategy(self, strategy_name: str):
        from trading_platform.strategies import StochasticStrategy, AdaptiveStrategySelector
        
        strategies = {
            'rsi': RSIStrategy(period=14, oversold=30, overbought=70),
            'ma': MACrossoverStrategy(short_period=20, long_period=50),
            'ema': EMAStrategy(short_period=12, long_period=26),
            'combined': CombinedStrategy(
                rsi_period=14, rsi_oversold=30, rsi_overbought=70,
                ema_short=12, ema_long=26, confirmation_threshold=2),
            'stochastic': StochasticStrategy(k_period=14, d_period=3, oversold=20, overbought=80),
            'adaptive': AdaptiveStrategySelector()
        }
        strategy = strategies.get(strategy_name.lower())
        if not strategy:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        return strategy
    
    def run_simulation(self):
        print("\n" + "=" * 80)
        print(f"TRADING PLATFORM - {self.strategy.name} Strategy")
        print("=" * 80)
        print(f"Symbols: {', '.join(self.symbols)}")
        print(f"Primary Market: {self.primary_market}")
        
        lot_info = [f"{s}({get_lot_size(s)})" for s in self.symbols]
        print(f"Lot Sizes: {', '.join(lot_info)}")
        print(f"Initial Capital: {self.primary_currency}{self.engine.initial_capital:,.2f}")
        print(f"Max Leverage: {self.engine.max_leverage}x")
        print(f"Simulation Ticks: {self.simulation_ticks}")
        print("=" * 80 + "\n")
        
        start_time = datetime.now()
        
        for tick in range(self.simulation_ticks):
            current_time =start_time + timedelta(seconds=tick)
            
            for symbol in self.symbols:
                price = self.generators[symbol].generate_price_tick()
                self.current_prices[symbol] = price
                self.market_data[symbol].append({
                    'timestamp': current_time, 'open': price,
                    'high': price * 1.001, 'low': price * 0.999,
                    'close': price, 'volume': 1000
                })
            
            for symbol in self.symbols:
                self._process_symbol_signals(symbol, current_time)
            
            self.risk.update_equity_history(current_time, self.current_prices)
            
            if tick % self.display_interval == 0 or tick == self.simulation_ticks - 1:
                self._display_status(tick, current_time)
        
        self._display_final_summary()
    
    def _process_symbol_signals(self, symbol: str, current_time: datetime):
        """Process trading signals for a symbol"""
        import pandas as pd
        
        # Need sufficient data for strategy
        if len(self.market_data[symbol]) < 60:
            return
        
        # Create DataFrame for strategy
        df = pd.DataFrame(self.market_data[symbol])
        
        # Get current position
        current_position = self.engine.get_position_quantity(symbol)
        
        # Generate signal
        signal = self.strategy.generate_signal(df, symbol, current_position)
        
        # Get currency for this symbol
        currency = get_currency_symbol(symbol)
        
        # Execute trades based on signal
        if signal.signal.value == "BUY" and current_position <= 0:
            # Enter long position
            quantity = self._calculate_position_size(symbol)
            if quantity > 0:
                order = Order(
                    symbol=symbol,
                    side=OrderSide.BUY,
                    quantity=quantity,
                    order_type=OrderType.MARKET,
                    timestamp=current_time
                )
                
                success = self.engine.execute_market_order(
                    order,
                    self.current_prices[symbol],
                    self.current_prices,
                    current_time
                )
                
                if success:
                    print(f"[TRADE] BUY {quantity} {symbol} @ {currency}{order.fill_price:.2f} | {signal.reason}")
        
        elif signal.signal.value == "SELL" and current_position >= 0:
            # Enter short position
            quantity = self._calculate_position_size(symbol)
            if quantity > 0:
                order = Order(
                    symbol=symbol,
                    side=OrderSide.SELL,
                    quantity=quantity,
                    order_type=OrderType.MARKET,
                    timestamp=current_time
                )
                
                success = self.engine.execute_market_order(
                    order,
                    self.current_prices[symbol],
                    self.current_prices,
                    current_time
                )
                
                if success:
                    print(f"[TRADE] SELL {quantity} {symbol} @ {currency}{order.fill_price:.2f} | {signal.reason}")
        
        elif signal.signal.value == "CLOSE" and current_position != 0:
            # Close existing position
            position = self.engine.get_current_position(symbol)
            if position:
                # Create opposite order to close
                close_side = OrderSide.SELL if position.is_long() else OrderSide.BUY
                quantity = abs(position.quantity)
                
                order = Order(
                    symbol=symbol,
                    side=close_side,
                    quantity=quantity,
                    order_type=OrderType.MARKET,
                    timestamp=current_time
                )
                
                success = self.engine.execute_market_order(
                    order,
                    self.current_prices[symbol],
                    self.current_prices,
                    current_time
                )
                
                if success:
                    print(f"[CLOSE] {close_side.value} {quantity} {symbol} @ {currency}{order.fill_price:.2f} | {signal.reason}")
    
    def _calculate_position_size(self, symbol: str) -> int:
        """
        Calculate position size based on available capital and market-specific lot sizes.
        Returns quantity in terms of lots (not individual shares for Indian market).
        """
        available = self.risk.get_available_margin(self.current_prices)
        price = self.current_prices[symbol]
        lot_size = get_lot_size(symbol)
        
        # Calculate contract value per lot
        contract_value_per_lot = price * lot_size
        
        # Use 20% of available capital per trade
        position_value = available * 0.2
        
        # Calculate number of lots
        num_lots = max(1, int(position_value / contract_value_per_lot))
        
        # Return total quantity (lots * lot_size)
        return num_lots * lot_size
    
    def _display_status(self, tick: int, current_time: datetime):
        """Display current status"""
        print(f"\n{'='*80}")
        print(f"Tick {tick}/{self.simulation_ticks} | {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
        # Portfolio summary
        summary = self.portfolio.get_portfolio_summary(self.current_prices)
        
        print("\n--- PORTFOLIO STATUS ---")
        print(f"Initial Capital:  {self.primary_currency}{self.engine.initial_capital:>12,.2f}")
        print(f"Current Value:    {self.primary_currency}{summary['total_value']:>12,.2f}")
        
        # Calculate remaining from initial capital
        remaining_from_initial = summary['total_value']
        remaining_pct = (remaining_from_initial / self.engine.initial_capital - 1) * 100
        remaining_sign = "+" if remaining_pct >= 0 else ""
        
        print(f"Remaining:        {self.primary_currency}{remaining_from_initial:>12,.2f} ({remaining_sign}{remaining_pct:.2f}%)")
        print(f"Cash Available:   {self.primary_currency}{summary['cash']:>12,.2f}")
        
        # P/L breakdown
        total_pnl_sign = "+" if summary['total_pnl'] >= 0 else ""
        print(f"\n--- PROFIT & LOSS ---")
        print(f"Total P&L:        {total_pnl_sign}{self.primary_currency}{summary['total_pnl']:>12,.2f} ({total_pnl_sign}{summary['total_pnl_pct']:.2f}%)")
        
        print(f"\n--- TRADING STATISTICS ---")
        print(f"Open Positions:   {summary['open_positions']:>12}")
        print(f"Closed Trades:    {summary['closed_trades']:>12}")
        if summary['closed_trades'] > 0:
            print(f"Win Rate:         {summary['win_rate']:>12.1f}%")
        
        # Risk metrics
        risk_summary = self.risk.get_risk_summary(self.current_prices)
        
        print("\n--- RISK METRICS ---")
        print(f"Margin Used:      {self.primary_currency}{risk_summary['margin_used']:>12,.2f}")
        print(f"Available Margin: {self.primary_currency}{risk_summary['available_margin']:>12,.2f}")
        print(f"Margin Util:      {risk_summary['margin_utilization_pct']:>12.2f}%")
        print(f"Total Exposure:   {self.primary_currency}{risk_summary['total_exposure']:>12,.2f}")
        
        unrealized_sign = "+" if risk_summary['unrealized_pnl_total'] >= 0 else ""
        realized_sign = "+" if risk_summary['realized_pnl'] >= 0 else ""
        print(f"Unrealized P&L:   {unrealized_sign}{self.primary_currency}{risk_summary['unrealized_pnl_total']:>12,.2f}")
        print(f"Realized P&L:     {realized_sign}{self.primary_currency}{risk_summary['realized_pnl']:>12,.2f}")
        
        # Open positions
        if self.engine.positions:
            print("\n--- OPEN POSITIONS ---")
            position_data = []
            for symbol, position in self.engine.positions.items():
                current_price = self.current_prices[symbol]
                unrealized = position.calculate_unrealized_pnl(current_price)
                unrealized_pct = position.calculate_unrealized_pnl_percentage(current_price)
                side = "LONG" if position.is_long() else "SHORT"
                currency = get_currency_symbol(symbol)
                
                unrealized_sign = "+" if unrealized >= 0 else ""
                position_data.append([
                    symbol,
                    side,
                    abs(position.quantity),
                    f"{currency}{position.entry_price:.2f}",
                    f"{currency}{current_price:.2f}",
                    f"{unrealized_sign}{currency}{unrealized:.2f}",
                    f"{unrealized_sign}{unrealized_pct:.2f}%"
                ])
            
            headers = ["Symbol", "Side", "Qty", "Entry", "Current", "P&L", "P&L %"]
            print(tabulate(position_data, headers=headers, tablefmt="simple"))
    
    def _display_final_summary(self):
        """Display final simulation summary"""
        print("\n" + "=" * 80)
        print("SIMULATION COMPLETE - FINAL SUMMARY")
        print("=" * 80)
        
        summary = self.portfolio.get_portfolio_summary(self.current_prices)
        risk_summary = self.risk.get_risk_summary(self.current_prices)
        
        print(f"\nInitial Capital:       {self.primary_currency}{self.engine.initial_capital:,.2f}")
        print(f"Final Portfolio Value: {self.primary_currency}{summary['total_value']:,.2f}")
        
        total_pnl_sign = "+" if summary['total_pnl'] >= 0 else ""
        print(f"Total P&L:             {total_pnl_sign}{self.primary_currency}{summary['total_pnl']:,.2f} ({total_pnl_sign}{summary['total_pnl_pct']:.2f}%)")
        
        print(f"\nTotal Trades:          {summary['closed_trades']}")
        if summary['closed_trades'] > 0:
            print(f"Win Rate:              {summary['win_rate']:.1f}%")
            print(f"Profit Factor:         {summary['profit_factor']:.2f}")
            print(f"Avg Win:               {self.primary_currency}{self.portfolio.get_average_win():.2f}")
            print(f"Avg Loss:              {self.primary_currency}{self.portfolio.get_average_loss():.2f}")
        
        print(f"\nMax Drawdown:          {self.primary_currency}{risk_summary['max_drawdown_dollars']:.2f} ({risk_summary['max_drawdown_pct']:.2f}%)")
        
        print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Trading Platform Simulator - Unified Markets")
    parser.add_argument("--symbols", type=str, default=None,
        help="Comma-separated symbols (if not provided, interactive menu shown)")
    parser.add_argument("--strategy", type=str, default="adaptive",
        choices=['rsi', 'ma', 'ema', 'combined', 'stochastic', 'adaptive'], help="Trading strategy")
    parser.add_argument("--capital", type=float, default=10000.0, help="Initial capital")
    parser.add_argument("--leverage", type=float, default=2.0, help="Maximum leverage")
    parser.add_argument("--ticks", type=int, default=500, help="Simulation ticks")
    parser.add_argument("--display-interval", type=int, default=50, help="Display interval")
    parser.add_argument("--no-interactive", action="store_true",
        help="Disable interactive mode (use defaults)")
    
    args = parser.parse_args()
    
    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(',')]
    elif args.no_interactive:
        symbols = ['NIFTY50', 'SENSEX', 'BANKNIFTY']
        print(f"Using defaults: {', '.join(symbols)}")
    else:
        symbols = get_user_symbol_selection()
        if not symbols:
            print("No symbols selected. Exiting.")
            return
    
    display_symbol_summary(symbols)
    
    if not args.no_interactive and not args.symbols:
        display_market_analysis(symbols)
        strategy = get_strategy_selection()
    else:
        strategy = args.strategy
    
    if not args.no_interactive and not args.symbols:
        confirm = input("\nReady to start simulation? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Simulation cancelled.")
            return
    
    simulator = TradingSimulator(
        symbols=symbols, strategy_name=strategy,
        initial_capital=args.capital, max_leverage=args.leverage,
        simulation_ticks=args.ticks, display_interval=args.display_interval
    )
    simulator.run_simulation()


if __name__ == "__main__":
    main()
