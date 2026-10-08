import re

# Outlook (desktop) renders HTML mail with the Word engine, which ignores much of
# what QTextEdit.toHtml() relies on: styles on <body>, the <style> block,
# numeric font weights, "white-space: pre-wrap" and Qt-only "-qt-*" properties.
# prepare_email_html() rewrites the editor HTML into plain inline-styled markup
# that Outlook displays the same way the editor and preview do.

_BLOCK_TAGS = ("p", "li", "td", "th", "h1", "h2", "h3", "h4", "h5", "h6")
_ALIGN_MAP = {"left": "left", "center": "center", "right": "right", "justify": "justify"}


def prepare_email_html(qt_html: str) -> str:
    html = qt_html

    # Base font taken from the <body> style Qt writes
    body_style = ""
    m = re.search(r"<body([^>]*)>", html, re.IGNORECASE)
    if m:
        sm = re.search(r'style="([^"]*)"', m.group(1))
        if sm:
            body_style = sm.group(1)
    base_style = _clean_style(body_style)
    base_family = _get_prop(base_style, "font-family") or "Calibri, sans-serif"
    base_size = _get_prop(base_style, "font-size") or "11pt"

    # Keep only the body content
    bm = re.search(r"<body[^>]*>(.*)</body>", html, re.IGNORECASE | re.DOTALL)
    if bm:
        html = bm.group(1)

    # Lists: give bullets room (Qt writes margin-left:0, which hides them in Outlook).
    # Done before style cleaning so -qt-list-indent is still available.
    def fix_list(mm):
        tag, attrs = mm.group(1), mm.group(2) or ""
        im = re.search(r"-qt-list-indent:\s*(\d+)", attrs)
        indent = max(1, int(im.group(1))) if im else 1
        attrs = _set_prop_in_attrs(attrs, "margin-left", f"{indent * 30}px")
        attrs = _set_prop_in_attrs(attrs, "padding-left", "0px")
        return f"<{tag}{attrs}>"

    html = re.sub(r"<(ul|ol)(\s[^>]*)?>", fix_list, html)

    # Clean every style attribute
    html = re.sub(
        r'style="([^"]*)"',
        lambda mm: f'style="{_clean_style(mm.group(1))}"',
        html,
    )

    # Alignment attribute -> also as CSS text-align (Outlook honours both)
    def fix_align(mm):
        tag, attrs = mm.group(1), mm.group(2) or ""
        am = re.search(r'\salign="(\w+)"', attrs)
        if am and am.group(1).lower() in _ALIGN_MAP:
            attrs = _set_prop_in_attrs(attrs, "text-align", _ALIGN_MAP[am.group(1).lower()])
        return f"<{tag}{attrs}>"

    html = re.sub(r"<(p|li|div|h[1-6])(\s[^>]*)?>", fix_align, html)

    # Apply the base font to every block so Outlook doesn't fall back to its default
    def add_base_font(mm):
        tag, attrs = mm.group(1), mm.group(2) or ""
        style = _get_style(attrs)
        extra = []
        if "font-family" not in style:
            extra.append(f"font-family:{base_family}")
        if "font-size" not in style:
            extra.append(f"font-size:{base_size}")
        if "color" not in re.sub(r"background-color", "", style):
            extra.append("color:#000000")
        if extra:
            attrs = _add_style(attrs, "; ".join(extra))
        return f"<{tag}{attrs}>"

    html = re.sub(
        r"<(%s)(\s[^>]*)?>" % "|".join(_BLOCK_TAGS), add_base_font, html, flags=re.IGNORECASE
    )

    # Preserve runs of spaces (Qt relies on white-space:pre-wrap, Outlook doesn't)
    html = _preserve_spaces(html)

    # Images: Outlook needs explicit width/height attributes to respect size
    html = re.sub(r"<img([^>]*)/?>", _fix_img, html)

    return (
        "<html><head><meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">"
        "</head>"
        f"<body><div style=\"font-family:{base_family}; font-size:{base_size}; color:#000000;\">"
        f"{html}</div></body></html>"
    )


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _clean_style(style: str) -> str:
    props = []
    for part in style.split(";"):
        if ":" not in part:
            continue
        name, value = part.split(":", 1)
        name, value = name.strip().lower(), value.strip()
        if not name or name.startswith("-qt-"):
            continue
        if name == "font-weight":
            try:
                value = "bold" if int(value) >= 600 else "normal"
            except ValueError:
                pass
        if name == "white-space":
            continue
        props.append(f"{name}:{value}")
    return "; ".join(props)


def _get_prop(style: str, name: str) -> str:
    m = re.search(r"(?:^|;)\s*%s\s*:\s*([^;]+)" % re.escape(name), style)
    return m.group(1).strip() if m else ""


def _get_style(attrs: str) -> str:
    m = re.search(r'style="([^"]*)"', attrs)
    return m.group(1) if m else ""


def _add_style(attrs: str, extra: str) -> str:
    if re.search(r'style="', attrs):
        return re.sub(
            r'style="([^"]*)"',
            lambda m: f'style="{(m.group(1).rstrip("; ") + "; " if m.group(1).strip() else "")}{extra}"',
            attrs,
            count=1,
        )
    return f'{attrs} style="{extra}"'


def _set_prop_in_attrs(attrs: str, name: str, value: str) -> str:
    style = _get_style(attrs)
    parts = [p for p in style.split(";") if p.strip() and p.split(":", 1)[0].strip().lower() != name]
    parts.append(f"{name}:{value}")
    new_style = "; ".join(p.strip() for p in parts)
    if 'style="' in attrs:
        return re.sub(r'style="[^"]*"', f'style="{new_style}"', attrs, count=1)
    return f'{attrs} style="{new_style}"'


def _preserve_spaces(html: str) -> str:
    def fix_text(m):
        text = m.group(1)
        text = re.sub(r" {2,}", lambda s: " " + "&nbsp;" * (len(s.group(0)) - 1), text)
        return f">{text}<"

    return re.sub(r">([^<>]+)<", fix_text, html)


def _fix_img(m) -> str:
    attrs = m.group(1).rstrip("/ ").rstrip()
    style = _get_style(attrs)
    for dim in ("width", "height"):
        if not re.search(r'\s%s="' % dim, attrs):
            sm = re.search(r"(?:^|;)\s*%s\s*:\s*(\d+)" % dim, style)
            if sm:
                attrs += f' {dim}="{sm.group(1)}"'
    if "border" not in attrs:
        attrs += ' border="0"'
    return f"<img{attrs} />"
