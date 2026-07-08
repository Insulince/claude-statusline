# claude-statusline

A custom status line for [Claude Code](https://claude.com/claude-code) showing model, cost, context window usage, and rate limit windows (5-hour / 7-day).

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
