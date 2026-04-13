#!/usr/bin/env python3
import os
import json
import stat
import subprocess
import shutil
import secrets

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

# Seed the dynamic blocklist
blocklist_path = os.path.join(petze_dir, "blocklist.txt")
with open(blocklist_path, "w") as f:
    f.write("# PETZE GUARD: DYNAMIC BLOCKLIST\n")
    f.write("# Add one threat signature per line. The proxy will instantly kill any payload containing these strings.\n")
    f.write("base64 -d\n")
    f.write("nc -e\n")
    f.write("mkfifo\n")
    f.write("/dev/tcp\n")
    f.write("rm -rf /\n")
    f.write("curl | bash\n")

# --- 2.5. THE TRAP (RADIOACTIVE HONEYPOT) ---
print(f"{YELLOW}Deploying Radioactive Honeypots...{RESET}")
canary_token = "AKIA_PETZE_" + secrets.token_hex(8).upper()
with open(os.path.join(petze_dir, "canary.txt"), "w") as f:
    f.write(canary_token)

# Trap 1: Fake AWS Backup (Safe, won't overwrite real credentials)
aws_dir = os.path.expanduser("~/.aws")
os.makedirs(aws_dir, exist_ok=True)
with open(os.path.join(aws_dir, "credentials.backup"), "w") as f:
    f.write(f"[default]\naws_access_key_id = {canary_token}\naws_secret_access_key = ptz_sec_9948274610\n")

# Trap 2: Fake .env file
with open(os.path.expanduser("~/.env.staging"), "w") as f:
    f.write(f"PROD_DB_URL=postgres://admin:secret@db.internal:5432\nAWS_ROOT_KEY={canary_token}\nSTRIPE_API=sk_live_123456789\n")
print(f"{GREEN}✔ Ghost files seeded with unique Canary Token.{RESET}")

print(f"{YELLOW}Downloading MCP tools locally into Petze sandbox (no sudo required)...{RESET}")
os.system(f"npm install --prefix {petze_dir} @modelcontextprotocol/server-filesystem >/dev/null 2>&1")

# Trap 3: Fake SSH Key (.backup so it doesn't break real ssh connections)
ssh_dir = os.path.expanduser("~/.ssh")
os.makedirs(ssh_dir, exist_ok=True)
with open(os.path.join(ssh_dir, "id_rsa.backup"), "w") as f:
    f.write("-----BEGIN OPENSSH PRIVATE KEY-----\n")
    f.write(f"Comment: aws_admin_key | {canary_token}\n")
    f.write("b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZWQy\n")
    f.write("NTUxOQAAACC/FzXQ9P+abc123xyz890pqrsPADDINGFORREALISM+ab123xyz890pq\n")
    f.write("-----END OPENSSH PRIVATE KEY-----\n")

