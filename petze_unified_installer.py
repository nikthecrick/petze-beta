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
desktop_dir = os.path.expanduser("~/Desktop")
os.makedirs(petze_dir, exist_ok=True)

with open(os.path.join(petze_dir, "config.json"), "w") as f: 
    json.dump({"api_key": api_key}, f)

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
                
                # --- THE BYPASS SWITCH ---
                if macro_intent == "BYPASS":
                    is_safe, reason = True, "⚠️ Auto-approved: Petze firewall disabled for this session"
                
                # --- FAST-PATH WHITELIST ---
                elif t_name in SAFE_TOOLS:
                    is_safe, reason = True, "Auto-approved: Safe context tool"
                
                else:
                    # --- DEEP PACKET INSPECTION (File Content Scanning) ---
                    if t_name in ["read_text_file", "read_file"]:
                        try:
                            file_path = t_args.get("path", "")
                            if os.path.exists(file_path):
                                with open(file_path, "r", encoding="utf-8") as f:
                                    content_preview = f.read(1500)
                                cmd_str += f"\\n[FILE CONTENT PREVIEW]: {content_preview}..."
                        except Exception:
                            pass

                    # --- ZERO-DEPENDENCY AWS CLOUD CHECK ---
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

# --- 4. THE DASHBOARD CLI COMMAND ---
dash_path = os.path.join(petze_dir, "petze-dash")
dash_code = r"""#!/usr/bin/env python3
import os, json, webbrowser
from datetime import datetime

TELEMETRY_FILE = os.path.expanduser("~/.openclaw/petze_telemetry.json")
DASHBOARD_FILE = "/tmp/Petze_Dashboard.html"
CONFIG_FILE = os.path.expanduser("~/.petze/config.json")
AWS_API_URL = "https://4w7pzc9yc1.execute-api.us-west-2.amazonaws.com/prod/v1/sync"

api_key = ""
try:
    with open(CONFIG_FILE, "r") as f: api_key = json.load(f).get("api_key", "")
except: pass

logs = []
if os.path.exists(TELEMETRY_FILE):
    try:
        with open(TELEMETRY_FILE, "r") as f: logs = json.load(f)
    except: pass

rows_html = ""
for i, log in enumerate(logs):
    try:
        dt = datetime.fromisoformat(log.get("timestamp", ""))
        time_str = dt.strftime("%b %d, %H:%M:%S")
    except: time_str = log.get("timestamp", "Unknown")

    verdict = log.get("verdict", "Unknown")
    is_approved = verdict == "Approved"
    
    v_color = "#10b981" if is_approved else "#ef4444"
    v_bg = "#10b98120" if is_approved else "#ef444420"
    badge = f"<span style='background: {v_bg}; color: {v_color}; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 0.85rem;'>{verdict}</span>"
    
    rows_html += f'''
    <tr>
        <td style="white-space: nowrap; color: #94a3b8; font-size: 0.9rem;">{time_str}</td>
        <td><div class="intent">{log.get('intent', 'N/A')}</div></td>
        <td><div class="cmd">{log.get('command', 'N/A')}</div></td>
        <td style="text-align: center;">{badge}</td>
        <td style="color: #cbd5e1; font-size: 0.9rem;">{log.get('reason', 'N/A')}</td>
        <td style="text-align: center; white-space: nowrap;" id="action-cell-{i}">
            <button class="btn btn-good" onclick="sendFeedback({i}, 'good')">👍 Good</button>
            <button class="btn btn-bad" onclick="sendFeedback({i}, 'bad')">👎 Bad</button>
        </td>
    </tr>
    '''

if not rows_html: rows_html = "<tr><td colspan='6' style='text-align: center; color: #64748b; padding: 2rem;'>No telemetry data found.</td></tr>"

html_content = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Petze Training Dashboard</title>
    <style>
        body {{ background-color: #0f172a; color: #e2e8f0; font-family: -apple-system, sans-serif; padding: 2rem; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ border-bottom: 2px solid #1e293b; padding-bottom: 1rem; margin-bottom: 2rem; }}
        table {{ width: 100%; border-collapse: separate; border-spacing: 0; background: #1e293b; border-radius: 10px; overflow: hidden; border: 1px solid #334155; }}
        th, td {{ padding: 1rem; text-align: left; border-bottom: 1px solid #334155; }}
        th {{ background: #0f172a; color: #94a3b8; text-transform: uppercase; font-size: 0.8rem; }}
        .intent {{ color: #38bdf8; font-weight: 500; font-size: 0.95rem; }}
        .cmd {{ font-family: monospace; background: #0f172a; padding: 6px; border-radius: 6px; color: #fbbf24; font-size: 0.85rem; word-break: break-all; }}
        .btn {{ padding: 6px 10px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; margin: 0 2px; }}
        .btn-good {{ background: #10b98120; color: #10b981; border: 1px solid #10b98150; }}
        .btn-bad {{ background: #ef444420; color: #ef4444; border: 1px solid #ef444450; }}
        .btn:hover {{ filter: brightness(1.5); }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ Petze Training & Feedback Dashboard</h1>
        <table>
            <thead>
                <tr>
                    <th style="width: 10%;">Timestamp</th>
                    <th style="width: 20%;">Macro Intent</th>
                    <th style="width: 20%;">Tool Command</th>
                    <th style="width: 10%; text-align: center;">Verdict</th>
                    <th style="width: 25%;">Petze Rationale</th>
                    <th style="width: 15%; text-align: center;">RLHF Grade</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>

    <script>
        const rawLogs = {json.dumps(logs)};
        const API_KEY = "{api_key}"; 
        const API_URL = "{AWS_API_URL}";

        async function sendFeedback(index, grade) {{
            const log = rawLogs[index];
            const cell = document.getElementById('action-cell-' + index);
            
            const payload = {{
                logs: [{{ timestamp: log.timestamp, intent: log.intent, command: log.command, verdict: log.verdict, reason: log.reason, grade: grade }}]
            }};

            cell.innerHTML = "<span style='color: #94a3b8; font-size: 0.9rem;'>⏳ Uploading...</span>";

            try {{
                const response = await fetch(API_URL, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json', 'x-api-key': API_KEY }},
                    body: JSON.stringify(payload)
                }});

                if (response.ok) cell.innerHTML = "<span style='color: #10b981; font-weight: bold;'>✔ Saved to AWS</span>";
                else cell.innerHTML = "<span style='color: #ef4444;'>✖ Upload Failed</span>";
            }} catch (error) {{
                cell.innerHTML = "<span style='color: #ef4444;'>✖ Network Error</span>";
            }}
        }}
    </script>
</body>
</html>
'''
with open(DASHBOARD_FILE, "w") as f: f.write(html_content)
webbrowser.open(f"file://{DASHBOARD_FILE}")
"""
with open(dash_path, "w") as f: f.write(dash_code)
os.chmod(dash_path, os.stat(dash_path).st_mode | stat.S_IEXEC)
print(f"{GREEN}✔ Built Dashboard CLI tool at {dash_path}{RESET}")

