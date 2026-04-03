#!/usr/bin/env python3
import os
import json
import stat
import subprocess

BLUE, GREEN, YELLOW, RED, RESET = '\033[94m', '\033[92m', '\033[93m', '\033[91m', '\033[0m'

print(f"\n{BLUE}======================================={RESET}")
print(f"{BLUE}🛡️  PETZE GUARD: UNIVERSAL INSTALLER{RESET}")
print(f"{BLUE}======================================={RESET}\n")

# --- 1. USER INPUTS ---
api_key = input(f"{YELLOW}Enter your Petze API Key:{RESET} ").strip()
if not api_key:
    print(f"\n{RED}✖ Aborted: No API Key provided.{RESET}")
    exit(1)

print(f"\n{YELLOW}Which AI Agent are you installing Petze for?{RESET}")
print("1) OpenCode")
print("2) Claude Code")
print("3) Both")
agent_choice = input(f"{YELLOW}Select (1/2/3):{RESET} ").strip()

# --- 1.5. PRE-FLIGHT SYSTEM CHECKS ---
print(f"\n{YELLOW}Running pre-flight system checks...{RESET}")
try:
    subprocess.run(["npx", "--version"], capture_output=True, check=True)
    print(f"{GREEN}✔ Node.js (npx) detected.{RESET}")
except Exception:
    print(f"{RED}✖ ERROR: 'npx' command not found.{RESET}")
    print(f"{YELLOW}Petze requires Node.js to run the local MCP servers.{RESET}")
    print(f"Please install Node.js from https://nodejs.org/ and run this installer again.\n")
    exit(1)

# --- 2. DIRECTORIES & CORE CONFIG ---
petze_dir = os.path.expanduser("~/.petze")
work_dir = os.path.expanduser("~")
os.makedirs(petze_dir, exist_ok=True)

with open(os.path.join(petze_dir, "config.json"), "w") as f: 
    json.dump({"api_key": api_key}, f)

print(f"{YELLOW}Downloading MCP tools locally into Petze sandbox (no sudo required)...{RESET}")
os.system(f"npm install --prefix {petze_dir} @modelcontextprotocol/server-filesystem >/dev/null 2>&1")

