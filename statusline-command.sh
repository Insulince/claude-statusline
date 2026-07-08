#!/usr/bin/env bash
input=$(cat)
script_dir="$(cd "$(dirname "$0")" && pwd)"

# Try python3 first, fall back to python (common on Windows).
if command -v python3 &>/dev/null; then
    echo "$input" | python3 "$script_dir/statusline.py"
elif command -v python &>/dev/null; then
    echo "$input" | python "$script_dir/statusline.py"
else
    echo "  [statusline: python not found]"
fi
