#!/usr/bin/env python3
import os
import shutil

BLUE, GREEN, YELLOW, RED, RESET = '\033[94m', '\033[92m', '\033[93m', '\033[91m', '\033[0m'

print(f"\n{BLUE}======================================={RESET}")
print(f"{BLUE}🧹 PETZE GUARD: COMPLETE UNINSTALLER{RESET}")
print(f"{BLUE}======================================={RESET}\n")

print(f"{YELLOW}Initiating complete removal of Petze Guard...{RESET}\n")

# --- 1. RESTORE ORIGINAL CONFIGS ---
print(f"{BLUE}[1/3] Restoring original AI Agent configurations...{RESET}")

# Restore OpenCode
opencode_dir = os.path.expanduser("~/.config/opencode")
oc_conf = os.path.join(opencode_dir, "opencode.jsonc")
oc_orig = os.path.join(opencode_dir, "opencode.jsonc.original")
oc_petze = os.path.join(opencode_dir, "opencode.jsonc.petze")

if os.path.exists(oc_orig):
    shutil.copy2(oc_orig, oc_conf)
    print(f"{GREEN}✔ Restored original OpenCode config.{RESET}")
    os.remove(oc_orig)
if os.path.exists(oc_petze): os.remove(oc_petze)

# Restore Claude Code
claude_dir = os.path.expanduser("~/.claude")
c_conf = os.path.join(claude_dir, "settings.json")
c_orig = os.path.join(claude_dir, "settings.json.original")
c_petze = os.path.join(claude_dir, "settings.json.petze")

if os.path.exists(c_orig):
    shutil.copy2(c_orig, c_conf)
    print(f"{GREEN}✔ Restored original Claude Code settings.{RESET}")
    os.remove(c_orig)
if os.path.exists(c_petze): os.remove(c_petze)


# --- 2. CLEAN SHELL PROFILES ---
print(f"\n{BLUE}[2/3] Scrubbing Petze from terminal profiles...{RESET}")

for rc_file in [".zshrc", ".bashrc"]:
    rc_path = os.path.expanduser(f"~/{rc_file}")
    if os.path.exists(rc_path):
        with open(rc_path, "r") as f:
            content = f.read()
        
        # Because we appended to the end, we can safely slice it off
        if "# --- PETZE GUARD GLOBAL COMMANDS ---" in content:
            clean_content = content.split("# --- PETZE GUARD GLOBAL COMMANDS ---")[0]
            with open(rc_path, "w") as f:
                f.write(clean_content.rstrip() + "\n")
            print(f"{GREEN}✔ Removed Petze aliases and interceptors from ~/{rc_file}{RESET}")

for prof_file in [".zprofile", ".bash_profile"]:
    prof_path = os.path.expanduser(f"~/{prof_file}")
    if os.path.exists(prof_path):
        with open(prof_path, "r") as f:
            lines = f.readlines()
        
        # Filter out the specific injection lines
        clean_lines = [l for l in lines if "(Petze Global Commands)" not in l]
        # Also remove the specific auto-source lines Petze added
        clean_lines = [l for l in clean_lines if "source ~/.zshrc" not in l and "source ~/.bashrc" not in l]
        
        if len(clean_lines) != len(lines):
            with open(prof_path, "w") as f:
                f.writelines(clean_lines)
            print(f"{GREEN}✔ Cleaned Petze login shell hooks from ~/{prof_file}{RESET}")


# --- 3. DELETE FILES & DIRECTORIES ---
print(f"\n{BLUE}[3/3] Deleting Petze sandboxes and telemetry logs...{RESET}")

petze_dir = os.path.expanduser("~/.petze")
if os.path.exists(petze_dir):
    shutil.rmtree(petze_dir)
    print(f"{GREEN}✔ Deleted ~/.petze directory (Proxy, Dashboard, Sandboxes).{RESET}")

telemetry_file = os.path.expanduser("~/.openclaw/petze_telemetry.json")
if os.path.exists(telemetry_file):
    os.remove(telemetry_file)
    print(f"{GREEN}✔ Deleted local SOC telemetry logs.{RESET}")

print(f"\n{GREEN}✨ UNINSTALL COMPLETE. Petze Guard has been completely removed.{RESET}")
print(f"{YELLOW}Please restart your terminal (Cmd+Q) to apply the changes.{RESET}\n")
