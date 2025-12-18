# Adaptive Trading Platform

## Problem Statement

Traditional trading systems use a single strategy regardless of market conditions, leading to suboptimal performance. Markets exhibit different behaviors (trending, sideways, volatile) that require different trading approaches. A fixed strategy that works well in trending markets may fail in sideways markets and vice versa.

### Key Challenges

1. **Market Regime Changes**: Markets constantly shift between trending, sideways, and volatile states
2. **Strategy Inefficiency**: Single strategies cannot adapt to changing market conditions
3. **Risk Management**: Need dynamic position sizing and risk controls across different market types
4. **Options Pricing**: Accurate Greeks calculation required for options trading decisions
5. **Multi-Asset Support**: Handle both Indian and international markets with different specifications

## Solution Approach

### Architecture Overview

```
Trading Platform
├── Market Data Generation (Synthetic pricing with GBM)
├── Market Regime Detection (ADX, Volatility, Trend Analysis)
├── Strategy Selection (Adaptive based on market conditions)
├── Execution Engine (Order processing & position management)
├── Risk Management (Portfolio tracking & limits)
└── Options Pricing (Black-Scholes with Greeks)
```

### Core Components

#### 1. Market Data Generator (`market_generator.py`)

**Purpose**: Generate realistic synthetic market data for backtesting

**Why Geometric Brownian Motion (GBM)?**
- Models stock prices as continuous-time stochastic process
- Captures realistic price movements with drift and volatility
- Industry-standard for financial simulation
- Formula: `dS = S * (μ*dt + σ*dW)` where:
  - S = Stock price
  - μ = Drift (average return)
  - σ = Volatility (standard deviation)
  - dW = Wiener process (random shock)

**Key Functions:**
```python
generate_price_tick()      # Single price update using GBM
generate_batch()            # Historical OHLCV data
generate_multiple_assets()  # Correlated multi-asset data
```

#### 2. Market Regime Analyzer (`market_regime.py`)

**Purpose**: Detect current market conditions to select optimal strategy

**Why ADX (Average Directional Index)?**
- ADX < 20: Sideways/ranging market
- ADX > 25: Strong trending market
- Helps avoid trend-following strategies in non-trending markets

**Why Volatility Analysis?**
- High volatility requires different position sizing
- Affects options pricing and Greeks
- Determines strategy aggressiveness

**Detection Logic:**
```python
1. Calculate ADX for trend strength
2. Measure volatility (standard deviation of returns)
3. Analyze volume patterns
4. Classify: UPTREND / DOWNTREND / SIDEWAYS
```

#### 3. Black-Scholes Options Pricing

**Purpose**: Calculate option prices and Greeks for informed trading

**Why Black-Scholes?**
- Industry-standard options pricing model
- Provides analytical solutions (fast computation)
- Greeks quantify risk exposure:
  - **Delta**: Price sensitivity (hedge ratio)
  - **Gamma**: Delta change rate (convexity)
  - **Vega**: Volatility sensitivity
  - **Theta**: Time decay
  - **Rho**: Interest rate sensitivity

**Formula:**
```
Call Price = S*N(d1) - K*e^(-rT)*N(d2)
d1 = [ln(S/K) + (r + σ²/2)*T] / (σ*√T)
d2 = d1 - σ*√T
```

#### 4. Trading Strategies

##### 4.1 RSI Strategy

**When to Use**: High volatility, rapid price movements

**Why RSI (Relative Strength Index)?**
- Identifies overbought (>70) and oversold (<30) conditions
- Mean reversion indicator
- Works well in ranging/oscillating markets

**Logic:**
```
- BUY when RSI < 30 (oversold)
- SELL when RSI > 70 (overbought)
- CLOSE when RSI returns to 50 (neutral)
```

##### 4.2 EMA Strategy

**When to Use**: Strong trending markets (ADX > 25)

**Why EMA (Exponential Moving Average)?**
- More reactive to recent price changes than SMA
- Crossovers signal trend changes
- Reduced lag compared to simple moving averages

**Logic:**
```
- BUY when fast EMA crosses above slow EMA
- SELL when fast EMA crosses below slow EMA
- Uses 12-period and 26-period EMAs
```

##### 4.3 Stochastic Oscillator

**When to Use**: Sideways/ranging markets (ADX < 20)

**Why Stochastic?**
- Compares closing price to price range over period
- Identifies momentum reversals in ranges
- Effective when price oscillates without clear trend

**Formula:**
```
%K = 100 * (Close - Low14) / (High14 - Low14)
%D = 3-period SMA of %K

Signals:
- BUY: %K crosses above %D in oversold zone (<20)
- SELL: %K crosses below %D in overbought zone (>80)
```

##### 4.4 Adaptive Strategy Selector

**Purpose**: Automatically choose best strategy based on market regime

**Decision Matrix:**
```
if ADX < 20 (Sideways):
    → Use Stochastic Oscillator
elif ADX > 25 and Trending:
    → Use EMA Strategy
elif Volatility > Threshold:
    → Use RSI Strategy
else:
    → Use Combined Strategy (multiple confirmations)
```

**Why Adaptive Selection?**
- Maximizes strategy effectiveness
- Reduces losses from strategy mismatch
- Automates expert decision-making
- Improves risk-adjusted returns

#### 5. Execution Engine (`execution_engine.py`)

**Purpose**: Process orders and manage positions

**Key Features:**
- Order validation and execution
- Position tracking (long/short)
- Margin calculations
- P&L computation (realized & unrealized)

**Why This Design?**
- Separates trading logic from execution
- Enables realistic slippage modeling
- Tracks full order lifecycle
- Supports multiple symbols simultaneously

#### 6. Risk Management

**Portfolio Manager**: Tracks total exposure, positions, P&L

