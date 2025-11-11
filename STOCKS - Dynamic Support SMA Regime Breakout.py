import yfinance as yf
import random
import multiprocessing as mp

# =====================================================
# LOAD DATA (100% Safe Numeric OHLC for GDX.AX)
# =====================================================
def load_data(symbol="GDX.AX", period="90d", interval="1h"):
    tk = yf.Ticker(symbol)
    df = tk.history(period=period, interval=interval).dropna()

    closes = [float(v) for v in df["Close"].values]
    highs  = [float(v) for v in df["High"].values]
    lows   = [float(v) for v in df["Low"].values]

    return highs, lows, closes

highs, lows, closes = load_data()

# =====================================================
# INDICATORS (NO NUMPY, PURE PYTHON MATH)
# =====================================================
def sma(arr, length, idx):
    if idx < length:
        return arr[idx]
    s = 0.0
    for i in range(idx-length, idx):
        s += arr[i]
    return s / length

def lowest(arr, length, idx):
    start = max(0, idx-length)
    v = arr[idx]
    for i in range(start, idx+1):
        if arr[i] < v:
            v = arr[i]
    return v

def atr(highs, lows, closes, length, idx):
    if idx < length:
        return highs[idx] - lows[idx]
    s = 0.0
    for i in range(idx-length, idx):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i-1]),
            abs(lows[i] - closes[i-1])
        )
        s += tr
    return s / length

# =====================================================
# BACKTEST STRATEGY (w/Stats Tracking)
# =====================================================
def backtest(params):
    lookback, sens, ma_len, stop_loss, rr = params

    balance = 1.0
    peak_balance = 1.0
    max_drawdown = 0.0
    in_position = False
    entry = 0.0

    trades = 0
    wins = 0
    pnl = []

    equity_curve = []

    for i in range(len(closes)):
        # Dynamic support
        supp = lowest(lows, lookback, i) + atr(highs, lows, closes, 14, i) * sens * 0.5
        ma = sma(closes, ma_len, i)

        # Regime filters
        sma20  = sma(closes, 20, i)
        sma50  = sma(closes, 50, i)
        sma200 = sma(closes, 200, i)

        atr_now  = atr(highs, lows, closes, 14, i)
        atr_prev = atr(highs, lows, closes, 14, i-3) if i >= 3 else atr_now

        trending = (sma20 > sma50) and (closes[i] > sma200) and (atr_now > atr_prev)

        # BUY: SMA crosses above support while trending
        if (not in_position
            and i > 1
            and ma > supp
            and sma(closes, ma_len, i-1) <= supp
            and trending):

            in_position = True
            entry = closes[i]

        # Manage open trade
        if in_position:
            stop_price = entry * (1 - stop_loss)
            target = entry + ((entry - stop_price) * rr)

            # Stop loss hit
            if lows[i] <= stop_price:
                balance *= stop_price / entry
                trades += 1
                pnl.append((stop_price - entry) / entry)
                in_position = False
            # Take profit hit
            elif highs[i] >= target:
                balance *= target / entry
                trades += 1
                pnl.append((target - entry) / entry)
                wins += 1
                in_position = False

        # Track equity curve for drawdown
        equity_curve.append(balance)
        if balance > peak_balance:
            peak_balance = balance
        dd = (peak_balance - balance) / peak_balance
        if dd > max_drawdown:
            max_drawdown = dd

    # Win rate calculation
    win_rate = (wins / trades) * 100 if trades > 0 else 0
    total_pnl = (balance - 1.0) * 100  # as percent

    return {
        "final_balance": balance,
        "drawdown": max_drawdown * 100,  # as percent
        "win_rate": win_rate,
        "trades": trades,
        "pnl": total_pnl,
        "params": params
    }

# =====================================================
# PARAMETER GENERATOR
# =====================================================
def random_params():
    return (
        random.randint(2, 200),       # lookback
        random.uniform(0.5, 3.0),     # sensitivity
        random.randint(2, 200),       # SMA length
        random.uniform(0.01, 0.20),   # stop loss %
        random.uniform(1, 20)         # RR
    )

# =====================================================
# MULTI-CORE WORKER
# =====================================================
def worker(_):
    params = random_params()
    result = backtest(params)
    return result

# =====================================================
# OPTIMIZER (Top 10 w/Full Stats)
# =====================================================
def optimize(trials=300):
    with mp.Pool(mp.cpu_count()) as pool:
        results = list(pool.imap(worker, range(trials)))

    results.sort(reverse=True, key=lambda x: x["final_balance"])

    print("\n===== TOP 10 RESULTS =====\n")
    for rank, res in enumerate(results[:10], start=1):
        lookback, sens, ma, sl, rr = res["params"]
        print(
            f"{rank}. Return {res['final_balance']:.4f} | "
            f"Drawdown {res['drawdown']:.2f}% | "
            f"Win rate {res['win_rate']:.2f}% | "
            f"Trades {res['trades']} | "
            f"PnL {res['pnl']:.2f}% | "
            f"lookback={lookback}, sens={sens:.3f}, ma={ma}, SL={sl:.3f}, RR={rr:.3f}"
        )

    print("\nBEST:", results[0])

# =====================================================
# RUN
# =====================================================
if __name__ == "__main__":
    optimize(50000)
