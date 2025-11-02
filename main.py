import asyncio
from telegram.ext import Application, CommandHandler
from telegram.constants import ParseMode
from datetime import datetime, timedelta
import pytz

from .config import load_settings
from .db import init_db, is_sent, mark_sent, signal_already_sent, mark_signal
from .provider_rss import fetch_rss
from .formatting import format_item_html
from .analysis_us30 import generate_us30_signal, format_signal_msg

from apscheduler.schedulers.asyncio import AsyncIOScheduler

async def broadcast_news(app, settings):
    items = await asyncio.to_thread(fetch_rss, settings.rss_urls, 20)
    tz = pytz.timezone(settings.tz)
    sent = 0
    for it in items:
        url = it.get("link")
        if not url or is_sent(settings.db_path, url):
            continue
        pub = it.get("published")
        if pub and datetime.now(tz) - pub.astimezone(tz) > timedelta(days=2):
            continue
        text = format_item_html(it)
        for tgt in settings.telegram_targets:
            try:
                await app.bot.send_message(chat_id=tgt, text=text, parse_mode=ParseMode.HTML, disable_web_page_preview=False)
            except Exception as e:
                print(f"[send_error] {tgt} {e}")
        mark_sent(settings.db_path, url)
        sent += 1
        if sent >= 10:
            break
    print(f"[broadcast_news] enviados={sent}")

async def broadcast_us30(app, settings):
    if not settings.us30_enable:
        return
    signals = await asyncio.to_thread(
        generate_us30_signal,
        settings.us30_symbol,
        settings.us30_interval,
        settings.us30_lookback,
        settings.tz,
        settings.us30_session_start,
        settings.us30_session_end
    )
    for sig in signals:
        payload = {
            "symbol": settings.us30_symbol,
            "side": sig.side,
            "entry": sig.entry,
            "stop": sig.stop,
            "tp": sig.tp,
            "rr": sig.rr,
            "reason": sig.reason,
        }
        if signal_already_sent(settings.db_path, payload):
            continue
        text = format_signal_msg(sig, settings.us30_symbol)
        for tgt in settings.telegram_targets:
            try:
                await app.bot.send_message(chat_id=tgt, text=text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            except Exception as e:
                print(f"[send_error_us30] {tgt} {e}")
        mark_signal(settings.db_path, payload)
    if signals:
        print(f"[broadcast_us30] enviados={len(signals)}")
    else:
        print("[broadcast_us30] sin señales en este ciclo")

def build_app(settings):
    application = Application.builder().token(settings.telegram_bot_token).build()

    from .handlers import start, help_cmd, chat_id
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("id", chat_id))

    return application

def main():
    settings = load_settings()
    init_db(settings.db_path)
    app = build_app(settings)

    scheduler = AsyncIOScheduler(timezone=settings.tz)

    async def job_news():
        await broadcast_news(app, settings)

    async def job_us30():
        await broadcast_us30(app, settings)

    scheduler.add_job(job_news, "interval", minutes=settings.refresh_minutes, next_run_time=None)
    scheduler.add_job(job_us30, "interval", minutes=settings.us30_refresh_minutes, next_run_time=None)

    scheduler.start()
    print("[bot] iniciando polling…")
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