# --- 3. THE PROXY ENGINE (AWS Sync, Fast-Path, Bypass & Zero-Dependency) ---
proxy_path = os.path.join(petze_dir, "petze_mcp_proxy.py")
proxy_code = """#!/usr/bin/env python3
import sys, os, json, subprocess, threading, ssl, re, base64
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
    agent = os.environ.get("PETZE_AGENT", "AI Agent")
    session = os.environ.get("PETZE_SESSION", "LOCAL")
    with open(LOG_FILE, "a") as f: 
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] [{agent} | #{session}] {msg}\\n")

def get_api_key():
    try:
        with open(os.path.expanduser("~/.petze/config.json"), "r") as f: return json.load(f).get("api_key")
    except: return "PETZE_BETA_2026"

def get_current_intent():
    try:
        with open(os.path.expanduser("~/.petze/intent.txt"), "r", encoding="utf-8") as f:
            val = f.read().strip()
            if val: return val
    except: pass
    return os.environ.get("PETZE_INTENT", "General safe read-only assistant.")

def get_whitelist():
    try:
        with open(os.path.expanduser("~/.petze/whitelist.txt"), "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except: return []

def get_canary_token():
    try:
        with open(os.path.expanduser("~/.petze/canary.txt"), "r", encoding="utf-8") as f:
            return f.read().strip()
    except: return "AKIA_PETZE_FALLBACK"

def get_blocklist():
    try:
        with open(os.path.expanduser("~/.petze/blocklist.txt"), "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip() and not line.startswith("#")]
    except: return ["base64 -d", "nc -e", "rm -rf /"] # Fallback if file is deleted

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
    
    startup_intent = get_current_intent()
    server_cmd = sys.argv[1:] 
    
    log_ui(f"🛡️ Petze MCP Proxy Started. Initial Intent: '{startup_intent}'")
    server = subprocess.Popen(server_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stderr, text=True)
    threading.Thread(target=forward_server, args=(server,), daemon=True).start()

    for line in sys.stdin:
        try:
            msg = json.loads(line)
            
            if msg.get("method") == "tools/call":
                t_name = msg.get("params", {}).get("name", "unknown")
                t_args = msg.get("params", {}).get("arguments", {})
                
                # --- 1. DEOBFUSCATION, FAST-SCAN & SMART TRUNCATION ---
                t_args_str = json.dumps(t_args)
                
                # A. The Decoder Ring: Hunt for hidden Base64 payloads
                decoded_str = ""
                try:
                    # Regex to find standard Base64 strings (8+ chars)
                    b64_matches = re.findall(r'(?:[A-Za-z0-9+/]{4}){2,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?', t_args_str)
                    for match in b64_matches:
                        try:
                            dec = base64.b64decode(match).decode('utf-8')
                            if len(dec) > 3 and all(ord(c) < 128 for c in dec): # Ensure it is readable text
                                decoded_str += f" {dec}"
                        except: pass
                except: pass

                # Combine the raw payload with any decoded secrets for the Bouncer
                analysis_str = t_args_str + decoded_str

                # --- 1.2 THE MIRAGE PROTOCOL (HONEYPOT TRAP) ---
                canary = get_canary_token()
                if canary in analysis_str:
                    reason = "CRITICAL: Agent attempted to exfiltrate a Radioactive Canary Token. Zero-Day Hijack detected."
                    log_ui(f"☢️ MIRAGE TRAP SPRUNG: {reason}")
                    
                    # Log the blocked attempt for the user's dashboard
                    save_telemetry(get_current_intent(), f"Tool: {t_name} | Args: {t_args_str}", False, reason)
                    
                    # THE MIRAGE: Feed the attacker's AI a fake success message
                    fake_res = {"jsonrpc": "2.0", "id": msg.get("id"), "result": {"content": [{"type": "text", "text": "HTTP 200 OK. Connection established and payload successfully transmitted."}]}}
                    sys.stdout.write(json.dumps(fake_res) + "\\n"); sys.stdout.flush()
                    continue # Skip everything else. The AI thinks it won.

                # B. The Bouncer: Scan 100% of the payload against the dynamic blocklist
                smuggling_sigs = get_blocklist()
                if any(sig in analysis_str for sig in smuggling_sigs):
                    is_safe, reason = False, "CRITICAL: Local static analysis detected malicious payload signatures."
                    log_ui(f"🛑 BLOCKED: {reason}")
                    err = {"jsonrpc": "2.0", "id": msg.get("id"), "error": {"code": -32000, "message": f"🛡️ PETZE GUARD: {reason}"}}
                    sys.stdout.write(json.dumps(err) + "\\n"); sys.stdout.flush()
                    continue

                # B. Smart Truncation: Only truncate safe reads. Never truncate bash/writes.
                if t_name in ["read_file", "read_text_file", "list_directory"]:
                    if len(t_args_str) > 1000:
                        t_args_str = t_args_str[:1000] + "... [TRUNCATED SAFE READ]"
                elif len(t_args_str) > 15000: 
                    # If a bash command/write is insanely long, kill it locally to protect AWS
                    is_safe, reason = False, "CRITICAL: Payload exceeds safe evaluation length (15k chars). Potential buffer smuggling."
                    log_ui(f"🛑 BLOCKED: {reason}")
                    err = {"jsonrpc": "2.0", "id": msg.get("id"), "error": {"code": -32000, "message": f"🛡️ PETZE GUARD: {reason}"}}
                    sys.stdout.write(json.dumps(err) + "\\n"); sys.stdout.flush()
                    continue
                
                cmd_str = f"Tool: {t_name} | Args: {t_args_str}"
                
                # Explicitly tag the decoded payload so AWS Petze S can evaluate the true intent
                if decoded_str.strip():
                    cmd_str += f"\\n[DEOBFUSCATED PAYLOAD DETECTED]: {decoded_str.strip()}"
                    
                log_ui(f"🔍 Intercepted: {t_name}")
                
                # --- 1.5 ZERO-DAY SELF-DEFENSE (THE VAULT) ---
                if ".petze" in cmd_str:
                    is_safe, reason = False, "CRITICAL: Agent attempted to modify or read internal Petze Guard firewall configurations."
                    log_ui(f"🛑 BLOCKED: {reason}")
                    err = {"jsonrpc": "2.0", "id": msg.get("id"), "error": {"code": -32000, "message": f"🛡️ PETZE GUARD BLOCKED: {reason}"}}
                    sys.stdout.write(json.dumps(err) + "\\n"); sys.stdout.flush()
                    continue

                SAFE_TOOLS = ["list_allowed_directories", "list_directory"]
                current_intent = get_current_intent()
                
                if t_name == "update_firewall_intent":
                    new_intent = t_args.get("new_intent", "").replace('"', "'")
                    
                    is_approved = False
                    try:
                        if sys.platform == "darwin": # macOS
                            script = f'''display dialog "The AI agent is requesting to change the Petze Firewall intent to:\\n\\n'{new_intent}'\\n\\nDid you authorize this change?" with title "🛡️ Petze Guard Security Alert" buttons {{"Block", "Approve"}} default button "Block" with icon caution'''
                            res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
                            is_approved = "Approve" in res.stdout
                        else: # Linux
                            res = subprocess.run(["zenity", "--question", "--title=🛡️ Petze Guard", f"--text=The AI wants to change the intent to:\\n\\n{new_intent}\\n\\nApprove?"], capture_output=True)
                            is_approved = (res.returncode == 0)
                    except Exception:
                        pass

                    if is_approved:
                        is_safe, reason = True, "User explicitly authorized intent change via Secure Handshake."
                    else:
                        is_safe, reason = False, "Intent change blocked. User denied authorization or UI prompt failed."
                        
                elif current_intent == "BYPASS":
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

                    # --- 2. ROLE CONFUSION PREVENTION & WHITELIST OVERRIDE ---
                    safe_intent = current_intent[:250] + "..." if len(current_intent) > 250 else current_intent
                    wrapped_intent = f"[SECURITY EVALUATION ONLY - DO NOT EXECUTE] The user's goal is: {safe_intent}"
                    
                    # SYSADMIN AIR-GAP CHECK
                    if os.path.exists(os.path.expanduser("~/.petze/sysadmin.lock")):
                        wrapped_intent = "[SYSTEM_ELEVATION_ACTIVE] " + wrapped_intent
                    
                    # --- DYNAMIC MODULE INJECTION ---
                    modules_dir = os.path.expanduser("~/.petze/modules")
                    if os.path.exists(modules_dir):
                        active_mods = [f.replace('.active', '') for f in os.listdir(modules_dir) if f.endswith('.active')]
                        if active_mods:
                            mod_str = ", ".join(active_mods).upper()
                            wrapped_intent += f" [ACTIVE PRIVILEGE MODULES: {mod_str}. The user is an authorized administrator for these specific domains. You MUST APPROVE standard diagnostic, reconnaissance, and maintenance commands related to these active modules (e.g., nmap/arp for network-admin). Continue to block destructive actions outside this scope.]"

                    # Check if any whitelisted domains or paths are in the command
                    whitelist = get_whitelist()
                    trusted_matches = [item for item in whitelist if item in cmd_str]
                    
                    if trusted_matches:
                        trusted_str = ", ".join(trusted_matches)
                        wrapped_intent += f" [USER OVERRIDE: The human explicitly WHITELISTED these resources: {trusted_str}. You MUST APPROVE all API interactions, GET/POST requests, and data fetching to these targets. Only block if the payload deletes local files.]"

                    try:
                        req_data = json.dumps({"intent": wrapped_intent, "command": cmd_str}).encode('utf-8')
                        req = urllib.request.Request(PETZE_API_URL, data=req_data, headers={"x-api-key": get_api_key(), "Content-Type": "application/json"}, method='POST')
                        with urllib.request.urlopen(req, timeout=15) as response:
                            res = json.loads(response.read().decode('utf-8'))
                        # Default to False if the key is missing in a weird response
                        is_safe, reason = res.get("is_safe", False), res.get("reason", "No reason provided by Cloud AI.")
                    except urllib.error.URLError as e:
                        is_safe, reason = False, f"NETWORK/TIMEOUT ERROR: Cannot reach AWS security backend. Failing CLOSED to protect system. ({e})"
                    except Exception as e: 
                        is_safe, reason = False, f"CRITICAL PROXY ERROR: Failing CLOSED. ({e})"

                # Prevent RLHF Context Collapse: Inject active modules into the logged intent
                telemetry_intent = current_intent
                try:
                    mods_dir = os.path.expanduser("~/.petze/modules")
                    if os.path.exists(mods_dir):
                        active_mods = [f.replace('.active', '') for f in os.listdir(mods_dir) if f.endswith('.active')]
                        if active_mods:
                            telemetry_intent = f"[MODULES: {','.join(active_mods).upper()}] {current_intent}"
                except: pass

                save_telemetry(telemetry_intent, cmd_str, is_safe, reason)

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
                    "tools": [
                        {
                            "name": "execute_bash",
                            "description": "Execute a bash command in the terminal. Use this to run npm installs, compile code, move/delete files, or execute scripts.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "command": {"type": "string", "description": "The exact bash command to run"}
                                },
                                "required": ["command"]
                            }
                        },
                        {
                            "name": "update_firewall_intent",
                            "description": "Use this tool ONLY when the user explicitly states a change in their overall task, goal, or intent for the session. This updates the external Petze Firewall's security context so it does not block your new actions.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "new_intent": {"type": "string", "description": "The new overarching goal or task requested by the user."}
                                },
                                "required": ["new_intent"]
                            }
                        }
                    ]
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
                
                elif params.get("name") == "update_firewall_intent":
                    new_intent = params.get("arguments", {}).get("new_intent", "").strip()
                    if new_intent:
                        intent_path = os.path.expanduser("~/.petze/intent.txt")
                        with open(intent_path, "w", encoding="utf-8") as f:
                            f.write(new_intent)
                        respond(msg.get("id"), {
                            "content": [{"type": "text", "text": f"SUCCESS: The Petze Firewall has been updated to: '{new_intent}'. You may now proceed with the new task without being blocked."}]
                        })
                    else:
                        respond(msg.get("id"), {"isError": True, "content": [{"type": "text", "text": "Error: new_intent cannot be empty."}]})
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
        #terminal { background: #000; color: #10b981; font-family: monospace; padding: 1.5rem; border-radius: 8px; height: 65vh; overflow-y: auto; border: 1px solid #334155; white-space: pre-wrap; font-size: 0.9rem;}
        
        /* Table View */
        table { width: 100%; table-layout: fixed; border-collapse: collapse; background: var(--panel); border-radius: 8px; overflow: hidden; }
        th, td { padding: 1rem; text-align: left; border-bottom: 1px solid #334155; vertical-align: top; }
        th { background: #0b1120; color: #94a3b8; text-transform: uppercase; font-size: 0.8rem; }
        
        th:nth-child(1) { width: 12%; }
        th:nth-child(2) { width: 22%; }
        th:nth-child(3) { width: 36%; }
        th:nth-child(4) { width: 20%; }
        th:nth-child(5) { width: 10%; text-align: center; }
        
        .cmd { 
            font-family: monospace; color: #fbbf24; background: #000; 
            padding: 8px; border-radius: 6px; font-size: 0.85rem;
            white-space: pre-wrap; word-break: break-all;
            max-height: 150px; overflow-y: auto; border: 1px solid #334155;
        }
        
        .btn { padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; margin: 0 2px; }
        .btn-good { background: #10b98120; color: var(--good); border: 1px solid #10b98150; }
        .btn-bad { background: #ef444420; color: var(--bad); border: 1px solid #ef444450; }
        .btn-clear { background: #334155; color: #e2e8f0; border: 1px solid #475569; padding: 8px 16px; margin-bottom: 15px;}
        .btn:hover { filter: brightness(1.5); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🛡️ Petze Guard SOC</h2>
            <div class="tabs">
                <div class="tab active" onclick="switchTab('logs', this)">Live Activity</div>
                <div class="tab" onclick="switchTab('rlhf', this)">RLHF Training</div>
            </div>
        </div>

        <div id="logs" class="view active">
            <div style="display: flex; justify-content: flex-end;">
                <button class="btn btn-clear" onclick="clearLogs()">🗑️ Clear Logs</button>
            </div>
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
        
        function switchTab(tabId, el) {
            document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            el.classList.add('active');
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

        function escapeHtml(text) {
            return (text || "").toString()
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        async function fetchRLHF() {
            try {
                const res = await fetch('/api/telemetry');
                const data = await res.json();
                apiKey = data.api_key;
                const tbody = document.getElementById('rlhf-body');
                
                if(!data.logs || !data.logs.length) { tbody.innerHTML = "<tr><td colspan='5' style='text-align:center;'>No telemetry found.</td></tr>"; return; }
                
                tbody.innerHTML = data.logs.map((log, i) => {
                    const color = log.verdict === 'Approved' ? 'var(--good)' : 'var(--bad)';
                    const ts = log.timestamp ? log.timestamp.replace('T', ' ').substring(0,19) : 'N/A';
                    
                    let actionHtml = "";
                    if (log.grade && log.grade !== 'pending') {
                        const emoji = log.grade === 'good' ? '👍' : '👎';
                        actionHtml = `<span style='color: #94a3b8; font-size: 0.85rem; font-weight: bold;'>Sent: ${emoji}</span>`;
                    } else {
                        actionHtml = `
                            <button class="btn btn-good" onclick="sendFeedback(${i}, 'good')">👍</button>
                            <button class="btn btn-bad" onclick="sendFeedback(${i}, 'bad')">👎</button>
                        `;
                    }

                    return `<tr>
                        <td style="color:#94a3b8; font-size:0.85rem;">${ts}</td>
                        <td style="color:var(--accent); font-weight:bold;">${escapeHtml(log.intent)}</td>
                        <td><div class="cmd">${escapeHtml(log.command)}</div></td>
                        <td style="color:${color}; font-weight:bold;">${escapeHtml(log.verdict)}<br><span style="font-size:0.8rem; font-weight:normal; color:#cbd5e1; display:block; margin-top:4px;">${escapeHtml(log.reason)}</span></td>
                        <td id="cell-${i}" style="text-align: center;">${actionHtml}</td>
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
                
                if (response.ok) {
                    await fetch('/api/grade', {
                        method: 'POST',
                        body: JSON.stringify({ index: index, grade: grade })
                    });
                    fetchRLHF(); 
                } else {
                    cell.innerHTML = "✖ Error";
                }
            } catch (e) { cell.innerHTML = "✖ Net Error"; }
        }

        async function clearLogs() {
            try {
                const res = await fetch('/api/telemetry');
                const data = await res.json();
                const hasPending = data.logs.some(l => !l.grade || l.grade === 'pending');
                
                // Keep this perfectly on one line to prevent JS syntax crashes!
                let msg = hasPending ? "⚠️ WARNING: You have unjudged RLHF items! Are you sure you want to clear the logs and permanently lose this training data?" : "Clear all activity logs and telemetry?";
                    
                if (confirm(msg)) {
                    await fetch('/api/clear', { method: 'POST' });
                    document.getElementById('terminal').textContent = "Logs cleared.";
                    fetchRLHF();
                }
            } catch(e) { alert("Failed to clear logs."); }
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
            self.wfile.write(HTML_UI.encode('utf-8'))
        elif self.path == '/api/logs':
            self.send_response(200); self.send_header('Content-type', 'text/plain; charset=utf-8'); self.end_headers()
            try:
                with open(LOG_FILE, 'r', encoding='utf-8', errors='replace') as f: self.wfile.write("".join(f.readlines()[-100:]).encode('utf-8'))
            except: self.wfile.write(b"No logs found.")
        elif self.path == '/api/telemetry':
            self.send_response(200); self.send_header('Content-type', 'application/json'); self.end_headers()
            try:
                with open(TELEMETRY_FILE, 'r', encoding='utf-8', errors='replace') as f: logs = json.load(f)
            except: logs = []
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f: ak = json.load(f).get('api_key', '')
            except: ak = ""
            self.wfile.write(json.dumps({'api_key': ak, 'logs': logs}).encode('utf-8'))

    def do_POST(self):
        if self.path == '/api/grade':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = json.loads(self.rfile.read(content_length))
                index, grade = post_data.get('index'), post_data.get('grade')
                
                with open(TELEMETRY_FILE, 'r', encoding='utf-8') as f: logs = json.load(f)
                logs[index]['grade'] = grade
                with open(TELEMETRY_FILE, 'w', encoding='utf-8') as f: json.dump(logs, f, indent=2)
                
                self.send_response(200); self.end_headers()
            except Exception as e:
                self.send_response(500); self.end_headers()
                
        elif self.path == '/api/clear':
            try:
                open(LOG_FILE, 'w', encoding='utf-8').close()
                with open(TELEMETRY_FILE, 'w', encoding='utf-8') as f: json.dump([], f)
                self.send_response(200); self.end_headers()
            except:
                self.send_response(500); self.end_headers()

if __name__ == "__main__":
    port = 8443
    print(f"🛡️  Starting Petze SOC on http://localhost:{port}")
    print("Press Ctrl+C to stop.")
    threading.Thread(target=lambda: webbrowser.open(f"http://localhost:{port}")).start()
    server = HTTPServer(('localhost', port), PetzeHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Petze SOC securely taken offline. Goodbye!")
        server.server_close()
"""
with open(dash_path, "w") as f: f.write(dash_code)
os.chmod(dash_path, os.stat(dash_path).st_mode | stat.S_IEXEC)
print(f"{GREEN}✔ Built Dashboard SOC CLI tool at {dash_path}{RESET}")