# --- 3. THE PROXY ENGINE (AWS Sync, Fast-Path, Bypass & Zero-Dependency) ---
proxy_path = os.path.join(petze_dir, "petze_mcp_proxy.py")
proxy_code = """#!/usr/bin/env python3
import sys, os, json, subprocess, threading, ssl
import urllib.request, urllib.error
from datetime import datetime

# --- macOS SSL Fix ---
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

TELEMETRY_FILE = os.path.expanduser("~/.openclaw/petze_telemetry.json")
LOG_FILE = os.path.expanduser("~/.petze/activity.log")
PETZE_API_URL = "https://4w7pzc9yc1.execute-api.us-west-2.amazonaws.com/prod/v1/check"
AWS_DB_URL = "https://4w7pzc9yc1.execute-api.us-west-2.amazonaws.com/prod/v1/sync"

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
os.makedirs(os.path.dirname(TELEMETRY_FILE), exist_ok=True)

def log_ui(msg):
    with open(LOG_FILE, "a") as f: f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\\n")

def get_api_key():
    try:
        with open(os.path.expanduser("~/.petze/config.json"), "r") as f: return json.load(f).get("api_key")
    except: return "PETZE_BETA_2026"

def push_to_aws_db(entry):
    try:
        req_data = json.dumps(entry).encode('utf-8')
        req = urllib.request.Request(AWS_DB_URL, data=req_data, headers={"x-api-key": get_api_key(), "Content-Type": "application/json"}, method='POST')
        urllib.request.urlopen(req, timeout=3)
    except Exception: pass

def save_telemetry(intent, command, is_safe, reason):
    verdict = "Approved" if is_safe else "Blocked"
    entry = {"timestamp": datetime.now().isoformat(), "intent": intent, "command": command, "verdict": verdict, "reason": reason}
    
    threading.Thread(target=push_to_aws_db, args=({"logs": [{"timestamp": entry["timestamp"], "intent": intent, "command": command, "verdict": verdict, "reason": reason, "grade": "pending"}]},), daemon=True).start()

    logs = []
    try:
        with open(TELEMETRY_FILE, "r") as f: logs = json.load(f)
    except: pass
    logs.insert(0, entry)
    with open(TELEMETRY_FILE, "w") as f: json.dump(logs[:100], f, indent=2)

def forward_server(proc):
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()

def main():
    if len(sys.argv) < 2: sys.exit(1)
    macro_intent = os.environ.get("PETZE_INTENT", "General safe read-only assistant.")
    server_cmd = sys.argv[1:] 
    
    log_ui(f"🛡️ Petze MCP Proxy Started. Intent: '{macro_intent}'")
    server = subprocess.Popen(server_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stderr, text=True)
    threading.Thread(target=forward_server, args=(server,), daemon=True).start()

    for line in sys.stdin:
        try:
            msg = json.loads(line)
            if msg.get("method") == "tools/call":
                t_name = msg.get("params", {}).get("name", "unknown")
                t_args = msg.get("params", {}).get("arguments", {})
                t_args_str = json.dumps(t_args)
                cmd_str = f"Tool: {t_name} | Args: {t_args_str}"
                log_ui(f"🔍 Intercepted: {t_name}")
                
                SAFE_TOOLS = ["list_allowed_directories", "list_directory"]
                
                if macro_intent == "BYPASS":
                    is_safe, reason = True, "⚠️ Auto-approved: Petze firewall disabled for this session"
                elif t_name in SAFE_TOOLS:
                    is_safe, reason = True, "Auto-approved: Safe context tool"
                else:
                    if t_name in ["read_text_file", "read_file"]:
                        try:
                            file_path = t_args.get("path", "")
                            if os.path.exists(file_path):
                                with open(file_path, "r", encoding="utf-8") as f:
                                    content_preview = f.read(1500)
                                cmd_str += f"\\n[FILE CONTENT PREVIEW]: {content_preview}..."
                        except Exception:
                            pass

                    try:
                        req_data = json.dumps({"intent": macro_intent, "command": cmd_str}).encode('utf-8')
                        req = urllib.request.Request(PETZE_API_URL, data=req_data, headers={"x-api-key": get_api_key(), "Content-Type": "application/json"}, method='POST')
                        with urllib.request.urlopen(req, timeout=15) as response:
                            res = json.loads(response.read().decode('utf-8'))
                        is_safe, reason = res.get("is_safe", True), res.get("reason", "No reason")
                    except Exception as e: is_safe, reason = True, f"Fail-open ({e})"

                save_telemetry(macro_intent, cmd_str, is_safe, reason)

                if is_safe:
                    log_ui(f"✅ APPROVED: {reason}")
                    server.stdin.write(line); server.stdin.flush()
                else:
                    log_ui(f"🛑 BLOCKED: {reason}")
                    err = {"jsonrpc": "2.0", "id": msg.get("id"), "error": {"code": -32000, "message": f"🛡️ PETZE GUARD BLOCKED: {reason}"}}
                    sys.stdout.write(json.dumps(err) + "\\n"); sys.stdout.flush()
            else:
                server.stdin.write(line); server.stdin.flush()
        except:
            server.stdin.write(line); server.stdin.flush()

if __name__ == "__main__": main()
"""
with open(proxy_path, "w") as f: f.write(proxy_code)
os.chmod(proxy_path, os.stat(proxy_path).st_mode | stat.S_IEXEC)
print(f"{GREEN}✔ Built Proxy Engine at {proxy_path}{RESET}")

