#!/usr/bin/env sh

cd -- "$(dirname -- "$0")" || exit 1

if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' 'Python 3 is required to start the simulator.'
  printf '%s' 'Press Enter to close.'
  read -r _
  exit 1
fi

python3 serve.py
status=$?
if [ "$status" -ne 0 ]; then
  printf '%s' 'Startup failed. Press Enter to close.'
  read -r _
fi

exit "$status"
