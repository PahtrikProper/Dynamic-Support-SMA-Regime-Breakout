import yfinance as yf
import random
import multiprocessing as mp

SYMBOLS = ["APA.AX", "GDX.AX", "GOLD.AX", "LTR.AX", "NAB.AX", "NDQ.AX", "PLS.AX", "WDS.AX"]

def load_data(symbol="GDX.AX", period="90d", interval="1h"):
    tk = yf.Ticker(symbol)
    df = tk.history(period=period, interval=interval).dropna()
    closes = [float(v) for v in df["Close"].values]
    highs  = [float(v) for v in df["High"].values]
    lows   = [float(v) for v in df["Low"].values]
    dates  = [str(idx) for idx in df.index]
    return highs, lows, closes, dates

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

def backtest(params, highs, lows, closes, dates):
    lookback, sens, ma_len, stop_loss, rr = params

    balance = 1.0
    peak_balance = 1.0
    max_drawdown = 0.0
    in_position = False
    entry = 0.0
    entry_idx = None

    trades = 0
    wins = 0
    pnl = []
    equity_curve = []
    trade_log = []

    for i in range(len(closes)):
        supp = lowest(lows, lookback, i) + atr(highs, lows, closes, 14, i) * sens * 0.5
        ma = sma(closes, ma_len, i)
        sma20  = sma(closes, 20, i)
        sma50  = sma(closes, 50, i)
        sma200 = sma(closes, 200, i)
        atr_now  = atr(highs, lows, closes, 14, i)
        atr_prev = atr(highs, lows, closes, 14, i-3) if i >= 3 else atr_now
        trending = (sma20 > sma50) and (closes[i] > sma200) and (atr_now > atr_prev)

        if (not in_position
            and i > 1
            and ma > supp
            and sma(closes, ma_len, i-1) <= supp
            and trending):
            in_position = True
            entry = closes[i]
            entry_idx = i

        if in_position:
            stop_price = entry * (1 - stop_loss)
            target = entry + ((entry - stop_price) * rr)
            if lows[i] <= stop_price:
                balance *= stop_price / entry
                trades += 1
                trade_log.append({
                    "entry_date": dates[entry_idx],
                    "exit_date": dates[i],
                    "entry_price": entry,
                    "exit_price": stop_price,
                    "pnl_pct": (stop_price - entry) / entry * 100,
                    "type": "loss"
                })
                pnl.append((stop_price - entry) / entry)
                in_position = False
                entry_idx = None
            elif highs[i] >= target:
                balance *= target / entry
                trades += 1
                trade_log.append({
                    "entry_date": dates[entry_idx],
                    "exit_date": dates[i],
                    "entry_price": entry,
                    "exit_price": target,
                    "pnl_pct": (target - entry) / entry * 100,
                    "type": "win"
                })
                pnl.append((target - entry) / entry)
                wins += 1
                in_position = False
                entry_idx = None

        equity_curve.append(balance)
        if balance > peak_balance:
            peak_balance = balance
        dd = (peak_balance - balance) / peak_balance
        if dd > max_drawdown:
            max_drawdown = dd

    win_rate = (wins / trades) * 100 if trades > 0 else 0
    total_pnl = (balance - 1.0) * 100  # percent

    return {
        "final_balance": balance,
        "drawdown": max_drawdown * 100,
        "win_rate": win_rate,
        "trades": trades,
        "pnl": total_pnl,
        "params": params,
        "trade_log": trade_log
    }

def random_params():
    return (
        random.randint(2, 200),
        random.uniform(0.5, 3.0),
        random.randint(2, 200),
        random.uniform(0.01, 0.20),
        random.uniform(1, 20)
    )

def worker(args):
    params, highs, lows, closes, dates = args
    result = backtest(params, highs, lows, closes, dates)
    return result

def optimize_for_symbol(symbol, trials=500):
    highs, lows, closes, dates = load_data(symbol, period="90d", interval="1h")
    args = [(random_params(), highs, lows, closes, dates) for _ in range(trials)]
    with mp.Pool(mp.cpu_count()) as pool:
        results = list(pool.imap(worker, args))
    results.sort(reverse=True, key=lambda x: x["final_balance"])
    best = results[0]
    best["symbol"] = symbol
    return best

def main():
    all_best = []
    print("\nRunning backtest for symbols:")
    for symbol in SYMBOLS:
        print(f"\n=== {symbol} ===")
        best = optimize_for_symbol(symbol, trials=500)  # adjust trials for more/less search
        print(f"Top result for {symbol}:")
        print(
            f"Return {best['final_balance']:.4f} | "
            f"Drawdown {best['drawdown']:.2f}% | "
            f"Win rate {best['win_rate']:.2f}% | "
            f"Trades {best['trades']} | "
            f"PnL {best['pnl']:.2f}% | "
            f"Params={best['params']}"
        )
        all_best.append(best)

    # Sort by highest PnL
    all_best.sort(reverse=True, key=lambda x: x["pnl"])
    print("\n\n===== FINAL RANKING (Highest PnL) =====")
    for rank, res in enumerate(all_best, start=1):
        print(
            f"{rank}. {res['symbol']} | PnL {res['pnl']:.2f}% | "
            f"Return {res['final_balance']:.4f} | "
            f"Drawdown {res['drawdown']:.2f}% | "
            f"Win rate {res['win_rate']:.2f}% | "
            f"Trades {res['trades']} | "
            f"Params={res['params']}"
        )
        print("Trade log (first 10 trades):")
        for t in res['trade_log'][:10]:
            print(
                f"  Entry: {t['entry_date']} @ {t['entry_price']:.2f} | "
                f"Exit: {t['exit_date']} @ {t['exit_price']:.2f} | "
                f"{t['type'].upper()} | "
                f"PnL: {t['pnl_pct']:.2f}%"
            )
        print("-" * 60)

if __name__ == "__main__":
    main()