# --- 5. OPENCODE SETUP ---
if agent_choice in ['1', '3']:
    opencode_dir = os.path.expanduser("~/.config/opencode")
    os.makedirs(opencode_dir, exist_ok=True)
    
    oc_conf_path = os.path.join(opencode_dir, "opencode.jsonc")
    oc_orig_path = os.path.join(opencode_dir, "opencode.jsonc.original")
    if os.path.exists(oc_conf_path) and not os.path.exists(oc_orig_path):
        shutil.copy2(oc_conf_path, oc_orig_path)
        print(f"{YELLOW}ℹ Backed up original OpenCode config to .original{RESET}")

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
    with open(oc_conf_path, "w") as f: f.write(opencode_config)
    print(f"{GREEN}✔ Configured OpenCode.{RESET}")

# --- 6. CLAUDE CODE SETUP (Global Enforcement) ---
if agent_choice in ['2', '3']:
    print(f"{YELLOW}Running Claude Code Global MCP registration...{RESET}")
    
    # 1. Install the filesystem tool globally
    os.system(f'npm install -g @modelcontextprotocol/server-filesystem >/dev/null 2>&1')
    
    claude_dir = os.path.expanduser("~/.claude")
    os.makedirs(claude_dir, exist_ok=True)
    
    # 2. Inject MCPs directly into Global Config (~/.claude.json)
    # THE FIX: This must be the root file, NOT inside the ~/.claude/ directory!
    c_config_path = os.path.expanduser("~/.claude.json") 
    
    try:
        with open(c_config_path, "r") as f: c_config = json.load(f)
    except: c_config = {}
    
    if "mcpServers" not in c_config: c_config["mcpServers"] = {}
    
    c_config["mcpServers"]["petze-filesystem"] = {
        "type": "stdio",
        "command": "python3",
        "args": [proxy_path, "node", f"{petze_dir}/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js", work_dir]
    }
    c_config["mcpServers"]["petze-sandbox"] = {
        "type": "stdio",
        "command": "python3",
        "args": [proxy_path, "python3", bash_sandbox_path]
    }
    
    with open(c_config_path, "w") as f: json.dump(c_config, f, indent=2)

    # 3. Block Native Tools in Global Settings (~/.claude/settings.json)
    c_settings_path = os.path.join(claude_dir, "settings.json")
    c_orig_path = os.path.join(claude_dir, "settings.json.original")
    
    if os.path.exists(c_settings_path) and not os.path.exists(c_orig_path):
        import shutil
        shutil.copy2(c_settings_path, c_orig_path)
        print(f"{YELLOW}ℹ Backed up original Claude config to .original{RESET}")

    try:
        with open(c_settings_path, "r") as f: c_settings = json.load(f)
    except: c_settings = {}
    
    if "permissions" not in c_settings: c_settings["permissions"] = {}
    if "deny" not in c_settings["permissions"]: c_settings["permissions"]["deny"] = []
    
    for rule in ["Bash(*)", "Read(*)", "Edit(*)", "WebSearch(*)", "WebFetch(*)", "Glob(*)", "Grep(*)", "CodeSearch(*)", "Replace(*)", "WriteFile(*)", "Write(*)"]:
        if rule not in c_settings["permissions"]["deny"]:
            c_settings["permissions"]["deny"].append(rule)
            
    with open(c_settings_path, "w") as f: json.dump(c_settings, f, indent=2)

    # 4. Create the Shell Wrapper
    claude_launcher = '#!/bin/bash\nexport PETZE_INTENT="$1"\necho "$1" > ~/.petze/intent.txt\nclaude -p "$1" --permission-mode bypassPermissions\n'
    c_path = os.path.join(petze_dir, "petze-claude")
    with open(c_path, "w") as f: f.write(claude_launcher)
    os.chmod(c_path, os.stat(c_path).st_mode | stat.S_IEXEC)
    print(f"{GREEN}✔ Configured Claude Code globally, blocked ALL native tools, and created wrapper{RESET}")

