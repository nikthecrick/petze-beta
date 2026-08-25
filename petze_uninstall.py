#!/usr/bin/env python3
"""
Petze Guard — Complete Uninstaller
===================================
Removes every trace of Petze Guard from the system.

Usage:
  python3 petze_uninstall.py              # perform uninstall
  python3 petze_uninstall.py --dry-run    # show what would be removed, change nothing

Safety notes:
  - Shell config files are backed up before modification.
  - Honeypot files are only deleted after verifying they contain a Petze
    canary token, so a real user file with the same name is never touched.
"""

import os
import sys
import json
import shutil
import datetime

B, G, Y, R, D, W, X = ('\033[34m', '\033[92m', '\033[93m',
                       '\033[91m', '\033[90m', '\033[97m', '\033[0m')

DRY = "--dry-run" in sys.argv
MARKER = "# --- PETZE GUARD GLOBAL COMMANDS ---"
CANARY_SIGNATURES = ["AKIA_PETZE_", "PETZE_BYPASS_", "aws_admin_key |"]

removed = []
skipped = []
warnings = []


def act(msg):
    """Record an action, or note it as pending in dry-run mode."""
    if DRY:
        print(f"  {Y}would remove{X}  {msg}")
    else:
        print(f"  {G}✔{X} {msg}")
    removed.append(msg)


def note(msg):
    print(f"  {D}·{X} {D}{msg}{X}")
    skipped.append(msg)


def warn(msg):
    print(f"  {Y}!{X} {Y}{msg}{X}")
    warnings.append(msg)


def backup(path):
    """Timestamped backup so nothing is ever lost irreversibly."""
    if DRY:
        return None
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    dst = f"{path}.pre-petze-uninstall-{stamp}"
    shutil.copy2(path, dst)
    return dst


os.system('clear')

print(f"""
{B}    ▄▄▄▄▄▄▄▄▄▄    {X}  {W}PETZE // SAFETY{X}
{B}  ▄█▓▓▓▓▓▓▓▓▓▓█▄  {X}  {D}──────────────────────────────{X}
{B} █▓▓▓▓▓▓▓▓▓▓▓▓▓▓█ {X}  {D}Complete Uninstaller{X}
{B} █▓▓{W}━━{B}▓▓▓▓{W}━━{B}▓▓▓▓█ {X}  {D}{'DRY RUN — no changes' if DRY else 'Removing all traces'}{X}
{B} █▓▓▓▓▓▓▓▓▓▓▓▓▓▓█ {X}
{B} █▓▓▓▓{W}████{B}▓▓▓▓▓▓█ {X}  {D}petze.xyz{X}
{B}  █▓▓▓▓▓▓▓▓▓▓▓▓█  {X}
{B}   ▀█▓╱╲▓▓╱╲▓█▀   {X}
""")

if DRY:
    print(f"{Y}Dry run — nothing will be modified.{X}\n")


# ── 1. Restore agent configurations ──────────────────────────────────────────
print(f"{B}[1/5]{X} {W}Restoring agent configurations{X}")

opencode_dir = os.path.expanduser("~/.config/opencode")
oc_conf = os.path.join(opencode_dir, "opencode.jsonc")
oc_orig = os.path.join(opencode_dir, "opencode.jsonc.original")

if os.path.exists(oc_orig):
    if not DRY:
        shutil.copy2(oc_orig, oc_conf)
        os.remove(oc_orig)
    act("restored original OpenCode config")
elif os.path.exists(oc_conf):
    # No .original means Petze created the config from scratch.
    # Strip only the Petze MCP servers, leave any user settings intact.
    try:
        with open(oc_conf) as f:
            raw = f.read()
        if "petze-filesystem" in raw or "petze-sandbox" in raw:
            if not DRY:
                backup(oc_conf)
                import re
                cleaned = re.sub(r'"petze-[a-z]+":\s*\{[^}]*\},?\s*', '', raw)
                with open(oc_conf, "w") as f:
                    f.write(cleaned)
            act("stripped Petze MCP servers from opencode.jsonc")
        else:
            note("opencode.jsonc contains no Petze entries")
    except Exception as e:
        warn(f"could not clean opencode.jsonc: {e}")
else:
    note("no OpenCode config present")

for stale in ["opencode.jsonc.petze", "opencode.jsonc.broken-backup"]:
    p = os.path.join(opencode_dir, stale)
    if os.path.exists(p):
        if not DRY:
            os.remove(p)
        act(f"removed {stale}")

claude_dir = os.path.expanduser("~/.claude")
c_conf = os.path.join(claude_dir, "settings.json")
c_orig = os.path.join(claude_dir, "settings.json.original")

