"""
n8n Remote Listener Entrypoint - forwards to Antigravity Remote Agent Engine
"""
from antigravity_remote_agent import run_server

if __name__ == "__main__":
    run_server()