# --- 3.5. THE BASH SANDBOX ENGINE ---
bash_sandbox_path = os.path.join(petze_dir, "petze_bash_mcp.py")
bash_sandbox_code = r"""#!/usr/bin/env python3
import sys, json, subprocess, os

def respond(msg_id, result):
    response = {"jsonrpc": "2.0", "id": msg_id, "result": result}
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()

def main():
    for line in sys.stdin:
        try:
            msg = json.loads(line)
            if msg.get("method") == "initialize":
                respond(msg.get("id"), {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "petze-sandbox", "version": "1.0.0"}
                })
            elif msg.get("method") == "tools/list":
                respond(msg.get("id"), {
                    "tools": [{
                        "name": "execute_bash",
                        "description": "Execute a bash command in the terminal. Use this to run npm installs, compile code, move/delete files, or execute scripts.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "command": {"type": "string", "description": "The exact bash command to run"}
                            },
                            "required": ["command"]
                        }
                    }]
                })
            elif msg.get("method") == "tools/call":
                params = msg.get("params", {})
                if params.get("name") == "execute_bash":
                    cmd = params.get("arguments", {}).get("command", "")
                    try:
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30, cwd=os.path.expanduser("~"))
                        output = result.stdout
                        if result.stderr:
                            output += "\n[STDERR]:\n" + result.stderr
                        
                        respond(msg.get("id"), {
                            "content": [{"type": "text", "text": output or "Command executed successfully with no output."}]
                        })
                    except subprocess.TimeoutExpired:
                        respond(msg.get("id"), {"content": [{"type": "text", "text": "Command timed out after 30 seconds."}]})
                    except Exception as e:
                        respond(msg.get("id"), {"isError": True, "content": [{"type": "text", "text": f"Error: {str(e)}"}]})
        except Exception:
            pass

if __name__ == "__main__":
    main()
"""
with open(bash_sandbox_path, "w") as f: f.write(bash_sandbox_code)
os.chmod(bash_sandbox_path, os.stat(bash_sandbox_path).st_mode | stat.S_IEXEC)
print(f"{GREEN}✔ Built Bash Sandbox Engine at {bash_sandbox_path}{RESET}")

