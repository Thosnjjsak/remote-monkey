"""
Antigravity Autonomous Remote Developer Agent Engine (OptiPlex Edition)
Listens directly to Slack (#all-you-can-do) without requiring Cloud n8n or ngrok.
Powered by Gemini 2.5 Pro / Flash reasoning with native Linux tool execution.
Executes file creations, terminal commands, project builds, and remote development on OptiPlex.
"""

import os
import sys
import time
import json
import ssl
import certifi
import datetime
import subprocess
from pathlib import Path
from typing import Set, List
from dotenv import load_dotenv

from google import genai
from google.genai import types
from slack_sdk import WebClient
from rich.console import Console
from rich.panel import Panel

# Load environment
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

console = Console()

DEFAULT_WORKSPACE = os.getenv("DEFAULT_WORKSPACE", "/home/waack/projects")
os.makedirs(DEFAULT_WORKSPACE, exist_ok=True)

# --- NATIVE LINUX DEVELOPER TOOLS ---

def run_shell_command(command: str, working_dir: str = "") -> str:
    """Executes any terminal command on OptiPlex Linux (e.g. git, python3, pip, npm, systemctl, ls, mkdir)."""
    cwd = working_dir.strip() if (working_dir and os.path.exists(working_dir.strip())) else DEFAULT_WORKSPACE
    console.print(f"[bold yellow]🛠️ [Shell Executing][/bold yellow] '{command}' in '{cwd}'")
    try:
        res = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=cwd, timeout=120)
        out = (res.stdout or "") + ("\nSTDERR:\n" + res.stderr if res.stderr else "")
        return out.strip() or "Command executed cleanly with no output."
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 120 seconds."
    except Exception as e:
        return f"Error executing command: {str(e)}"

def create_or_write_file(filepath: str, content: str) -> str:
    """Creates a new file or overwrites an existing file with code or documentation on OptiPlex."""
    console.print(f"[bold cyan]📝 [Writing File][/bold cyan] {filepath}")
    try:
        p = Path(filepath)
        if not p.is_absolute():
            p = Path(DEFAULT_WORKSPACE) / p
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File successfully written to '{p}' ({len(content)} bytes)."
    except Exception as e:
        return f"Error writing file: {str(e)}"

def read_file_contents(filepath: str) -> str:
    """Reads the content of any code or text file on OptiPlex."""
    try:
        p = Path(filepath)
        if not p.is_absolute():
            p = Path(DEFAULT_WORKSPACE) / p
        if not p.exists():
            return f"Error: File '{p}' does not exist."
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def list_directory_contents(dirpath: str = "") -> str:
    """Lists files and folders inside a given directory on OptiPlex."""
    try:
        target = dirpath.strip() if (dirpath and os.path.exists(dirpath.strip())) else DEFAULT_WORKSPACE
        items = os.listdir(target)
        return "\n".join(sorted(items)) if items else "Directory is empty."
    except Exception as e:
        return f"Error listing directory: {str(e)}"


# --- AGENT RUNNER LOOP ---

def run_antigravity_agent(user_prompt: str, target_dir: str = "") -> str:
    """
    Autonomous AI Developer Agent Loop powered by Gemini.
    Performs autonomous reasoning and tool execution on OptiPlex Linux.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "❌ Error: GEMINI_API_KEY environment variable is not configured."

    today_str = datetime.date.today().strftime("%B %d, %Y")
    workspace = target_dir.strip() if (target_dir and os.path.exists(target_dir.strip())) else DEFAULT_WORKSPACE

    system_instruction = f"""You are "Antigravity Remote Developer" (also known as Remote Monkey), an autonomous senior AI Software & Systems Engineer running natively on Thomas's Dell OptiPlex Linux workstation.
Current Date: {today_str}.
Active Workspace Directory: {workspace}.

