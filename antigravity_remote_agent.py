"""
Antigravity Autonomous Remote Developer Agent Engine
General-purpose AI Developer listening for Slack triggers via n8n.
Powered by Gemini Pro reasoning & tool-calling agent loop.
Executes file creations, terminal commands, project builds, and conversational debating across any directory on Mac.
"""

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import json
import subprocess
import os
import datetime
from google import genai
from google.genai import types

PORT = 5001
DEFAULT_WORKSPACE = "/Users/thomaswu/Desktop"

# --- AGENT TOOLS ---

def run_shell_command(command: str, working_dir: str = DEFAULT_WORKSPACE) -> str:
    """Executes any terminal command on Mac (e.g. mkdir, git, python3, npm, n8n creation, pip)."""
    cwd = working_dir if os.path.exists(working_dir) else DEFAULT_WORKSPACE
    print(f"🛠️ [Agent Executing Command] '{command}' in '{cwd}'")
    res = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=cwd)
    out = (res.stdout or "") + ("\nSTDERR:\n" + res.stderr if res.stderr else "")
    return out.strip() or "Command executed cleanly with no output."

def create_or_write_file(filepath: str, content: str) -> str:
    """Creates a new file or updates an existing file with code or documentation on Mac."""
    print(f"🛠️ [Agent Writing File] {filepath}")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return f"File successfully written to '{filepath}'."

def read_file_contents(filepath: str) -> str:
    """Reads the content of any file on Mac."""
    if not os.path.exists(filepath):
        return f"Error: File '{filepath}' does not exist."
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def list_directory_contents(dirpath: str = DEFAULT_WORKSPACE) -> str:
    """Lists files and folders inside a given directory on Mac."""
    if not os.path.exists(dirpath):
        return f"Error: Directory '{dirpath}' does not exist."
    items = os.listdir(dirpath)
    return "\n".join(sorted(items)) if items else "Directory is empty."

TOOL_MAP = {
    "run_shell_command": run_shell_command,
    "create_or_write_file": create_or_write_file,
    "read_file_contents": read_file_contents,
    "list_directory_contents": list_directory_contents,
}


def run_antigravity_agent(user_prompt: str, target_dir: str = DEFAULT_WORKSPACE) -> str:
    """
    Autonomous AI Developer Agent Loop powered by Gemini 2.5 Pro.
    Supports multi-turn reasoning, debating, code writing, and local execution.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "❌ Error: GEMINI_API_KEY environment variable is not set on Mac."

    today_str = datetime.date.today().strftime("%B %d, %Y")
    client = genai.Client(api_key=api_key)
    workspace = target_dir if (target_dir and os.path.exists(target_dir)) else DEFAULT_WORKSPACE

    system_instruction = f"""You are "Antigravity Remote Developer", a top-tier autonomous AI Software & Systems Engineer running on Thomas's Mac.
Current Date: {today_str}.
Active Workspace Directory: {workspace}.

YOUR CORE ROLE & PERSONALITY:
1. You are a collaborative, highly capable remote developer. Thomas can ask you questions, ask you to build new projects, edit code, configure n8n, write BigQuery scripts, or debate architecture with you.
2. If Thomas wants to debate or discuss ideas, provide thoughtful, highly technical engineering feedback like a senior pair programmer.
3. If Thomas requests a task involving local work (creating folders, writing scripts, running terminal commands, installing packages), execute the appropriate tools on his Mac directly.
4. NEVER ask for manual confirmation for routine shell commands or file creation; execute them autonomously using your tools.
5. FOLDER CREATION RULE: When Thomas asks to create a new folder or new project (e.g., "create a folder called X"), ALWAYS create it directly on the Desktop (`/Users/thomaswu/Desktop/X`) so it is immediately visible on his screen.
6. Always respond with clear, well-structured Slack Markdown (bold headers, code blocks, bullet points, and clean status indicators).
"""

    messages = [user_prompt]
    max_turns = 6
    execution_logs = []

    for turn in range(max_turns):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-pro',
                contents=messages,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=[run_shell_command, create_or_write_file, read_file_contents, list_directory_contents],
                    temperature=0.2,
                )
            )

            # Process Tool Calls if requested by the Agent
            if response.function_calls:
                for call in response.function_calls:
                    fn_name = call.name
                    fn_args = call.args
                    print(f"🤖 [Turn {turn+1}] Agent Calling Tool: '{fn_name}' with args {fn_args}")

                    if fn_name in TOOL_MAP:
                        tool_result = TOOL_MAP[fn_name](**fn_args)
                        execution_logs.append(f"Tool `{fn_name}` ➔ {tool_result[:300]}")
                        messages.append(response.candidates[0].content)
                        messages.append(types.Part.from_function_response(name=fn_name, response={"result": tool_result}))
                    else:
                        print(f"Unknown Tool: {fn_name}")
            else:
                final_text = response.text or "Task completed successfully."
                if execution_logs:
                    return f"{final_text}\n\n*Actions Executed on Mac:*\n```\n" + "\n".join(execution_logs) + "\n```"
                return final_text

        except Exception as e:
            # Fallback to flash model if pro model rate-limits
            print(f"Pro Model exception ({e}), falling back to Flash model...")
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=messages,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        tools=[run_shell_command, create_or_write_file, read_file_contents, list_directory_contents],
                        temperature=0.2,
                    )
                )
                return response.text or "Task completed."
            except Exception as e2:
                return f"❌ Antigravity Agent Execution Error: {str(e2)}"

    return "⚠️ Antigravity Agent reached max step limit."


class StandaloneN8nListener(BaseHTTPRequestHandler):
    def _send_response(self, status_code, message_dict):
        body = json.dumps(message_dict).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            payload = json.loads(post_data.decode('utf-8'))
        except Exception:
            payload = {}

        raw_action = payload.get("action") or payload.get("text") or "Hello Antigravity!"
        target_dir = payload.get("project_dir", DEFAULT_WORKSPACE)

        # Anti-loop check for bot responses
        if "remote developer" in str(raw_action).lower() or "🤖" in str(raw_action) or "⚡" in str(raw_action) or "antigravity" in str(raw_action).lower():
            print("⚠️ IGNORED BOT RESPONSE LOOP")
            self._send_response(200, {"status": "IGNORED", "output": ""})
            return

        print(f"\n📩 SLACK INSTRUCTION RECEIVED: Prompt='{raw_action}' | TargetDir='{target_dir}'")

        ai_response = run_antigravity_agent(raw_action, target_dir)
        self._send_response(200, {"status": "SUCCESS", "output": ai_response})

    def do_GET(self):
        self._send_response(200, {"status": "ONLINE", "service": "Antigravity Autonomous Remote Developer Engine", "port": PORT})


def run_server():
    server_address = ('', PORT)
    httpd = ThreadingHTTPServer(server_address, StandaloneN8nListener)
    print("==================================================================")
    print(f"🚀 ANTIGRAVITY REMOTE DEVELOPER ENGINE IS ONLINE ON PORT {PORT}")
    print("==================================================================")
    print("Location: /Users/thomaswu/Desktop/n8n_automation/antigravity_remote_agent.py\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping agent server...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