# --- 4. THE DASHBOARD CLI COMMAND (Micro-Server + UI) ---
dash_path = os.path.join(petze_dir, "petze-dash")
dash_code = r"""#!/usr/bin/env python3
import os, json, webbrowser, threading, time
from http.server import BaseHTTPRequestHandler, HTTPServer

TELEMETRY_FILE = os.path.expanduser("~/.openclaw/petze_telemetry.json")
LOG_FILE = os.path.expanduser("~/.petze/activity.log")
CONFIG_FILE = os.path.expanduser("~/.petze/config.json")
AWS_API_URL = "https://4w7pzc9yc1.execute-api.us-west-2.amazonaws.com/prod/v1/sync"

HTML_UI = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Petze Guard SOC</title>
    <style>
        :root { --bg: #0f172a; --panel: #1e293b; --text: #e2e8f0; --accent: #38bdf8; --good: #10b981; --bad: #ef4444; }
        body { background-color: var(--bg); color: var(--text); font-family: -apple-system, sans-serif; padding: 2rem; margin: 0; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--panel); padding-bottom: 1rem; margin-bottom: 2rem; }
        .tabs { display: flex; gap: 1rem; }
        .tab { padding: 0.5rem 1rem; cursor: pointer; border-radius: 6px; background: var(--panel); color: #94a3b8; font-weight: bold; border: 1px solid #334155; }
        .tab.active { background: var(--accent); color: #000; border-color: var(--accent); }
        .view { display: none; }
        .view.active { display: block; }
        
        /* Terminal View */
        #terminal { background: #000; color: #10b981; font-family: monospace; padding: 1.5rem; border-radius: 8px; height: 70vh; overflow-y: auto; border: 1px solid #334155; white-space: pre-wrap; font-size: 0.9rem;}
        
        /* Table View */
        table { width: 100%; table-layout: fixed; border-collapse: collapse; background: var(--panel); border-radius: 8px; overflow: hidden; }
        th, td { padding: 1rem; text-align: left; border-bottom: 1px solid #334155; vertical-align: top; }
        th { background: #0b1120; color: #94a3b8; text-transform: uppercase; font-size: 0.8rem; }
        
        /* Strict Column Widths to prevent overflow */
        th:nth-child(1) { width: 12%; } /* Time */
        th:nth-child(2) { width: 22%; } /* Intent */
        th:nth-child(3) { width: 36%; } /* Command */
        th:nth-child(4) { width: 20%; } /* Verdict & Reason */
        th:nth-child(5) { width: 10%; text-align: center; } /* Action */
        
        /* Command Box Fixes */
        .cmd { 
            font-family: monospace; color: #fbbf24; background: #000; 
            padding: 8px; border-radius: 6px; font-size: 0.85rem;
            white-space: pre-wrap; word-break: break-all;
            max-height: 150px; overflow-y: auto; border: 1px solid #334155;
        }
        
        .btn { padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; margin: 0 2px; }
        .btn-good { background: #10b98120; color: var(--good); border: 1px solid #10b98150; }
        .btn-bad { background: #ef444420; color: var(--bad); border: 1px solid #ef444450; }
        .btn:hover { filter: brightness(1.5); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🛡️ Petze Guard SOC</h2>
            <div class="tabs">
                <div class="tab active" onclick="switchTab('logs')">Live Activity</div>
                <div class="tab" onclick="switchTab('rlhf')">RLHF Training</div>
            </div>
        </div>

        <div id="logs" class="view active">
            <div id="terminal">Loading secure feed...</div>
        </div>

        <div id="rlhf" class="view">
            <table>
                <thead><tr><th>Time</th><th>Intent</th><th>Command</th><th>Verdict & Reason</th><th>Action</th></tr></thead>
                <tbody id="rlhf-body"></tbody>
            </table>
        </div>
    </div>

    <script>
        let apiKey = "";
        
        function switchTab(tabId) {
            document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
        }

        async function fetchLogs() {
            try {
                const res = await fetch('/api/logs');
                const text = await res.text();
                const term = document.getElementById('terminal');
                const isScrolledToBottom = term.scrollHeight - term.clientHeight <= term.scrollTop + 1;
                term.textContent = text || "No activity detected yet.";
                if(isScrolledToBottom) term.scrollTop = term.scrollHeight;
            } catch(e) {}
        }

        async function fetchRLHF() {
            try {
                const res = await fetch('/api/telemetry');
                const data = await res.json();
                apiKey = data.api_key;
                const tbody = document.getElementById('rlhf-body');
                
                if(!data.logs.length) { tbody.innerHTML = "<tr><td colspan='5' style='text-align:center;'>No telemetry found.</td></tr>"; return; }
                
                tbody.innerHTML = data.logs.map((log, i) => {
                    const color = log.verdict === 'Approved' ? 'var(--good)' : 'var(--bad)';
                    return `<tr>
                        <td style="color:#94a3b8; font-size:0.85rem;">${log.timestamp.replace('T', ' ').substring(0,19)}</td>
                        <td style="color:var(--accent); font-weight:bold;">${log.intent || 'N/A'}</td>
                        <td><div class="cmd">${log.command}</div></td>
                        <td style="color:${color}; font-weight:bold;">${log.verdict}<br><span style="font-size:0.8rem; font-weight:normal; color:#cbd5e1; display:block; margin-top:4px;">${log.reason}</span></td>
                        <td id="cell-${i}" style="text-align: center;">
                            <button class="btn btn-good" onclick="sendFeedback(${i}, 'good')">👍</button>
                            <button class="btn btn-bad" onclick="sendFeedback(${i}, 'bad')">👎</button>
                        </td>
                    </tr>`;
                }).join('');
            } catch(e) {}
        }

        async function sendFeedback(index, grade) {
            const res = await fetch('/api/telemetry');
            const data = await res.json();
            const log = data.logs[index];
            const cell = document.getElementById('cell-' + index);
            cell.innerHTML = "⏳...";
            
            try {
                const response = await fetch("''' + AWS_API_URL + '''", {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'x-api-key': apiKey },
                    body: JSON.stringify({ logs: [{...log, grade: grade}] })
                });
                if (response.ok) cell.innerHTML = "✔ Saved";
                else cell.innerHTML = "✖ Error";
            } catch (e) { cell.innerHTML = "✖ Net Error"; }
        }

        setInterval(fetchLogs, 1000);
        setInterval(fetchRLHF, 3000);
        fetchLogs(); fetchRLHF();
    </script>
</body>
</html>'''

class PetzeHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass 
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200); self.send_header('Content-type', 'text/html'); self.end_headers()
            self.wfile.write(HTML_UI.encode())
        elif self.path == '/api/logs':
            self.send_response(200); self.send_header('Content-type', 'text/plain'); self.end_headers()
            try:
                with open(LOG_FILE, 'r') as f: self.wfile.write("".join(f.readlines()[-100:]).encode())
            except: self.wfile.write(b"No logs found.")
        elif self.path == '/api/telemetry':
            self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
            try:
                with open(TELEMETRY_FILE, 'r') as f: logs = json.load(f)
            except: logs = []
            try:
                with open(CONFIG_FILE, 'r') as f: ak = json.load(f).get('api_key', '')
            except: ak = ""
            self.wfile.write(json.dumps({'api_key': ak, 'logs': logs}).encode())

if __name__ == "__main__":
    port = 8443
    print(f"🛡️  Starting Petze SOC on http://localhost:{port}")
    print("Press Ctrl+C to stop.")
    threading.Thread(target=lambda: webbrowser.open(f"http://localhost:{port}")).start()
    HTTPServer(('localhost', port), PetzeHandler).serve_forever()
"""
with open(dash_path, "w") as f: f.write(dash_code)
os.chmod(dash_path, os.stat(dash_path).st_mode | stat.S_IEXEC)
print(f"{GREEN}✔ Built Dashboard SOC CLI tool at {dash_path}{RESET}")

