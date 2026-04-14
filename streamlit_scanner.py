import time
from typing import Any
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Momentum Ladder Scanner", layout="wide")
st.title("Momentum Ladder Scanner")
st.caption("Entry and exit scanner using ladder levels, candles, momentum, volume, and RVOL.")


LADDER_RULES = [
    {"sell_range": range(4, 9), "sell_offsets": [0.00, 0.01, 0.02, 0.03], "buy_offsets": [0.72, 0.82, 0.83, 0.87, 0.91, 0.92, 0.95]},
    {"sell_range": range(9, 14), "sell_offsets": [0.00, 0.01, 0.02, 0.03], "buy_offsets": [0.67, 0.77, 0.78, 0.82, 0.86, 0.87, 0.90]},
    {"sell_range": range(14, 19), "sell_offsets": [0.00, 0.01, 0.02, 0.03], "buy_offsets": [0.62, 0.72, 0.73, 0.77, 0.81, 0.82, 0.85]},
    {"sell_range": range(19, 24), "sell_offsets": [0.00, 0.01, 0.02, 0.03], "buy_offsets": [0.57, 0.67, 0.68, 0.72, 0.76, 0.77, 0.80]},
    {"sell_range": range(24, 29), "sell_offsets": [0.00, 0.01, 0.02, 0.03], "buy_offsets": [0.52, 0.62, 0.63, 0.67, 0.71, 0.72, 0.75]},
    {"sell_range": range(29, 34), "sell_offsets": [0.00, 0.01, 0.02, 0.03], "buy_offsets": [0.47, 0.57, 0.58, 0.62, 0.66, 0.67, 0.70]},
    {"sell_range": range(34, 39), "sell_offsets": [0.00, 0.01, 0.02, 0.03], "buy_offsets": [0.42, 0.52, 0.53, 0.57, 0.61, 0.62, 0.65]},
    {"sell_range": range(39, 44), "sell_offsets": [0.00, 0.01, 0.02, 0.03], "buy_offsets": [0.37, 0.47, 0.48, 0.52, 0.56, 0.57, 0.60]},
    {"sell_range": range(44, 49), "sell_offsets": [0.00, 0.01, 0.02, 0.03], "buy_offsets": [0.32, 0.42, 0.43, 0.47, 0.51, 0.52, 0.55]},
    {"sell_range": range(49, 54), "sell_offsets": [0.00, 0.01, 0.02, 0.03], "buy_offsets": [0.27, 0.37, 0.38, 0.42, 0.46, 0.47, 0.50]},
    {"sell_range": range(54, 59), "sell_offsets": [0.00, 0.01, 0.02, 0.03], "buy_offsets": [0.22, 0.32, 0.33, 0.37, 0.41, 0.42, 0.45]},
    {"sell_range": range(59, 64), "sell_offsets": [0.00, 0.01, 0.02, 0.03], "buy_offsets": [0.17, 0.27, 0.28, 0.32, 0.36, 0.37, 0.40]},
    {"sell_range": range(64, 69), "sell_offsets": [0.00, 0.01, 0.02, 0.03], "buy_offsets": [0.12, 0.22, 0.23, 0.27, 0.31, 0.32, 0.35]},
    {"sell_range": range(69, 74), "sell_offsets": [0.00, 0.01, 0.02, 0.03], "buy_offsets": [0.07, 0.17, 0.18, 0.22, 0.26, 0.27, 0.30]},
    {"sell_range": range(74, 79), "sell_offsets": [0.00, 0.01, 0.02, 0.03], "buy_offsets": [0.02, 0.12, 0.13, 0.17, 0.21, 0.22, 0.25]},
    {"sell_range": range(79, 84), "sell_offsets": [0.00, 0.01, 0.02, 0.03], "buy_offsets": [0.97, 0.07, 0.08, 0.12, 0.16, 0.17, 0.20]},
    {"sell_range": range(84, 89), "sell_offsets": [0.00, 0.01, 0.02, 0.03], "buy_offsets": [0.92, 0.02, 0.03, 0.07, 0.11, 0.12, 0.15]},
    {"sell_range": range(89, 94), "sell_offsets": [0.00, 0.01, 0.02, 0.03], "buy_offsets": [0.87, 0.97, 0.98, 0.02, 0.06, 0.07, 0.10]},
    {"sell_range": range(94, 99), "sell_offsets": [0.00, 0.01, 0.02, 0.03], "buy_offsets": [0.82, 0.92, 0.93, 0.97, 0.01, 0.02, 0.05]},
    {"sell_range": range(99, 100), "sell_offsets": [0.00, 0.01, 0.02, 0.03], "buy_offsets": [0.77, 0.87, 0.88, 0.92, 0.96, 0.97, 0.00]},
]


