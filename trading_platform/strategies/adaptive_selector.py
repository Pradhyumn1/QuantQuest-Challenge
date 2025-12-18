"""Adaptive Strategy Selector"""

from .rsi_strategy import RSIStrategy
from .ma_crossover import MACrossoverStrategy
from .ema_strategy import EMAStrategy
from .combined_strategy import CombinedStrategy
from .stochastic_strategy import StochasticStrategy
from trading_platform.analysis.market_regime import MarketRegimeAnalyzer, MarketRegime


class AdaptiveStrategySelector:
    
    def __init__(self):
        self.regime_analyzer = MarketRegimeAnalyzer(lookback_period=60)
        self.current_strategy = None
        self.name = "Adaptive"
        self.current_market_conditions = None
    
    def select_strategy(self, market_data):
        conditions = self.regime_analyzer.get_market_conditions(market_data)
        
        trend = conditions['trend']
        volatility = conditions['volatility']
        adx = conditions['adx']
        
        if conditions['sideways'] or adx < 20:
            strategy = StochasticStrategy(k_period=14, d_period=3, oversold=20, overbought=80)
            reason = f"Sideways market (ADX={adx:.1f})"
        
        elif trend == MarketRegime.UPTREND and volatility < 20:
            strategy = EMAStrategy(short_period=12, long_period=26)
            reason = f"Uptrend with low volatility (Vol={volatility:.1f}%)"
        
        elif trend == MarketRegime.DOWNTREND and volatility < 20:
            strategy = EMAStrategy(short_period=12, long_period=26)
            reason = f"Downtrend with low volatility (Vol={volatility:.1f}%)"
        
        elif volatility > 30:
            strategy = RSIStrategy(period=14, oversold=30, overbought=70)
            reason = f"High volatility (Vol={volatility:.1f}%)"
        
        else:
            strategy = CombinedStrategy(
                rsi_period=14, rsi_oversold=30, rsi_overbought=70,
                ema_short=12, ema_long=26, confirmation_threshold=2)
            reason = f"Mixed conditions (Trend={trend}, Vol={volatility:.1f}%)"
        
        self.current_strategy = strategy
        return strategy, reason, conditions
    
    def generate_signal(self, data, symbol, current_position):
        if self.current_strategy is None:
            self.select_strategy(data.to_dict('records'))
        
        return self.current_strategy.generate_signal(data, symbol, current_position)