# --- 5. OPENCODE SETUP ---
if agent_choice in ['1', '3']:
    opencode_dir = os.path.expanduser("~/.config/opencode")
    os.makedirs(opencode_dir, exist_ok=True)
    # Added petze-sandbox to the MCP block and chained it through the proxy
    opencode_config = f"""{{
      "model": "opencode/big-pickle",
      "small_model": "opencode/big-pickle",
      "share": "disabled",
      "tools": {{"read": false, "write": false, "bash": false}},
      "mcp": {{
        "petze-filesystem": {{"type": "local", "command": ["python3", "{proxy_path}", "node", "{petze_dir}/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js", "{work_dir}"], "enabled": true}},
        "petze-sandbox": {{"type": "local", "command": ["python3", "{proxy_path}", "python3", "{bash_sandbox_path}"], "enabled": true}}
      }}
    }}"""
    with open(os.path.join(opencode_dir, "opencode.jsonc"), "w") as f: f.write(opencode_config)
    
    launcher_code = '#!/bin/bash\nexport PETZE_INTENT="$1"\nopencode run "$1"\n'
    l_path = os.path.join(petze_dir, "petze-run")
    with open(l_path, "w") as f: f.write(launcher_code)
    os.chmod(l_path, os.stat(l_path).st_mode | stat.S_IEXEC)
    print(f"{GREEN}✔ Configured OpenCode and created 'petze-run' wrapper{RESET}")

# --- 6. CLAUDE CODE SETUP ---
if agent_choice in ['2', '3']:
    print(f"{YELLOW}Running Claude Code MCP registration...{RESET}")
    # Register filesystem
    os.system('npm install -g @modelcontextprotocol/server-filesystem >/dev/null 2>&1')
    os.system(f'claude mcp add petze-filesystem python3 {proxy_path} node {petze_dir}/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js {work_dir} >/dev/null 2>&1')
    
    # Register bash sandbox
    os.system(f'claude mcp add petze-sandbox python3 {proxy_path} python3 {bash_sandbox_path} >/dev/null 2>&1')
    
    claude_dir = os.path.expanduser("~/.claude")
    os.makedirs(claude_dir, exist_ok=True)
    c_settings_path = os.path.join(claude_dir, "settings.json")
    try:
        with open(c_settings_path, "r") as f: c_settings = json.load(f)
    except: c_settings = {}
    if "permissions" not in c_settings: c_settings["permissions"] = {}
    if "deny" not in c_settings["permissions"]: c_settings["permissions"]["deny"] = []
    
    for rule in ["Bash(*)", "Read(*)", "Edit(*)", "WebSearch(*)", "WebFetch(*)", "Glob(*)", "Grep(*)", "CodeSearch(*)", "Replace(*)", "WriteFile(*)", "Write(*)"]:
        if rule not in c_settings["permissions"]["deny"]:
            c_settings["permissions"]["deny"].append(rule)
            
    with open(c_settings_path, "w") as f: json.dump(c_settings, f, indent=2)

    claude_launcher = '#!/bin/bash\nexport PETZE_INTENT="$1"\nclaude -p "$1" --permission-mode bypassPermissions\n'
    c_path = os.path.join(petze_dir, "petze-claude")
    with open(c_path, "w") as f: f.write(claude_launcher)
    os.chmod(c_path, os.stat(c_path).st_mode | stat.S_IEXEC)
    print(f"{GREEN}✔ Configured Claude Code, blocked ALL native tools, and created wrapper{RESET}")

# --- 7. ALIAS & GLOBAL PROFILE INJECTION (Smart Shell Hijack) ---
shell_path = os.environ.get("SHELL", "")
is_zsh = "zsh" in shell_path
rc_file = ".zshrc" if is_zsh else ".bashrc"
profile_file = ".zprofile" if is_zsh else ".bash_profile"

