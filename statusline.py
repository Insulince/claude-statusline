import sys
import json
import shutil
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

# Bars scale in discrete steps with terminal width (xs/s/m/l/xl) instead of a
# fixed size, so a wide terminal gets a bit more visual detail without the
# bars trying to fill all available real estate.
BAR_WIDTH_BREAKPOINTS = [
    (190, 6),   # xs - below this, the line is already getting cut off regardless
    (210, 8),   # s
    (240, 10),  # m
    (270, 15),  # l
    (None, 20), # xl
]

def scaled_bar_width():
    try:
        cols = shutil.get_terminal_size().columns
    except Exception:
        cols = 0
    for max_cols, width in BAR_WIDTH_BREAKPOINTS:
        if max_cols is None or cols < max_cols:
            return width

# ── ANSI ──────────────────────────────────────────────────────────────────────

RESET      = "\033[0m"
BOLD       = "\033[1m"
DIM        = "\033[2m"
CYAN       = "\033[36m"
YELLOW     = "\033[33m"
GREEN      = "\033[32m"
RED        = "\033[31m"
BRIGHT_RED = "\033[91m"
MAGENTA    = "\033[35m"
BLUE       = "\033[34m"
WHITE      = "\033[37m"
SEP     = f"{DIM}{WHITE}│{RESET}"

WEEK_SECONDS  = 7 * 86400
GRACE_SECONDS = 2 * 3600  # grace window around "on target" before calling it over/under

def c(code, text):
    return f"{code}{text}{RESET}"

def pct_color(v):
    """Context window thresholds."""
    if v is None: return BRIGHT_RED
    if v >= 90:   return BRIGHT_RED
    if v >= 75:   return RED
    if v >= 50:   return YELLOW
    return GREEN

def rate_color(v):
    """Rate limit thresholds."""
    if v is None: return RED
    if v >= 85:   return RED
    if v >= 65:   return YELLOW
    return GREEN

def cost_color(v):
    if v is None: return DIM
    if v >= 20:   return RED
    if v >= 10:   return YELLOW
    return GREEN

def fmt_relative(epoch):
    if epoch is None: return "—"
    try:
        delta = int(epoch) - int(datetime.now().timestamp())
        if delta <= 0: return "now"
        d = delta // 86400
        h = (delta % 86400) // 3600
        m = (delta % 3600) // 60
        if d > 0:   return f"{d}d{h}h{m:02d}m"
        if h > 0:   return f"{h}h{m:02d}m"
        return f"{m}m"
    except Exception:
        return "—"

def fmt_duration(seconds):
    """Format a raw second count (not an epoch) as e.g. '1d22h05m' / '3h12m' / '9m'."""
    if seconds is None: return "—"
    neg = seconds < 0
    seconds = abs(int(seconds))
    d = seconds // 86400
    h = (seconds % 86400) // 3600
    m = (seconds % 3600) // 60
    if d > 0:   s = f"{d}d{h}h{m:02d}m"
    elif h > 0: s = f"{h}h{m:02d}m"
    else:       s = f"{m}m"
    return ("-" if neg else "") + s

def consumption_status(week_pct, week_reset):
    """
    Compares actual time remaining until the 7-day reset against the idealized
    time the remaining usage budget "should" last if spent at a constant,
    uniform rate. Also projects the current average burn rate out to the full
    window. Returns (label, color, eta_str, pace_str) or None if inputs are missing.
    """
    if week_pct is None or week_reset is None:
        return None
    try:
        now = datetime.now().timestamp()
        remaining_actual  = float(week_reset) - now
        ideal_remaining   = (100 - week_pct) / 100 * WEEK_SECONDS
        diff              = remaining_actual - ideal_remaining  # >0 means overconsuming

        elapsed_so_far = WEEK_SECONDS - remaining_actual
        if elapsed_so_far > 0:
            pace_mult = (week_pct / 100) * WEEK_SECONDS / elapsed_so_far
            pace_str  = f"{pace_mult:.2f}x"
        else:
            pace_str = None
    except Exception:
        return None

    if diff > GRACE_SECONDS:
        return ("overconsuming", RED, f"{fmt_duration(diff)} left", pace_str)
    if diff < -GRACE_SECONDS:
        return ("underconsuming", BLUE, "∞", pace_str)
    # on target (within grace window)
    if diff >= 0:
        return ("on target", GREEN, f"{fmt_duration(diff)} left", pace_str)
    return ("on target", GREEN, "∞", pace_str)

def make_bar(pct, width=24, color_fn=None):
    """Filled/empty block bar, coloured by threshold."""
    if color_fn is None: color_fn = pct_color
    if pct is None:
        return c(DIM, "░" * width)
    filled = min(round(pct / 100 * width), width)  # clamp so >100% doesn't overflow
    bar    = "█" * filled + "░" * (width - filled)
    return c(color_fn(pct), bar)

# ── Helpers ───────────────────────────────────────────────────────────────────

def dig(d, *keys):
    for k in keys:
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d

def fmt_ms(ms):
    if ms is None: return "—"
    s = int(ms) // 1000
    return f"{s // 60}:{s % 60:02d}"

def fmt_epoch(epoch):
    if epoch is None: return "—"
    try:
        dt = datetime.fromtimestamp(int(epoch))
        return dt.strftime("%a %I:%M%p").replace(" 0", " ").lower()
    except Exception:
        return str(epoch)

