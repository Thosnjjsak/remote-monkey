#!/bin/bash
# Automatically configures and loads launchd background services for n8n automation

PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️ Warning: GEMINI_API_KEY is not set in environment."
    read -p "Enter your GEMINI_API_KEY: " GEMINI_API_KEY
fi

LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
mkdir -p "$LAUNCH_AGENTS_DIR"

LISTENER_PLIST="$LAUNCH_AGENTS_DIR/com.thomaswu.n8n-remote-listener.plist"
NGROK_PLIST="$LAUNCH_AGENTS_DIR/com.thomaswu.ngrok-tunnel.plist"

echo "⚙️ Creating Listener LaunchAgent at $LISTENER_PLIST..."
cat <<EOF > "$LISTENER_PLIST"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.thomaswu.n8n-remote-listener</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PROJECT_DIR/.venv/bin/python</string>
        <string>$PROJECT_DIR/n8n_remote_listener.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>GEMINI_API_KEY</key>
        <string>$GEMINI_API_KEY</string>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/listener_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/listener_stderr.log</string>
</dict>
</plist>
EOF

echo "⚙️ Creating ngrok LaunchAgent at $NGROK_PLIST..."
cat <<EOF > "$NGROK_PLIST"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.thomaswu.ngrok-tunnel</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PROJECT_DIR/ngrok</string>
        <string>http</string>
        <string>127.0.0.1:5001</string>
        <string>--url=refute-puzzle-osmosis.ngrok-free.dev</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/ngrok_launchd_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/ngrok_launchd_stderr.log</string>
</dict>
</plist>
EOF

echo "🚀 Loading launchd services..."
launchctl unload "$LISTENER_PLIST" 2>/dev/null
launchctl load "$LISTENER_PLIST"

launchctl unload "$NGROK_PLIST" 2>/dev/null
launchctl load "$NGROK_PLIST"

echo "✅ Launchd setup complete! Services are active and will run on startup."