rc_path = os.path.expanduser(f"~/{rc_file}")
profile_path = os.path.expanduser(f"~/{profile_file}")

# 7a. Construct the injection payload
shell_injection = "\n# --- PETZE GUARD GLOBAL COMMANDS ---\n"
shell_injection += f'alias petze-dash="{os.path.join(petze_dir, "petze-dash")}"\n'

if agent_choice in ['1', '3']:
    shell_injection += f'alias petze-run="{os.path.join(petze_dir, "petze-run")}"\n'
    shell_injection += r"""
opencode() {
    echo -e "\033[93m🛡️  Petze Guard: You launched OpenCode directly.\033[0m"
    read -p "Define intent (Type 'OFF' to disable Petze, or Enter for read-only): " user_intent
    
    if [ "$user_intent" = "OFF" ] || [ "$user_intent" = "off" ]; then
        export PETZE_INTENT="BYPASS"
        echo -e "\033[91m⚠️  Petze Firewall DISABLED. Agent has unrestricted tool access.\033[0m"
    elif [ -z "$user_intent" ]; then
        export PETZE_INTENT="General safe read-only assistant."
        echo -e "\033[90m🔒 Safe-mode activated.\033[0m"
    else
        export PETZE_INTENT="$user_intent"
        echo -e "\033[92m🔓 Intent locked: $user_intent\033[0m"
    fi
    command opencode "$@"
}
"""

if agent_choice in ['2', '3']:
    shell_injection += f'alias petze-claude="{os.path.join(petze_dir, "petze-claude")}"\n'
    shell_injection += r"""
claude() {
    if [[ "$1" == "mcp" || "$1" == "update" || "$1" == "login" || "$1" == "logout" || "$1" == "config" ]]; then
        command claude "$@"
        return
    fi

    echo -e "\033[93m🛡️  Petze Guard: You launched Claude directly.\033[0m"
    read -p "Define intent (Type 'OFF' to disable Petze, or Enter for read-only): " user_intent
    
    if [ "$user_intent" = "OFF" ] || [ "$user_intent" = "off" ]; then
        export PETZE_INTENT="BYPASS"
        echo -e "\033[91m⚠️  Petze Firewall DISABLED. Agent has unrestricted tool access.\033[0m"
    elif [ -z "$user_intent" ]; then
        export PETZE_INTENT="General safe read-only assistant."
        echo -e "\033[90m🔒 Safe-mode activated.\033[0m"
    else
        export PETZE_INTENT="$user_intent"
        echo -e "\033[92m🔓 Intent locked: $user_intent\033[0m"
    fi
    
    command claude "$@" --permission-mode bypassPermissions
}
"""

# 7b. Write to rc file
try:
    with open(rc_path, "r") as f: rc_content = f.read()
except FileNotFoundError: rc_content = ""

if "# --- PETZE GUARD GLOBAL COMMANDS ---" not in rc_content:
    with open(rc_path, "a") as f:
        f.write(shell_injection)
    print(f"{GREEN}✔ Injected terminal interceptors and aliases into ~/{rc_file}{RESET}")
else:
    print(f"{YELLOW}⚠ Terminal interceptors already exist in ~/{rc_file}. Skipping injection.{RESET}")

# 7c. Link to Profile (Global Fix)
try:
    with open(profile_path, "r") as f: profile_content = f.read()
except FileNotFoundError: profile_content = ""

if f"source ~/{rc_file}" not in profile_content:
    with open(profile_path, "a") as f:
        f.write(f"\n# Load {rc_file} for login shells (Petze Global Commands)\n")
        f.write(f"if [ -f ~/{rc_file} ]; then source ~/{rc_file}; fi\n")
    print(f"{GREEN}✔ Linked ~/{rc_file} to ~/{profile_file} for global terminal access{RESET}")

# --- 8. LOG FILE ---
open(os.path.join(petze_dir, "activity.log"), "a").close()

print(f"\n{GREEN}🚀 INSTALLATION COMPLETE!{RESET}")
print(f"{YELLOW}Important: Run this command right now to activate your new aliases and interceptors:{RESET}")
print(f"source ~/{rc_file}\n")
