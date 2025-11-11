
---

# Dynamic Support SMA Regime Breakout Backtester

A simple, pure-Python, multiprocessing backtester for a regime-filtered, ATR-dynamic-support breakout strategy. Designed for experimentation and rapid optimization on **Australian Gold Miners ETF (GDX.AX)**, but can be used for any Yahoo Finance symbol.

---

## **Features**

* **No dependencies except `yfinance` and standard library.**
* **Pure Python math** (no numpy or pandas in the loop).
* **Strategy:** Buys when a simple moving average (SMA) crosses above a dynamic ATR-based support, in a trending regime.
* **Regime filters:** Multi-SMA and ATR-based volatility filters for trend confirmation.
* **Tracks:**

  * Final return
  * Maximum drawdown
  * Win rate
  * Number of trades
  * Trade-by-trade log (with date/time, entry/exit price, outcome, PnL %)
* **Multiprocessing** for fast optimization of random parameter sets.

---

## **Strategy Logic**

**Entry:**

* SMA crosses above (lowest low + ATR * sensitivity)
* Trend regime is confirmed via SMA and ATR filters

**Exit:**

* Hard stop-loss (percent from entry)
* Fixed risk-reward take-profit (multiples of stop size)

---

## **Usage**

1. **Install requirements**

   ```bash
   pip install yfinance
   ```

2. **Run the backtester**

   ```bash
   python your_script.py
   ```

3. **Output**

   * Top 10 parameter sets with statistics.
   * Prints the first 10 trades from the best run (dates, prices, outcome, PnL).

   Example output:

   ```
   1. Return 1.1532 | Drawdown 8.12% | Win rate 45.45% | Trades 11 | PnL 15.32% | lookback=40, sens=1.231, ma=18, SL=0.054, RR=3.145
   ...
   Sample trades from best result:
   {'entry_date': '2023-09-01 10:00:00', 'exit_date': '2023-09-03 11:00:00', 'entry_price': 36.7, 'exit_price': 38.12, 'pnl_pct': 3.88, 'type': 'win'}
   ```

---

## **Parameters**

Randomly searches:

* **lookback:** Period for lowest low (support)
* **sensitivity:** ATR multiplier
* **ma:** SMA length
* **SL:** Stop loss %
* **RR:** Reward/risk ratio

---

## **Customization**

* Change `symbol`, `period`, `interval` in `load_data()`.
* Change strategy logic in `backtest()`.

---

## **Notes**

* **Only works for LONG trades as written.**
* Not investment advice—research before using live.
* For best speed, run on multicore machines.

---