**Risk Tracker**: Monitors:
- Maximum drawdown
- Position concentration
- Margin utilization
- Equity curve

**Why Risk Management?**
- Prevents catastrophic losses
- Ensures sustainable trading
- Provides performance metrics
- Enables position sizing rules

## Implementation Details

### Multi-Market Support

**Indian Markets:**
- Currency: ₹ (Indian Rupee)
- Symbols: NIFTY50, SENSEX, BANKNIFTY, FINNIFTY
- Lot sizes: Standardized contract sizes
- Margin: 14-18% based on instrument

**International Markets:**
- Currency: $ (USD), € (EUR)
- Symbols: AAPL, GOOGL, MSFT, SPY, QQQ
- Lot sizes: Typically 100 shares
- Margin: 50% for stocks, varies for options

### Data Flow

```
1. Market Data Generated → OHLCV prices
2. Regime Analysis → Trend, Volatility, ADX
3. Strategy Selection → Based on regime
4. Signal Generation → BUY/SELL/HOLD/CLOSE
5. Order Execution → Position updates
6. Risk Monitoring → P&L, drawdown, margins
7. Display Results → Portfolio summary
```

## Usage

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run with adaptive strategy
python main.py

# Command-line mode
python main.py --symbols NIFTY50,AAPL --strategy adaptive --ticks 500
```

### Strategy Selection

```bash
# Specific strategies
python main.py --strategy rsi        # RSI mean reversion
python main.py --strategy ema        # Trend following
python main.py --strategy stochastic # Sideways markets
python main.py --strategy adaptive   # Auto-select
```

### Interactive Mode

```
1. Select symbols (Indian/US/EU markets)
2. View market analysis (trend, volatility, Greeks)
3. Choose strategy
4. Run simulation
5. Review results
```

## Technical Design Decisions

### Why Python?

- Rapid prototyping and iteration
- Rich ecosystem (numpy, pandas, scipy)
- Readable code for financial logic
- Easy integration with data sources

### Why Pandas DataFrames?

- Efficient time-series operations
- Built-in window functions (rolling, EMA)
- Easy data manipulation
- Standard in quantitative finance

### Why Modular Architecture?

- **Separation of Concerns**: Each module has single responsibility
- **Testability**: Individual components can be tested
- **Extensibility**: Easy to add new strategies
- **Maintainability**: Changes localized to modules

### Why Synthetic Data?

- **Backtesting**: Test strategies without real data costs
- **Controllable**: Set drift, volatility parameters
- **Reproducible**: Seed-based generation
- **Safe**: No real money risk during development

## Performance Metrics

The platform tracks:

- **Total P&L**: Realized + Unrealized profit/loss
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / Gross loss
- **Max Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted returns (future)

## Future Enhancements

1. **Machine Learning Integration**: Train models on market regimes
2. **Real-Time Data**: Connect to live market feeds
3. **Advanced Options Strategies**: Iron condors, butterflies, straddles
4. **Backtesting Framework**: Historical data testing with walk-forward
5. **Portfolio Optimization**: Multi-asset allocation
6. **Risk Metrics**: VaR, CVaR, Sortino ratio

## Dependencies

```
numpy>=1.24.0      # Numerical computations
pandas>=2.0.0      # Data manipulation
scipy>=1.10.0      # Statistical functions (Black-Scholes)
matplotlib>=3.7.0  # Visualization (future)
tabulate>=0.9.0    # Display formatting
```

## Project Structure

```
tradingc++/
├── main.py                          # Entry point
├── requirements.txt                 # Dependencies  
├── README.md                        # This file
└── trading_platform/
    ├── data/
    │   └── market_generator.py      # GBM price generation + options
    ├── analysis/
    │   └── market_regime.py         # ADX, trend, volatility detection
    ├── strategies/
    │   ├── base_strategy.py         # Abstract strategy interface
    │   ├── rsi_strategy.py          # Mean reversion
    │   ├── ema_strategy.py          # Trend following
    │   ├── ma_crossover.py          # Simple MA crossover
    │   ├── stochastic_strategy.py   # Oscillator for sideways
    │   ├── combined_strategy.py     # Multi-indicator
    │   └── adaptive_selector.py     # Auto strategy selection
    ├── engine/
    │   ├── execution_engine.py      # Order processing
    │   ├── order.py                 # Order types & states
    │   └── position.py              # Position tracking
    ├── portfolio/
    │   ├── portfolio_manager.py     # Holdings & P&L
    │   └── risk_tracker.py          # Risk metrics
    └── market_config.py             # Symbol specifications
```

## Key Insights

### Why Adaptive Trading Works

1. **Market-Appropriate Strategies**: Each strategy excels in specific conditions
2. **Reduced False Signals**: Avoid trend signals in sideways markets
3. **Risk-Aware**: Adjust position size based on volatility
4. **Automatic Optimization**: No manual strategy switching

### Black-Scholes Limitations

While Black-Scholes is industry-standard, it assumes:
- Constant volatility (not realistic)
- Log-normal returns (fat tails in reality)
- No transaction costs
- Continuous trading

**Future**: Implement stochastic volatility models (Heston)

### Strategy Performance Context

No strategy wins all the time. Performance depends on:
- Market regime match
- Parameter tuning (lookback periods)
- Transaction costs
- Slippage modeling

## License

MIT License - Free for educational and commercial use

## Contributing

Contributions welcome! Focus areas:
- Additional strategies (Bollinger Bands, MACD, etc.)
- Real data connectors (APIs)
- Advanced risk metrics
- Machine learning integration

---

**Built with**: Python 3.11+ | NumPy | Pandas | SciPy
**Purpose**: Adaptive algorithmic trading research platform
**Status**: Production-ready for simulation & backtesting