YOUR CORE ROLE & PERSONALITY:
1. You are a senior pair programmer and autonomous builder. Thomas can ask you questions, ask you to build new projects, edit code, configure services, run tests, or debate architecture.
2. Direct Execution on Linux: When Thomas asks for work to be done (creating projects, running scripts, git operations, installing dependencies with uv/pip), execute them autonomously using your tools.
3. Autonomous Completeness Rule: When asked to investigate, inspect, debug, or verify, you MUST execute all necessary tool calls (shell commands, reading files, listing directories) immediately in this session. NEVER output future promises like "I'll now examine...", "I will now check...", or "Reading file...". Call the tool right now and return the full completed findings in your response.
4. Project Creation Rule: Always place new projects inside `{DEFAULT_WORKSPACE}/<project_name>`.
5. Code Quality: Write clean, modular, production-ready code with appropriate comments.
6. Slack Markdown: Format your final response with clear Slack markdown: bold section titles, bullet points, status indicators (✅, 🚀, ⚠️), and code blocks. Summarize actions taken with definitive conclusions.
"""

    client = genai.Client(api_key=api_key)
    tools = [run_shell_command, create_or_write_file, read_file_contents, list_directory_contents]

    try:
        chat = client.chats.create(
            model='gemini-2.5-flash',
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=tools,
                temperature=0.2,
            )
        )
        response = chat.send_message(user_prompt)
        text_output = (response.text or "").strip()

        # Autonomous follow-through loop: if the model prematurely stopped with a promise to check
        incomplete_signals = [
            "i'll now examine", "i will now examine", "let me examine",
            "i will now check", "i'll now check", "reading `", "i will now read", "let me read"
        ]
        max_followups = 3
        followup_count = 0
        while followup_count < max_followups:
            if not text_output or any(sig in text_output.lower() for sig in incomplete_signals):
                console.print(f"[bold yellow]🔄 Follow-through step {followup_count + 1}: Agent left task in-progress. Enforcing tool completion...[/bold yellow]")
                followup_count += 1
                followup_prompt = (
                    "Continue: You stated you would examine, read, or check something, but have not delivered the completed investigation. "
                    "Use your tools (read_file_contents, run_shell_command) right now to read the necessary files, and provide the complete final findings and answers."
                )
                res_followup = chat.send_message(followup_prompt)
                if res_followup.text and res_followup.text.strip():
                    text_output = res_followup.text.strip()
            else:
                break

        return text_output or "Task executed successfully."
    except Exception as e:
        console.print(f"[red]Agent Exception: {e}[/red]")
        # Fallback to direct call if chat fails
        try:
            res = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_prompt,
                config=types.GenerateContentConfig(system_instruction=system_instruction)
            )
            return res.text or "Completed."
        except Exception as e2:
            return f"❌ Execution Error: {str(e2)}"


# --- SLACK LISTENER ---

class RemoteMonkeySlackListener:
    def __init__(self):
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.client = WebClient(token=self.bot_token, ssl=self.ssl_context) if self.bot_token else None
        self.target_channel_id = os.getenv("TARGET_CHANNEL_ID", "C0AJDTKMDP1")
        self.target_channel_name = os.getenv("TARGET_CHANNEL", "all-you-can-do")
        self.bot_user_id = None
        self.processed_message_ts: Set[str] = set()

    def connect(self) -> bool:
        if not self.client:
            console.print("[red]❌ Error: SLACK_BOT_TOKEN is not set.[/red]")
            return False

        try:
            auth = self.client.auth_test()
            self.bot_user_id = auth.get("user_id")
            console.print(Panel(
                f"[bold green]🤖 Remote Monkey Authenticated:[/bold green] @{auth.get('user')} (ID: `{self.bot_user_id}`)\n"
                f"[bold cyan]🏢 Workspace:[/bold cyan] {auth.get('team')}\n"
                f"[bold yellow]🎯 Listening on Channel:[/bold yellow] #{self.target_channel_name} (`{self.target_channel_id}`)\n"
                f"[bold magenta]📁 Workspace Directory:[/bold magenta] {DEFAULT_WORKSPACE}",
                title="Remote Monkey Online",
                border_style="green"
            ))
            return True
        except Exception as e:
            console.print(f"[red]❌ Slack Authentication failed: {e}[/red]")
            return False

    def start_listening(self, poll_interval_seconds: int = 2):
        if not self.connect():
            return

        console.print("\n[bold cyan]📡 REMOTE MONKEY LISTENING FOR INSTRUCTIONS IN #all-you-can-do...[/bold cyan]\n")

        while True:
            try:
                res = self.client.conversations_history(
                    channel=self.target_channel_id,
                    limit=5
                )
                messages = res.get("messages", [])

                for msg in reversed(messages):
                    msg_ts = msg.get("ts")
                    user = msg.get("user")
                    text = msg.get("text", "").strip()

                    # Ignore bot's own messages and processed messages
                    if user and user != self.bot_user_id and msg_ts not in self.processed_message_ts and text:
                        self.processed_message_ts.add(msg_ts)

                        now_ts = time.time()
                        # Process messages within the last 30 minutes
                        if float(msg_ts) > (now_ts - 1800):
                            console.print(Panel(
                                f"[bold yellow]From User:[/bold yellow] {user}\n"
                                f"[bold white]Instruction:[/bold white] {text}",
                                title=f"⚡ Incoming Remote Dev Task [{time.strftime('%H:%M:%S')}]",
                                border_style="yellow"
                            ))

                            # Add 👀 reaction to acknowledge receipt
                            try:
                                self.client.reactions_add(
                                    channel=self.target_channel_id,
                                    name="eyes",
                                    timestamp=msg_ts
                                )
                            except Exception:
                                pass

                            with console.status("[bold green]Remote Monkey coding & executing on OptiPlex...[/bold green]"):
                                agent_output = run_antigravity_agent(text)

                            # Post response back into channel
                            self.client.chat_postMessage(
                                channel=self.target_channel_id,
                                text=agent_output
                            )

                            # Add ✅ reaction to signify completion
                            try:
                                self.client.reactions_add(
                                    channel=self.target_channel_id,
                                    name="white_check_mark",
                                    timestamp=msg_ts
                                )
                            except Exception:
                                pass

                            console.print(Panel(
                                f"[green]{agent_output[:250]}...[/green]",
                                title="✅ Response Posted to #all-you-can-do",
                                border_style="green"
                            ))

                time.sleep(poll_interval_seconds)

            except KeyboardInterrupt:
                console.print("\n[yellow]Stopping Remote Monkey Listener.[/yellow]")
                break
            except Exception as loop_err:
                console.print(f"[dim red]Loop notice: {loop_err}[/dim red]")
                time.sleep(poll_interval_seconds)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        console.print("[bold cyan]🤖 Remote Monkey CLI Mode (Type 'exit' to quit)[/bold cyan]")
        while True:
            try:
                user_input = input("\n[Remote-Monkey] > ")
                if user_input.strip().lower() in ["exit", "quit"]:
                    break
                if not user_input.strip():
                    continue
                res = run_antigravity_agent(user_input)
                print("\n" + res)
            except KeyboardInterrupt:
                break
    else:
        listener = RemoteMonkeySlackListener()
        listener.start_listening()


if __name__ == "__main__":
    main()