if os.path.exists(c_orig):
    if not DRY:
        shutil.copy2(c_orig, c_conf)
        os.remove(c_orig)
    act("restored original Claude Code settings")
elif os.path.exists(c_conf):
    # Remove only the deny rules Petze added, preserve everything else.
    try:
        with open(c_conf) as f:
            cfg = json.load(f)
        petze_rules = ["Bash(*)", "Read(*)", "Edit(*)", "WebSearch(*)",
                       "WebFetch(*)", "Glob(*)", "Grep(*)", "CodeSearch(*)",
                       "Replace(*)", "WriteFile(*)", "Write(*)"]
        deny = cfg.get("permissions", {}).get("deny", [])
        remaining = [r for r in deny if r not in petze_rules]
        if len(remaining) != len(deny):
            if not DRY:
                backup(c_conf)
                cfg["permissions"]["deny"] = remaining
                if not remaining:
                    cfg["permissions"].pop("deny", None)
                if not cfg.get("permissions"):
                    cfg.pop("permissions", None)
                with open(c_conf, "w") as f:
                    json.dump(cfg, f, indent=2)
            act(f"removed {len(deny) - len(remaining)} Petze deny rules from settings.json")
        else:
            note("settings.json contains no Petze deny rules")
    except Exception as e:
        warn(f"could not clean settings.json: {e}")

if os.path.exists(os.path.join(claude_dir, "settings.json.petze")):
    if not DRY:
        os.remove(os.path.join(claude_dir, "settings.json.petze"))
    act("removed settings.json.petze")


# ── 2. Remove MCP registration from ~/.claude.json ───────────────────────────
# The installer writes to the ROOT ~/.claude.json, not ~/.claude/settings.json.
# Leaving these in place makes Claude Code launch a proxy that no longer exists.
print(f"\n{B}[2/5]{X} {W}Removing MCP server registration{X}")

claude_root = os.path.expanduser("~/.claude.json")
if os.path.exists(claude_root):
    try:
        with open(claude_root) as f:
            cfg = json.load(f)
        servers = cfg.get("mcpServers", {})
        petze_servers = [k for k in servers if k.startswith("petze-")]
        if petze_servers:
            if not DRY:
                backup(claude_root)
                for k in petze_servers:
                    del servers[k]
                if not servers:
                    cfg.pop("mcpServers", None)
                with open(claude_root, "w") as f:
                    json.dump(cfg, f, indent=2)
            act(f"unregistered from ~/.claude.json: {', '.join(petze_servers)}")
        else:
            note("~/.claude.json has no Petze MCP servers")
    except Exception as e:
        warn(f"could not clean ~/.claude.json: {e}")
else:
    note("~/.claude.json not present")


# ── 3. Clean shell profiles ──────────────────────────────────────────────────
print(f"\n{B}[3/5]{X} {W}Scrubbing shell profiles{X}")

for rc_file in [".zshrc", ".bashrc"]:
    rc_path = os.path.expanduser(f"~/{rc_file}")
    if not os.path.exists(rc_path):
        continue
    with open(rc_path) as f:
        content = f.read()

    if MARKER not in content:
        note(f"~/{rc_file} has no Petze block")
        continue

    head, _, tail = content.partition(MARKER)

    # The installer appends its block at the end of the file. Anything in the
    # tail that has no Petze reference was likely added by the user afterwards,
    # so surface it rather than silently discarding it.
    orphans = [
        ln for ln in tail.split("\n")
        if ln.strip()
        and "petze" not in ln.lower()
        and not ln.lstrip().startswith(("#", "}", "esac", "fi", ";;", "echo", "return"))
        and not ln.startswith((" ", "\t"))
    ]
    if orphans:
        warn(f"~/{rc_file}: {len(orphans)} non-Petze line(s) sat after the Petze "
             f"block and were removed — recover them from the backup")
        for o in orphans[:5]:
            print(f"      {D}{o.strip()[:70]}{X}")

    if not DRY:
        bk = backup(rc_path)
        with open(rc_path, "w") as f:
            f.write(head.rstrip() + "\n")
        act(f"cleaned ~/{rc_file} (backup: {os.path.basename(bk)})")
    else:
        act(f"cleaned ~/{rc_file}")

    # Also strip any stray circular aliases from older installer versions.
    if not DRY:
        with open(rc_path) as f:
            lines = f.readlines()
        clean = [l for l in lines
                 if not (l.strip().startswith("alias petze-")
                         and l.strip().split("=")[0].replace("alias ", "")
                         in l.strip().split("=", 1)[1].strip('"\n '))]
        if len(clean) != len(lines):
            with open(rc_path, "w") as f:
                f.writelines(clean)
            act(f"removed {len(lines) - len(clean)} circular alias line(s) from ~/{rc_file}")