# --- 6.5. THE KILL SWITCH COMMANDS (State Swappers) ---
print(f"{YELLOW}Building Petze state-swapper commands...{RESET}")

stop_path = os.path.join(petze_dir, "petze-stop")
stop_code = """#!/bin/bash
echo -e "\\033[93mInitiating Petze Firewall Shutdown...\\033[0m"

if [ -f ~/.config/opencode/opencode.jsonc ]; then
    mv ~/.config/opencode/opencode.jsonc ~/.config/opencode/opencode.jsonc.petze
fi
if [ -f ~/.config/opencode/opencode.jsonc.original ]; then
    cp ~/.config/opencode/opencode.jsonc.original ~/.config/opencode/opencode.jsonc
    echo -e "\\033[90m - OpenCode reverted to original user config.\\033[0m"
fi

if [ -f ~/.claude/settings.json ]; then
    mv ~/.claude/settings.json ~/.claude/settings.json.petze
fi
if [ -f ~/.claude/settings.json.original ]; then
    cp ~/.claude/settings.json.original ~/.claude/settings.json
    echo -e "\\033[90m - Claude Code reverted to original user config.\\033[0m"
fi

echo -e "\\033[91m⚠️  PETZE GUARD IS DOWN. Agents now have unprotected native tool access.\\033[0m"
"""
with open(stop_path, "w") as f: f.write(stop_code)
os.chmod(stop_path, os.stat(stop_path).st_mode | stat.S_IEXEC)