def fmt_time(epoch):
    if epoch is None: return "—"
    try:
        dt = datetime.fromtimestamp(int(epoch))
        return dt.strftime("%I:%M%p").lstrip("0").lower()
    except Exception:
        return str(epoch)

def fmt_pct(v):
    return f"{v:3.0f}%" if v is not None else "  — "

def fmt_ctx_pct(v):
    return f"{v:6.2f}%" if v is not None else "   —  "

# ── Parse ─────────────────────────────────────────────────────────────────────

try:
    raw = sys.stdin.read()
    data = json.loads(raw)
except Exception:
    print("  [statusline: could not parse input JSON]")
    sys.exit(0)

import os
if os.environ.get("STATUSLINE_DEBUG"):
    _debug_path = os.path.join(os.path.dirname(__file__), "statusline-debug.json")
    with open(_debug_path, "w", encoding="utf-8") as f:
        f.write(raw)


model         = dig(data, "model", "display_name") or "Unknown"
cwd           = dig(data, "cwd") or dig(data, "workspace", "current_dir") or "Unknown"

total_cost    = dig(data, "cost", "total_cost_usd")
total_ms      = dig(data, "cost", "total_duration_ms")

ctx_size      = dig(data, "context_window", "context_window_size")
_raw_used_pct = dig(data, "context_window", "used_percentage")
cur_in        = dig(data, "context_window", "current_usage", "input_tokens")
cur_out       = dig(data, "context_window", "current_usage", "output_tokens")
cur_cache_r   = dig(data, "context_window", "current_usage", "cache_read_input_tokens")
cur_cache_c   = dig(data, "context_window", "current_usage", "cache_creation_input_tokens")

five_pct      = dig(data, "rate_limits", "five_hour", "used_percentage")
five_reset    = dig(data, "rate_limits", "five_hour", "resets_at")
week_pct      = dig(data, "rate_limits", "seven_day", "used_percentage")
week_reset    = dig(data, "rate_limits", "seven_day", "resets_at")

# ── Render ────────────────────────────────────────────────────────────────────

print()

# Line 1: model + session stats + context bar (all inline)
cost_str    = c(cost_color(total_cost), f"${total_cost:.2f}") if total_cost is not None else c(DIM, "—")
cur_usage_vals = [cur_in, cur_out, cur_cache_r, cur_cache_c]
if any(v is not None for v in cur_usage_vals):
    ctx_tokens = sum(v for v in cur_usage_vals if v is not None)
    has_tok    = True
    used_pct   = ctx_tokens / ctx_size * 100 if ctx_size else _raw_used_pct
else:
    ctx_tokens = 0
    has_tok    = False
    used_pct   = _raw_used_pct
ctx_lbl     = c(WHITE, f"/{ctx_size}") if ctx_size is not None else ""
tok_str     = (c(pct_color(used_pct), f"{ctx_tokens:6d}") + ctx_lbl) if has_tok else c(WHITE, "     —")

bar_width = scaled_bar_width()

ctx_bar = make_bar(used_pct, width=bar_width)
ctx_pct = c(pct_color(used_pct), fmt_ctx_pct(used_pct))

five_extra = five_pct is not None and five_pct > 100
week_extra = week_pct is not None and week_pct > 100

def fmt_rate_segment(pct, bar_width=bar_width, dimmed=False):
    """Returns (pct_str, bar). EXTRA (bright red) when pct > 100; dimmed when other window is the binding constraint."""
    if pct is not None and pct > 100:
        return c(BRIGHT_RED, " EXTRA"), c(BRIGHT_RED, "█" * bar_width)
    if dimmed:
        return c(DIM, fmt_pct(pct)), make_bar(pct, width=bar_width, color_fn=lambda v: DIM)
    return c(rate_color(pct), fmt_pct(pct)), make_bar(pct, width=bar_width, color_fn=rate_color)

rate_parts = []
if five_pct is not None:
    pct_str, bar = fmt_rate_segment(five_pct, dimmed=week_extra and not five_extra)
    rst     = c(WHITE, fmt_relative(five_reset))
    rst_abs = fmt_time(five_reset)
    rate_parts.append(f"5-hour  {pct_str} {bar} ↻ {rst} ({c(WHITE, rst_abs)})")
if week_pct is not None:
    pct_str, bar = fmt_rate_segment(week_pct, dimmed=five_extra and not week_extra)
    rst_rel = c(WHITE, fmt_relative(week_reset))
    rst_abs = fmt_epoch(week_reset)
    rate_parts.append(f"7-day  {pct_str} {bar} ↻ {rst_rel} ({c(WHITE, rst_abs)})")

    consumption = consumption_status(week_pct, week_reset)
    if consumption is not None:
        label, color, eta, pace = consumption
        seg = "Pace  "
        if pace is not None:
            seg += f"{c(color, pace)} "
        seg += f"({c(WHITE, eta)})"
        rate_parts.append(seg)

rate_str = f"  {SEP}  ".join(rate_parts)

print(f"  {BOLD}{CYAN}{model}{RESET}  {SEP}  "
      f"{cost_str}  {SEP}  "
      f"ctx  {ctx_pct} {ctx_bar}  {tok_str} tks"
      + (f"  {SEP}  {rate_str}" if rate_str else ""))

print()