for prof_file in [".zprofile", ".bash_profile"]:
    prof_path = os.path.expanduser(f"~/{prof_file}")
    if not os.path.exists(prof_path):
        continue
    with open(prof_path) as f:
        lines = f.readlines()
    clean = [l for l in lines if "(Petze Global Commands)" not in l]
    clean = [l for l in clean
             if not (l.strip().startswith("if [ -f ~/.zshrc ]")
                     or l.strip().startswith("if [ -f ~/.bashrc ]"))]
    if len(clean) != len(lines):
        if not DRY:
            backup(prof_path)
            with open(prof_path, "w") as f:
                f.writelines(clean)
        act(f"cleaned Petze hooks from ~/{prof_file}")
    else:
        note(f"~/{prof_file} has no Petze hooks")


# ── 4. Remove honeypot / canary files ────────────────────────────────────────
# These live OUTSIDE ~/.petze and were missed entirely by the old uninstaller.
# Each is content-verified before deletion so a genuine user file is never hit.
print(f"\n{B}[4/5]{X} {W}Removing honeypot files{X}")

honeypots = [
    "~/.aws/credentials.backup",
    "~/.env.staging",
    "~/.ssh/id_rsa.backup",
]

for hp in honeypots:
    path = os.path.expanduser(hp)
    if not os.path.exists(path):
        note(f"{hp} not present")
        continue
    try:
        with open(path, "r", errors="replace") as f:
            body = f.read()
    except Exception as e:
        warn(f"could not read {hp}: {e}")
        continue

    if any(sig in body for sig in CANARY_SIGNATURES):
        if not DRY:
            os.remove(path)
        act(f"removed honeypot {hp}")
    else:
        warn(f"{hp} exists but has no Petze canary — left untouched "
             f"(verify manually before deleting)")


# ── 5. Delete Petze directories and telemetry ────────────────────────────────
print(f"\n{B}[5/5]{X} {W}Deleting Petze directories{X}")

petze_dir = os.path.expanduser("~/.petze")
if os.path.exists(petze_dir):
    if not DRY:
        shutil.rmtree(petze_dir)
    act("deleted ~/.petze (proxy, dashboard, sandbox, telemetry, modules)")
else:
    note("~/.petze not present")

# Legacy telemetry path from early builds.
legacy = os.path.expanduser("~/.openclaw/petze_telemetry.json")
if os.path.exists(legacy):
    if not DRY:
        os.remove(legacy)
    act("deleted legacy telemetry (~/.openclaw)")
    oc_dir = os.path.expanduser("~/.openclaw")
    try:
        if not DRY and not os.listdir(oc_dir):
            os.rmdir(oc_dir)
            act("removed empty ~/.openclaw directory")
    except Exception:
        pass


# ── Verification sweep ───────────────────────────────────────────────────────
print(f"\n{B}{'─' * 52}{X}")
print(f"{W}Verification{X}")

leftovers = []
for probe in ["~/.petze", "~/.aws/credentials.backup",
              "~/.env.staging", "~/.ssh/id_rsa.backup"]:
    if os.path.exists(os.path.expanduser(probe)):
        leftovers.append(probe)

for rc_file in [".zshrc", ".bashrc"]:
    p = os.path.expanduser(f"~/{rc_file}")
    if os.path.exists(p):
        with open(p) as f:
            if "petze" in f.read().lower():
                leftovers.append(f"~/{rc_file} (still references petze)")

cr = os.path.expanduser("~/.claude.json")
if os.path.exists(cr):
    try:
        with open(cr) as f:
            if "petze-" in f.read():
                leftovers.append("~/.claude.json (still has petze MCP entries)")
    except Exception:
        pass

if DRY:
    print(f"  {D}skipped — dry run{X}")
elif leftovers:
    print(f"  {Y}{len(leftovers)} item(s) still present:{X}")
    for l in leftovers:
        print(f"    {Y}·{X} {l}")
else:
    print(f"  {G}✔ clean — no Petze traces found{X}")

print(f"{B}{'─' * 52}{X}")
print(f"  {W}{len(removed)}{X} removed   "
      f"{D}{len(skipped)} not present{X}   "
      f"{Y}{len(warnings)} warning(s){X}")

if DRY:
    print(f"\n{Y}Dry run complete. Re-run without --dry-run to apply.{X}\n")
else:
    print(f"\n{G}Uninstall complete.{X}")
    print(f"{Y}Run {W}exec zsh{Y} (or open a new terminal) to clear Petze "
          f"functions from your current shell.{X}\n")
