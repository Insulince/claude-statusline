# claude-statusline

A custom status line for [Claude Code](https://claude.com/claude-code) showing model, cost, context window usage, rate limit windows (5-hour / 7-day), and a 7-day consumption pace indicator.

![Status line preview](docs/statusline.png)

Left to right:

- **`Sonnet 5`** — the active model's display name.
- **`$5.22`** — total session cost (`cost.total_cost_usd`), colored green/yellow/red past $10/$20.
- **`ctx 14.53% [bar] 145348/1000000 tks`** — context window usage. The percentage and token count are computed directly from the current turn's token usage (input + output + cache read + cache creation) against the model's context window size, so it's precise to 2 decimal places. Bar and percentage are colored green/yellow/red/bright-red at 50/75/90% full.
- **`5-hour 26% [bar] ↻ 3h35m (3:30am)`** — the 5-hour rate limit window: percent used (as reported by the API — already whole-number precision, no decimals to be had), a bar colored green/yellow/red at 65/85% used, time remaining until this window resets, and the absolute reset time in parentheses.
- **`7-day 88% [bar] ↻ 1d10h05m (thu 10:00am)`** — same idea, for the rolling 7-day rate limit window.
- **`Pace 1.10x (13h56m left)`** — a projection of the 7-day window: your average usage rate so far, extrapolated across the full 7 days, expressed as a multiple of the sustainable rate (`1.00x` = using the budget exactly evenly). Colored **red** when overconsuming (on pace to run out before reset — the `(... left)` shows how much runway remains at that pace), **blue** when underconsuming (plenty of budget left, no risk of running out — shown as `(∞)`), and **green** when on target (within a small grace window of exactly even pace).

The progress bars scale in five discrete steps (`xs`/`s`/`m`/`l`/`xl`) with the terminal's width, so wider terminals get more visual resolution without the bars trying to fill all available space.

## Setup

1. Copy `statusline-command.sh` and `statusline.py` into a directory of your choice.
2. Point Claude Code's `statusLine` config at the script, e.g. in `~/.claude/settings.json`:

   ```json
   "statusLine": {
     "type": "command",
     "command": "bash /path/to/statusline-command.sh"
   }
   ```

Requires `python3` (or `python`) on PATH. The wrapper script falls back gracefully if neither is found.

Set `STATUSLINE_DEBUG=1` to dump the raw session JSON Claude Code passes in to `statusline-debug.json` next to the script, for debugging.
