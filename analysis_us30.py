from dataclasses import dataclass
from typing import List
from datetime import datetime
import pytz

from .ta import ema, rsi, atr
from .provider_market_yf import fetch_candles

@dataclass
class US30Signal:
    side: str
    entry: float
    stop: float
    tp: float
    rr: float
    reason: str

def in_session(now, start_str: str, end_str: str, tz_str: str) -> bool:
    tz = pytz.timezone(tz_str)
    local = now.astimezone(tz)
    s_h, s_m = map(int, start_str.split(":"))
    e_h, e_m = map(int, end_str.split(":"))
    start = tz.localize(datetime(local.year, local.month, local.day, s_h, s_m))
    end   = tz.localize(datetime(local.year, local.month, local.day, e_h, e_m))
    return start <= local <= end

def generate_us30_signal(symbol: str, interval: str, lookback: str, tz: str, session_start: str, session_end: str) -> List[US30Signal]:
    now = datetime.now(pytz.utc)
    if not in_session(now, session_start, session_end, tz):
        return []

    df = fetch_candles(symbol, interval=interval, lookback=lookback)
    if df.empty or len(df) < 210:
        return []

    df["EMA20"] = ema(df["Close"], 20)
    df["EMA50"] = ema(df["Close"], 50)
    df["EMA200"] = ema(df["Close"], 200)
    df["RSI14"] = rsi(df["Close"], 14)
    df["ATR14"] = atr(df, 14)

    last = df.iloc[-1]
    price = float(last["Close"])
    ema20, ema50, ema200 = float(last["EMA20"]), float(last["EMA50"]), float(last["EMA200"])
    rsi14 = float(last["RSI14"])
    atr14 = float(last["ATR14"])

    signals: List[US30Signal] = []

    green = last["Close"] > last["Open"]
    red   = last["Close"] < last["Open"]

    rr_target = 1.5
    atr_mult = 1.2

    N = 10
    recent_low  = float(df["Low"].iloc[-N:].min())
    recent_high = float(df["High"].iloc[-N:].max())

    if price > ema200 and ema20 > ema50 and rsi14 > 55 and green:
        stop = max(recent_low, price - atr_mult * atr14)
        risk = price - stop
        if risk > 0:
            tp = price + rr_target * risk
            reason = f"Trend ↑ (EMA200), EMA20>EMA50, RSI14={rsi14:.1f}>55, vela verde. ATR14={atr14:.1f}."
            signals.append(US30Signal("BUY", round(price,2), round(stop,2), round(tp,2), rr_target, reason))

    if price < ema200 and ema20 < ema50 and rsi14 < 45 and red:
        stop = min(recent_high, price + atr_mult * atr14)
        risk = stop - price
        if risk > 0:
            tp = price - rr_target * risk
            reason = f"Trend ↓ (EMA200), EMA20<EMA50, RSI14={rsi14:.1f}<45, vela roja. ATR14={atr14:.1f}."
            signals.append(US30Signal("SELL", round(price,2), round(stop,2), round(tp,2), rr_target, reason))

    return signals

def format_signal_msg(sig: US30Signal, symbol: str) -> str:
    lines = [
        f"📊 <b>US30 ({symbol})</b> — Señal técnica",
        f"Dirección: <b>{'Compra' if sig.side=='BUY' else 'Venta'}</b>",
        f"Entrada: <code>{sig.entry}</code>  |  SL: <code>{sig.stop}</code>  |  TP: <code>{sig.tp}</code>  |  R:R ~ <b>{sig.rr:.1f}</b>",
        f"Motivo: {sig.reason}",
        "—",
        "<i>Nota: Esto es informativo, no es asesoría financiera. Gestiona tu riesgo (≤1% por operación).</i>"
    ]
    return "\n".join(lines)