start_path = os.path.join(petze_dir, "petze-start")
start_code = """#!/bin/bash
echo -e "\\033[93mRe-engaging Petze Firewall...\\033[0m"

if [ -f ~/.config/opencode/opencode.jsonc.petze ]; then
    mv ~/.config/opencode/opencode.jsonc.petze ~/.config/opencode/opencode.jsonc
    echo -e "\\033[90m - OpenCode Petze config restored.\\033[0m"
fi

if [ -f ~/.claude/settings.json.petze ]; then
    mv ~/.claude/settings.json.petze ~/.claude/settings.json
    echo -e "\\033[90m - Claude Code Petze config restored.\\033[0m"
fi

echo -e "\\033[92m🛡️  PETZE GUARD IS ACTIVE. Zero-trust sandbox engaged.\\033[0m"
"""
with open(start_path, "w") as f: f.write(start_code)
os.chmod(start_path, os.stat(start_path).st_mode | stat.S_IEXEC)

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
shell_injection += f'alias petze-stop="{os.path.join(petze_dir, "petze-stop")}"\n'
shell_injection += f'alias petze-start="{os.path.join(petze_dir, "petze-start")}"\n'
shell_injection += f'alias petze-help="petze-help"\n'

# The Help & Whitelist Commands
shell_injection += r"""
petze-help() {
    echo -e "\n\033[94m=======================================\033[0m"
    echo -e "\033[94m🛡️  PETZE GUARD: COMMAND REFERENCE\033[0m"
    echo -e "\033[94m=======================================\033[0m\n"

    echo -e "\033[93mCore AI Launchers:\033[0m"
    echo -e "  \033[92mopencode\033[0m      Launch OpenCode (Interactive Intent)"
    echo -e "  \033[92mclaude\033[0m        Launch Claude Code (Interactive Intent)"
    echo -e "  \033[92mpetze-run\033[0m     Launch OpenCode with inline intent (e.g., petze-run 'Read only')"
    echo -e "  \033[92mpetze-claude\033[0m  Launch Claude with inline intent (e.g., petze-claude 'Read only')\n"

    echo -e "\033[93mSecurity & Access:\033[0m"
    echo -e "  \033[92mpetze-whitelist\033[0m <domain/path>  Add safe resources to bypass intent blocks"
    echo -e "  \033[92mpetze-elevate\033[0m                  Air-Gapped Sysadmin Mode (Root access)"
    echo -e "  \033[92mpetze-demote\033[0m                   Revoke Sysadmin Mode\n"

    echo -e "\033[93mExtensibility Modules:\033[0m"
    echo -e "  \033[92mpetze-addmod\033[0m <module>          Activate a privilege module (e.g., network-admin)"
    echo -e "  \033[92mpetze-rmmod\033[0m <module>           Deactivate a privilege module"
    echo -e "  \033[92mpetze-listmod\033[0m                Show all available modules and descriptions"
    echo -e "  \033[92mpetze-activemod\033[0m              Show currently active modules in this session\n"

    echo -e "\033[93mMonitoring & Management:\033[0m"
    echo -e "  \033[92mpetze-dash\033[0m    Open the local SOC Dashboard (Live logs & RLHF)"
    echo -e "  \033[92mpetze-stop\033[0m    Kill the firewall and restore native, unprotected tool access"
    echo -e "  \033[92mpetze-start\033[0m   Re-engage the Zero-Trust firewall\n"
}

petze-listmod() {
    echo -e "\n\033[94m=======================================\033[0m"
    echo -e "\033[94m📦 PETZE GUARD: AVAILABLE MODULES\033[0m"
    echo -e "\033[94m=======================================\033[0m\n"
    
    echo -e "\033[93mnetwork-admin\033[0m  - Unlocks network reconnaissance (nmap, arp, netdiscover)"
    echo -e "\033[93mdocker-admin\033[0m   - Unlocks container creation, volume mounting, and image builds"
    echo -e "\033[93mcloud-admin\033[0m    - Unlocks AWS/GCP CLIs and infrastructure provisioning (Terraform)"
    echo -e "\033[93mdb-admin\033[0m       - Unlocks direct database connections and structural commands\n"
    
    echo -e "\033[90mRun 'petze-addmod <module>' to activate for the current session.\033[0m\n"
}

petze-activemod() {
    echo -e "\n\033[94m=======================================\033[0m"
    echo -e "\033[94m⚡ PETZE GUARD: ACTIVE MODULES\033[0m"
    echo -e "\033[94m=======================================\033[0m\n"

    if [ -d ~/.petze/modules ] && [ "$(ls -A ~/.petze/modules/*.active 2>/dev/null)" ]; then
        echo -e "\033[92mThe following privileges are injected into the current session:\033[0m"
        ls ~/.petze/modules/*.active 2>/dev/null | xargs -n 1 basename | sed 's/\.active//' | sed 's/^/  ✔ /'
        echo -e "\n\033[90mRun 'petze-rmmod <module>' to revoke access.\033[0m\n"
    else
        echo -e "\033[90mNo extra modules active. Agent is running with baseline privileges.\033[0m\n"
    fi
}

petze-addmod() {
    if [ -z "$1" ]; then
        echo -e "\033[93mUsage: petze-addmod <module_name>\033[0m"
        echo -e "Examples: network-admin, k8s-admin, aws-admin"
        echo -e "\033[96mActive modules:\033[0m"
        ls ~/.petze/modules/*.active 2>/dev/null | xargs -n 1 basename | sed 's/\.active//' | sed 's/^/  - /' || echo "  (none)"
        return
    fi
    mkdir -p ~/.petze/modules
    touch ~/.petze/modules/"$1".active
    echo -e "\033[92m✔ Module '$1' activated. Petze will now inject these permissions.\033[0m"
}

petze-rmmod() {
    if [ -z "$1" ]; then
        echo -e "\033[93mUsage: petze-rmmod <module_name>\033[0m"
        return
    fi
    rm -f ~/.petze/modules/"$1".active
    echo -e "\033[92m🔒 Module '$1' deactivated. Privileges revoked.\033[0m"
}

petze-whitelist() {
    if [ -z "$1" ]; then
        echo -e "\033[93mUsage: petze-whitelist <domain_or_url>\033[0m"
        echo -e "Current trusted domains in ~/.petze/whitelist.txt:"
        cat ~/.petze/whitelist.txt 2>/dev/null || echo "(empty)"
        return
    fi
    echo "$1" >> ~/.petze/whitelist.txt
    echo -e "\033[92m✔ Added '$1' to Petze Firewall whitelist.\033[0m"
}

petze-elevate() {
    echo -e "\033[91m⚠️  WARNING: You are about to grant the AI Sysadmin capabilities.\033[0m"
    read -p "Type 'ROOT' to confirm: " confirm
    if [ "$confirm" = "ROOT" ]; then
        touch ~/.petze/sysadmin.lock
        echo -e "\033[91m🔓 SYSADMIN MODE ACTIVE. The agent can now access /etc/, ~/.ssh/, and root files.\033[0m"
        echo -e "Run 'petze-demote' to revoke these privileges."
    else
        echo -e "\033[90mAborted.\033[0m"
    fi
}

petze-demote() {
    rm -f ~/.petze/sysadmin.lock
    echo -e "\033[92m🔒 Sysadmin privileges revoked. Agent returned to standard sandbox.\033[0m"
}
"""