def build_sell_price(dollars: int, cents_value: float) -> float:
    cents = int(round(cents_value * 100))
    if cents >= 100:
        return round((dollars + 1) + ((cents - 100) / 100), 2)
    return round(dollars + (cents / 100), 2)


def build_buy_price(current_price: float, buy_cents_value: float) -> float:
    current_total_cents = int(round(current_price * 100))
    buy_cents = int(round(buy_cents_value * 100))
    same_dollar = (current_total_cents // 100) * 100 + buy_cents
    if same_dollar < current_total_cents:
        return round(same_dollar / 100, 2)
    prev_dollar = same_dollar - 100
    return round(prev_dollar / 100, 2)


def get_ladder_for_price(price: float) -> dict[str, Any] | None:
    total_cents = int(round(price * 100))
    dollars = total_cents // 100
    cents = total_cents % 100

    for rule in LADDER_RULES:
        if cents in rule["sell_range"]:
            sell_prices = [build_sell_price(dollars, (cents / 100) + off) for off in rule["sell_offsets"]]
            buy_prices = sorted(set(build_buy_price(price, off) for off in rule["buy_offsets"]))
            return {
                "cents": cents,
                "sell_prices": sell_prices,
                "buy_prices": buy_prices,
            }
    return None


def price_near_any(price: float, levels: list[float], tolerance: float = 0.02) -> bool:
    return any(abs(price - level) <= tolerance for level in levels)


def closest_level(price: float, levels: list[float]) -> float | None:
    if not levels:
        return None
    return min(levels, key=lambda x: abs(price - x))


def get_best_buy_point(price: float, buy_levels: list[float]) -> tuple[float | None, float | None]:
    if not buy_levels:
        return None, None

    valid_levels = [level for level in buy_levels if level <= price + 0.03]
    if not valid_levels:
        best = min(buy_levels, key=lambda x: abs(price - x))
    else:
        best = max(valid_levels)

    distance = round(price - best, 2)
    return best, distance


def candle_analysis(hist: pd.DataFrame) -> dict[str, Any] | None:
    if len(hist) < 3:
        return None

    latest = hist.iloc[-1]
    prev = hist.iloc[-2]
    prev2 = hist.iloc[-3]

    open_price = float(latest["Open"])
    high = float(latest["High"])
    low = float(latest["Low"])
    close = float(latest["Close"])
    volume = float(latest["Volume"])

    prev_close = float(prev["Close"])
    prev_high = float(prev["High"])
    prev_low = float(prev["Low"])
    prev_volume = float(prev["Volume"])
    prev2_volume = float(prev2["Volume"])

    avg_volume = float(hist["Volume"].iloc[:-1].mean())

    if high == low or prev_close == 0 or avg_volume == 0:
        return None

    pct_change = ((close - prev_close) / prev_close) * 100
    rel_volume = volume / avg_volume

    body = abs(close - open_price)
    candle_range = high - low
    upper_wick = high - max(open_price, close)
    lower_wick = min(open_price, close) - low

    close_position = (close - low) / candle_range
    body_percent = body / candle_range
    upper_wick_percent = upper_wick / candle_range
    lower_wick_percent = lower_wick / candle_range

    higher_high = high > prev_high
    higher_low = low > prev_low
    volume_rising = volume > prev_volume
    recent_volume_rising = prev_volume > prev2_volume

    notes: list[str] = []
    score = 0

    if pct_change > 4:
        score += 20
        notes.append("good gain")
    if pct_change > 7:
        score += 25
        notes.append("strong gain")
    if pct_change > 10:
        score += 30
        notes.append("big gain")

    if volume > 1_000_000:
        score += 10
        notes.append("good volume")
    if volume > 5_000_000:
        score += 10
        notes.append("heavy volume")

    if rel_volume > 1.5:
        score += 10
        notes.append("strong rvol")
    if rel_volume > 2:
        score += 15
        notes.append("very high rvol")

    if 1 <= close <= 8:
        score += 10
        notes.append("good price range")

    if close_position > 0.75:
        score += 15
        notes.append("closed near high")
    elif close_position < 0.40:
        score -= 15
        notes.append("closed weak")

    if body_percent > 0.50:
        score += 10
        notes.append("strong body")
    elif body_percent < 0.25:
        score -= 10
        notes.append("small body")

    if upper_wick_percent < 0.20:
        score += 10
        notes.append("small top wick")
    elif upper_wick_percent > 0.40:
        score -= 20
        notes.append("long top wick")

    if lower_wick_percent > 0.30:
        score += 5
        notes.append("dip bought")

    if higher_high:
        score += 10
        notes.append("higher high")
    if higher_low:
        score += 10
        notes.append("higher low")
    if volume_rising:
        score += 10
        notes.append("volume rising")
    if recent_volume_rising:
        score += 5
        notes.append("volume trend rising")

    strong_entry_candle = (
        close_position > 0.65
        and body_percent > 0.35
        and upper_wick_percent < 0.25
    )

    weak_exit_candle = (
        close_position < 0.45
        or upper_wick_percent > 0.35
        or "closed weak" in notes
        or "long top wick" in notes
    )

    return {
        "close": close,
        "volume": int(volume),
        "pct_change": pct_change,
        "rel_volume": rel_volume,
        "score": score,
        "notes": notes,
        "close_position": close_position,
        "body_percent": body_percent,
        "upper_wick_percent": upper_wick_percent,
        "strong_entry_candle": strong_entry_candle,
        "weak_exit_candle": weak_exit_candle,
    }


def decide_entry(price: float, ladder: dict[str, Any], candle: dict[str, Any]) -> tuple[str, str, float | None, float | None]:
    buy_levels = ladder["buy_prices"]
    best_buy, distance_to_buy = get_best_buy_point(price, buy_levels)

    near_buy = False
    if best_buy is not None:
        near_buy = abs(price - best_buy) <= 0.03

    strong_momentum = (
        candle["pct_change"] > 4
        and candle["rel_volume"] > 1.2
        and candle["strong_entry_candle"]
    )

    too_extended = (
        candle["pct_change"] > 12
        and candle["close_position"] < 0.60
    )

    if best_buy is None:
        return "NO ENTRY", "no buy point found", None, None

    if near_buy and strong_momentum and candle["score"] >= 90:
        return "BUY NOW", f"real buy point {best_buy:.2f}", best_buy, distance_to_buy

    if near_buy and candle["score"] >= 70 and not candle["weak_exit_candle"]:
        return "WATCH FOR ENTRY", f"near buy point {best_buy:.2f}", best_buy, distance_to_buy

    if too_extended:
        return "TOO EXTENDED", f"best buy was {best_buy:.2f}", best_buy, distance_to_buy

    return "WAIT", f"next real buy point {best_buy:.2f}", best_buy, distance_to_buy


def decide_exit(price: float, ladder: dict[str, Any], candle: dict[str, Any]) -> tuple[str, str]:
    sell_levels = ladder["sell_prices"]
    near_sell = price_near_any(price, sell_levels, tolerance=0.02)
    nearest_sell = closest_level(price, sell_levels)

    strong_hold = (
        candle["pct_change"] > 4
        and candle["rel_volume"] > 1.2
        and candle["close_position"] > 0.65
        and candle["upper_wick_percent"] < 0.25
    )

    if near_sell and candle["weak_exit_candle"]:
        return "SELL NOW", f"at/near sell level {nearest_sell:.2f}"

    if near_sell and strong_hold:
        return "SELL PARTIAL", f"at/near sell level {nearest_sell:.2f}"

    if candle["score"] >= 130 and strong_hold:
        return "HOLD FOR NEXT SELL", "momentum still strong"

    return "HOLD", f"next sell area {nearest_sell:.2f}" if nearest_sell is not None else "no sell level"


def highlight_signals(row: pd.Series) -> list[str]:
    if row["Entry"] == "BUY NOW":
        return ["background-color: #0b3d0b"] * len(row)
    if row["Exit"] == "SELL NOW":
        return ["background-color: #4a0d0d"] * len(row)
    if row["Exit"] == "SELL PARTIAL":
        return ["background-color: #4a320d"] * len(row)
    if row["Entry"] == "WATCH FOR ENTRY":
        return ["background-color: #0d2f4a"] * len(row)
    return [""] * len(row)


def style_df(df: pd.DataFrame):
    if df.empty:
        return df
    return df.style.apply(highlight_signals, axis=1)


@st.cache_data(show_spinner=False)
def run_scan(sample_size: int) -> pd.DataFrame:
    stocks = pd.read_csv("all_symbols.csv")["Symbol"].dropna().astype(str).tolist()

    stocks = [
        s for s in stocks
        if "." not in s
        and "^" not in s
        and "/" not in s
        and "$" not in s
        and len(s) <= 5
        and not s.endswith("W")
        and not s.endswith("U")
        and not s.endswith("R")
    ]

    stocks_to_scan = stocks[:sample_size]
    results: list[dict[str, Any]] = []

    for stock in stocks_to_scan:
        try:
            hist = yf.Ticker(stock).history(period="5d")
            candle = candle_analysis(hist)
            if candle is None:
                continue

            price = candle["close"]

            if price < 0.50 or price > 10:
                continue

            if candle["pct_change"] < 4 or candle["rel_volume"] < 1.2 or candle["volume"] < 1_000_000:
                continue

            ladder = get_ladder_for_price(price)
            if ladder is None:
                continue

            entry_signal, entry_reason, best_buy_point, distance_to_buy = decide_entry(price, ladder, candle)
            exit_signal, exit_reason = decide_exit(price, ladder, candle)

            results.append({
                "Ticker": stock,
                "Price": round(price, 2),
                "% Change": round(candle["pct_change"], 2),
                "RVOL": round(candle["rel_volume"], 2),
                "Score": candle["score"],
                "Entry": entry_signal,
                "Entry Reason": entry_reason,
                "Best Buy Point": best_buy_point,
                "Distance to Buy": distance_to_buy,
                "Exit": exit_signal,
                "Exit Reason": exit_reason,
                "Sell Ladder": ", ".join(f"{p:.2f}" for p in ladder["sell_prices"]),
                "Buy Ladder": ", ".join(f"{p:.2f}" for p in ladder["buy_prices"]),
                "Notes": ", ".join(candle["notes"]),
            })

            time.sleep(0.02)

        except Exception:
            continue

    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values(by=["Entry", "Distance to Buy", "Score"], ascending=[True, True, False])
    return df


with st.sidebar:
    st.header("Scanner Controls")
    sample_size = st.slider("How many symbols to scan", min_value=100, max_value=2000, value=1000, step=100)
    auto_refresh = st.checkbox("Auto Refresh (15s)")
    run_button = st.button("Run Scan", type="primary")

if run_button:
    with st.spinner("Scanning symbols..."):
        df = run_scan(sample_size)

    if df.empty:
        st.warning("No stocks met all filters.")
    else:
        buy_df = df[df["Entry"].isin(["BUY NOW", "WATCH FOR ENTRY"])]
        watch_df = df[df["Entry"].isin(["WAIT", "TOO EXTENDED", "NO ENTRY"])]
        sell_df = df[df["Exit"].isin(["SELL NOW", "SELL PARTIAL"])]

        st.subheader("Real Buy-In Points")
        st.dataframe(style_df(buy_df), use_container_width=True)

        st.subheader("Watchlist")
        st.dataframe(style_df(watch_df), use_container_width=True)

        st.subheader("Sell / Take Profit")
        st.dataframe(style_df(sell_df), use_container_width=True)

        st.subheader("All Results")
        st.dataframe(style_df(df), use_container_width=True)
else:
    st.info("Click 'Run Scan' in the sidebar.")

if auto_refresh:
    time.sleep(15)
    st.rerun()