#!/bin/bash
set -e

# Define Display
export DISPLAY=:99
export RESOLUTION="1280x720x16"

# Link Steam Client for Headless operation
mkdir -p /root/.steam/sdk64
mkdir -p /root/.steam/sdk32
ln -sf /root/steamcmd/linux64/steamclient.so /root/.steam/sdk64/steamclient.so
ln -sf /root/steamcmd/linux64/steamclient.so /root/.steam/sdk32/steamclient.so

echo "--- Starting Xvfb on $DISPLAY ($RESOLUTION) ---"
Xvfb $DISPLAY -screen 0 $RESOLUTION &
XVFB_PID=$!
sleep 1

echo "--- Starting Fluxbox ---"
fluxbox &
FLUXBOX_PID=$!

echo "--- Starting x11vnc on Port 5900 ---"
x11vnc -display $DISPLAY -forever -nopw -bg -quiet -listen 0.0.0.0 -xkb

echo "--- Ready! ---"
echo "Log: /app/logs/runtime.log (if used)"

# Execute the passed command (default is tail -f /dev/null)
exec "$@"