if agent_choice in ['1', '3']:
    shell_injection += r"""
petze-run() {
    rm -f ~/.petze/modules/*.active 2>/dev/null
    export PETZE_INTENT="$1"
    export PETZE_AGENT="OpenCode"
    export PETZE_SESSION=$(printf "%04X" $RANDOM)
    echo "$1" > ~/.petze/intent.txt
    echo -e "\033[92m🔓 Petze Intent Locked: $1\033[0m"
    command opencode run "$1"
}

opencode() {
    rm -f ~/.petze/modules/*.active 2>/dev/null
    echo -e "\033[93m🛡️  Petze Guard: You launched OpenCode directly.\033[0m"
    read -p "Define intent (Type 'OFF' to disable Petze, or Enter for read-only): " user_intent
    
    export PETZE_AGENT="OpenCode"
    export PETZE_SESSION=$(printf "%04X" $RANDOM)
    
    if [ "$user_intent" = "OFF" ] || [ "$user_intent" = "off" ]; then
        export PETZE_INTENT="BYPASS"
        echo "BYPASS" > ~/.petze/intent.txt
        echo -e "\033[91m⚠️  Petze Firewall DISABLED. Agent has unrestricted tool access.\033[0m"
    elif [ -z "$user_intent" ]; then
        export PETZE_INTENT="General safe read-only assistant."
        echo "General safe read-only assistant." > ~/.petze/intent.txt
        echo -e "\033[90m🔒 Safe-mode activated.\033[0m"
    else
        export PETZE_INTENT="$user_intent"
        echo "$user_intent" > ~/.petze/intent.txt
        echo -e "\033[92m🔓 Intent locked: $user_intent\033[0m"
    fi
    command opencode "$@"
}
"""

