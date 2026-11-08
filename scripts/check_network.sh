#!/usr/bin/env bash
# Invariant I2: in the app, only core/cloud.py (and localhost-only core/local_llm.py) may do network I/O.
hits=$(grep -rnE "^\s*(import|from)\s+(requests|httpx|urllib3|aiohttp|socket|urllib\.request|http\.client)" \
  --include=*.py core app.py ui phone 2>/dev/null | grep -vE "^core/(cloud|local_llm)\.py:")
if [ -n "$hits" ]; then echo "I2 violation:"; echo "$hits"; exit 1; fi
echo "network ok"
