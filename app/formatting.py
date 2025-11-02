import html
def format_item_html(item: dict) -> str:
    title = html.escape(item.get("title") or "")
    link  = item.get("link") or ""
    src   = html.escape(item.get("source") or "")
    return f"<b>{title}</b>\n<i>{src}</i>\n{link}"
