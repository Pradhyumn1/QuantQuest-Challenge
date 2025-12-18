"""Market Regime Analyzer - Detects market conditions"""

import numpy as np
import pandas as pd


class MarketRegime:
    UPTREND = 'UPTREND'
    DOWNTREND = 'DOWNTREND'
    SIDEWAYS = 'SIDEWAYS'


class MarketRegimeAnalyzer:
    
    def __init__(self, lookback_period=60):
        self.lookback_period = lookback_period
    
    def detect_trend(self, prices):
        if len(prices) < self.lookback_period:
            return MarketRegime.SIDEWAYS
        
        recent = prices[-self.lookback_period:]
        slope = np.polyfit(range(len(recent)), recent, 1)[0]
        std = np.std(recent)
        
        threshold = std * 0.1
        
        if slope > threshold:
            return MarketRegime.UPTREND
        elif slope < -threshold:
            return MarketRegime.DOWNTREND
        return MarketRegime.SIDEWAYS
    
    def calculate_volatility(self, prices):
        if len(prices) < 2:
            return 0.0
        returns = np.diff(prices) / prices[:-1]
        return np.std(returns) * np.sqrt(252) * 100
    
    def calculate_adx(self, high, low, close, period=14):
        if len(high) < period + 1:
            return 0.0
        
        high = np.array(high[-period-1:])
        low = np.array(low[-period-1:])
        close = np.array(close[-period-1:])
        
        plus_dm = np.maximum(high[1:] - high[:-1], 0)
        minus_dm = np.maximum(low[:-1] - low[1:], 0)
        
        tr = np.maximum(
            high[1:] - low[1:],
            np.maximum(
                np.abs(high[1:] - close[:-1]),
                np.abs(low[1:] - close[:-1])
            )
        )
        
        atr = np.mean(tr)
        if atr == 0:
            return 0.0
        
        plus_di = 100 * np.mean(plus_dm) / atr
        minus_di = 100 * np.mean(minus_dm) / atr
        
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        return dx
    
    def analyze_volume(self, volumes):
        if len(volumes) < 20:
            return 'NEUTRAL'
        
        recent = volumes[-20:]
        avg = np.mean(recent)
        recent_avg = np.mean(recent[-5:])
        
        if recent_avg > avg * 1.2:
            return 'HIGH'
        elif recent_avg < avg * 0.8:
            return 'LOW'
        return 'NEUTRAL'
    
    def get_market_conditions(self, data):
        prices = [x['close'] for x in data]
        highs = [x['high'] for x in data]
        lows = [x['low'] for x in data]
        volumes = [x['volume'] for x in data]
        
        trend = self.detect_trend(prices)
        volatility = self.calculate_volatility(prices)
        adx = self.calculate_adx(highs, lows, prices)
        volume_profile = self.analyze_volume(volumes)
        
        return {
            'trend': trend,
            'volatility': volatility,
            'adx': adx,
            'volume': volume_profile,
            'trending': adx > 25,
            'sideways': adx < 20
        }
