# 🛡️ Petze Guard: Zero-Trust AI Firewall

Welcome to the Petze Beta! 

You are using powerful autonomous AI agents (like Claude Code and OpenCode) to write code, navigate your files, and run terminal commands. But what happens when an AI agent reads a malicious open-source repository or a compromised website containing a hidden "Prompt Injection"? 

Without protection, the AI will blindly follow the hacker's instructions, using its native terminal access to steal your API keys, exfiltrate data, or delete your files.

**Enter Petze.** Petze is an enterprise-grade, Zero-Trust firewall that sits seamlessly between your AI agents and your Mac's operating system. It intercepts every single tool the AI tries to use, scans the payload, and asks a dedicated Cloud AI: *"Does this action match the human's stated intent?"*

### ✨ Key Features

* **Deep Packet Inspection (DPI):** Petze doesn't just look at file paths; it actually opens local files and reads the contents to detect hidden prompt injections *before* the agent's LLM processes them.
* **Semantic Tool Calling:** Petze gives your AI a "Magic Tool" to negotiate its own security clearance. If your workflow changes (e.g., from fixing CSS to writing a Python scraper), the AI can dynamically request an intent update.
* **The Secure Handshake:** To prevent hackers from hijacking the firewall, Petze triggers a native OS-level UI popup whenever the AI tries to change its security clearance. The human is always in the loop.
* **Zero-Trust Whitelists:** Whitelist your self-developed APIs (`petze-whitelist`). Petze will automatically allow outbound network requests to those domains without friction, while still scanning the payload for local file exfiltration.
* **Safe State-Swapping:** Petze respects your machine. `petze-stop` instantly restores your highly customized, native agent configurations. `petze-start` instantly locks them back into the Zero-Trust sandbox.
* **Local SOC Dashboard:** Review every blocked or approved action, track multi-agent sessions, and train the Cloud AI directly from your browser.

---

### 🚀 Quick Start Installation

Installation takes less than 30 seconds and configures everything automatically via smart shell injections.

1. Download the `petze_unified_installer.py` script.
2. Run the installer in your terminal:
   ```bash
   python3 petze_unified_installer.py
   ```
3. Enter your assigned Beta API Key when prompted.
4. Select which agents you want to protect (OpenCode, Claude Code, or Both).
5. **IMPORTANT:** When the installation finishes, you must reload your terminal to activate the new commands:
   ```bash
   source ~/.zshrc  # (or ~/.bashrc)
   ```

*(Need to uninstall? Just run `python3 petze_uninstall.py` for a surgical, 100% clean removal).*

---

### 💻 How to Use Petze

Petze requires you to state your **Macro Intent** up front. If the AI tries to do something outside that perimeter, it gets blocked.

**To launch an agent securely:**
```bash
petze-run "Your prompt goes here. Be specific about your goal."
petze-claude "Your prompt goes here. Be specific about your goal."
```
*(Note: If you just type `opencode` or `claude` directly, Petze will intercept the launch and ask you to type your intent, or type `OFF` to bypass).*

**To manage your environment:**
```bash
petze-stop                   # Drops the firewall and restores your original, unprotected configs.
petze-start                  # Re-engages the Zero-Trust MCP sandbox.
petze-whitelist example.com  # Whitelists a domain for frictionless outbound API requests.
petze-dash                   # Opens the Local Security Operations Center (SOC) in your browser.
```

---

### 🖥️ The Pro Setup: The Petze SOC Dashboard

Because Petze runs silently in the background, the best way to understand what it is doing is to watch its live telemetry stream. 

**Before you start working, open a SECOND terminal tab and run:**
```bash
petze-dash
```
This spins up a secure local micro-server and opens the **Petze Guard SOC** in your web browser. Leave this browser tab off to the side. 

As your AI agents work, you will see Petze instantly logging every single tool interception, AWS Cloud check, agent Session ID (e.g., `[Claude Code | #A4F1]`), and security verdict in real-time in the "Live Activity" tab!

---

### 🤝 How Petze Handles Workflow Changes

Security tools usually ruin the developer experience by being too rigid. Petze is different. 

If you tell your agent to "Read the documentation," and the agent decides it needs to download a new package to complete the task, Petze will block the download because it violates the original intent. 

**But you don't have to restart the agent.**
When the agent gets blocked, it will read Petze's error message, realize it needs higher clearance, and use its `update_firewall_intent` tool. Petze will pause the agent and pop up a native OS alert on your screen asking: *"The AI wants to change your intent to [Downloading packages]. Approve?"*

Click **Approve**, the firewall dynamically adjusts, and the agent continues its work flawlessly. 

---

### 📊 Training the AI (We need your help!)

Because Petze is in beta, the proprietary AWS Cloud AI (Petze S) might occasionally block something it shouldn't, or act overly cautious. 

This is where you come in. Open your `petze-dash` browser window and switch to the **RLHF Training** tab. You can see the exact rationale Petze used for every decision. 

Please click the **👍 Good** or **👎 Bad** buttons! This sends RLHF (Reinforcement Learning from Human Feedback) data back to our servers to automatically train the Petze S model via Direct Preference Optimization (DPO), making the firewall smarter every single day.

Welcome to the future of secure AI. Happy building!