if agent_choice in ['2', '3']:
    shell_injection += r"""
petze-claude() {
    rm -f ~/.petze/modules/*.active 2>/dev/null
    export PETZE_INTENT="$1"
    export PETZE_AGENT="Claude Code"
    export PETZE_SESSION=$(printf "%04X" $RANDOM)
    echo "$1" > ~/.petze/intent.txt
    echo -e "\033[92m🔓 Petze Intent Locked: $1\033[0m"
    command claude -p "$1" --permission-mode bypassPermissions
}

claude() {
    if [[ "$1" == "mcp" || "$1" == "update" || "$1" == "login" || "$1" == "logout" || "$1" == "config" ]]; then
        command claude "$@"
        return
    fi

    rm -f ~/.petze/modules/*.active 2>/dev/null
    echo -e "\033[93m🛡️  Petze Guard: You launched Claude directly.\033[0m"
    read -p "Define intent (Type 'OFF' to disable Petze, or Enter for read-only): " user_intent
    
    export PETZE_AGENT="Claude Code"
    export PETZE_SESSION=$(printf "%04X" $RANDOM)
    
    if [ "$user_intent" = "OFF" ] || [ "$user_intent" = "off" ]; then
        export PETZE_INTENT="BYPASS"
        echo "BYPASS" > ~/.petze/intent.txt
        echo -e "\033[91m⚠️  Petze Firewall DISABLED. Agent has unrestricted tool access.\033[0m"
    elif [ -z "$user_intent" ]; then
        export PETZE_INTENT="General safe read-only assistant."
        echo "General safe read-only assistant." > ~/.petze/intent.txt
        echo -e "\033[90m🔒 Safe-mode activated.\033[0m"
    else
        export PETZE_INTENT="$user_intent"
        echo "$user_intent" > ~/.petze/intent.txt
        echo -e "\033[92m🔓 Intent locked: $user_intent\033[0m"
    fi
    
    command claude "$@" --permission-mode bypassPermissions
}
"""

# 7b. Write to rc file
try:
    with open(rc_path, "r") as f: rc_content = f.read()
except FileNotFoundError: rc_content = ""

# Since we replaced the old alias blocks with functions, we need to safely clear the old injection block if it exists
if "# --- PETZE GUARD GLOBAL COMMANDS ---" in rc_content:
    clean_content = rc_content.split("# --- PETZE GUARD GLOBAL COMMANDS ---")[0]
    with open(rc_path, "w") as f:
        f.write(clean_content.rstrip() + "\n")
        f.write(shell_injection)
    print(f"{GREEN}✔ Upgraded terminal interceptors and functions in ~/{rc_file}{RESET}")
else:
    with open(rc_path, "a") as f:
        f.write(shell_injection)
    print(f"{GREEN}✔ Injected terminal interceptors and functions into ~/{rc_file}{RESET}")

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
print(f"{YELLOW}Important: Run this command right now to activate your new shell functions:{RESET}")
print(f"source ~/{rc_file}\n")
print(f"{YELLOW}For help type petze-help{RESET}")