# --- 5. OPENCODE SETUP (MiniMax Default) ---
if agent_choice in ['1', '3']:
    opencode_dir = os.path.expanduser("~/.config/opencode")
    os.makedirs(opencode_dir, exist_ok=True)
    opencode_config = f"""{{
      "model": "opencode/big-pickle",
      "small_model": "opencode/big-pickle",
      "share": "disabled",
      "tools": {{"read": false, "write": false, "bash": false}},
      "mcp": {{
        "petze-filesystem": {{"type": "local", "command": ["python3", "{proxy_path}", "npx", "-y", "@modelcontextprotocol/server-filesystem", "{desktop_dir}"], "enabled": true}},
        "petze-terminal": {{"type": "local", "command": ["python3", "{proxy_path}", "npx", "-y", "@modelcontextprotocol/server-bash"], "enabled": true}}
      }}
    }}"""
    with open(os.path.join(opencode_dir, "opencode.jsonc"), "w") as f: f.write(opencode_config)
    
    launcher_code = '#!/bin/bash\nexport PETZE_INTENT="$1"\nopencode run "$1"\n'
    l_path = os.path.join(petze_dir, "petze-run")
    with open(l_path, "w") as f: f.write(launcher_code)
    os.chmod(l_path, os.stat(l_path).st_mode | stat.S_IEXEC)
    print(f"{GREEN}✔ Configured OpenCode with MiniMax and created 'petze-run' wrapper{RESET}")

# --- 6. CLAUDE CODE SETUP ---
if agent_choice in ['2', '3']:
    print(f"{YELLOW}Running Claude Code MCP registration...{RESET}")
    os.system(f'claude mcp add petze-filesystem python3 {proxy_path} npx -y @modelcontextprotocol/server-filesystem {desktop_dir} >/dev/null 2>&1')
    
    claude_dir = os.path.expanduser("~/.claude")
    os.makedirs(claude_dir, exist_ok=True)
    c_settings_path = os.path.join(claude_dir, "settings.json")
    try:
        with open(c_settings_path, "r") as f: c_settings = json.load(f)
    except: c_settings = {}
    if "permissions" not in c_settings: c_settings["permissions"] = {}
    if "deny" not in c_settings["permissions"]: c_settings["permissions"]["deny"] = []
    
    for rule in ["Bash(*)", "Read(*)", "Edit(*)"]:
        if rule not in c_settings["permissions"]["deny"]:
            c_settings["permissions"]["deny"].append(rule)
            
    with open(c_settings_path, "w") as f: json.dump(c_settings, f, indent=2)

    claude_launcher = '#!/bin/bash\nexport PETZE_INTENT="$1"\nclaude -p "$1"\n'
    c_path = os.path.join(petze_dir, "petze-claude")
    with open(c_path, "w") as f: f.write(claude_launcher)
    os.chmod(c_path, os.stat(c_path).st_mode | stat.S_IEXEC)
    print(f"{GREEN}✔ Configured Claude Code, blocked native tools, and created wrapper{RESET}")

# --- 7. ALIAS & GLOBAL PROFILE INJECTION (Shell Hijack with Bypass) ---
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
    command claude "$@"
}
"""

# 7b. Write to rc file
try:
    with open(rc_path, "r") as f: rc_content = f.read()
except FileNotFoundError: rc_content = ""

# Check for our marker to avoid duplicate blocks if installer is run multiple times
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
