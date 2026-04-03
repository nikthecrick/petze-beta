# 🛡️ Petze Guard: Zero-Trust AI Firewall

Welcome to the Petze Beta!

You are using powerful autonomous AI agents (like Claude Code and OpenCode) to write code, navigate your files, and run terminal commands. But what happens when an AI agent reads a malicious open-source repository or a compromised website containing a hidden "Prompt Injection"? 

Without protection, the AI will blindly follow the hacker's instructions, using its native terminal access to steal your API keys or delete your files.

**Enter Petze.** Petze is an enterprise-grade, Zero-Trust firewall that sits seamlessly between your AI agents and your Mac's operating system. It intercepts every single tool the AI tries to use, scans the payload, and asks a dedicated Cloud AI: *"Is this safe?"*

## ✨ Key Features

* **Intercept & Isolate:** Petze safely disables the dangerous native tools inside Claude Code and OpenCode, forcing them to route all actions through a secure Model Context Protocol (MCP) proxy.
* **Deep Packet Inspection (DPI):** Petze doesn't just look at file paths; it actually opens files and reads the contents to detect hidden prompt injections *before* the agent acts on them.
* **Cloud-Backed Verification:** Every command is instantly evaluated by an AWS-hosted Llama 3.1 model against your specific, stated intent.
* **The "Fast-Path":** Harmless context-gathering tools (like checking the current directory) are auto-approved locally for zero-latency performance.
* **Local SOC Dashboard:** Review every blocked or approved action in a beautiful local web interface and train the system directly from your machine.

## 🚀 Quick Start Installation

Installation takes less than 30 seconds and configures everything automatically.

1. Download the `petze_unified_installer.py` script.
2. Run the installer in your terminal:
   `python3 petze_unified_installer.py`
3. Enter your assigned Beta API Key when prompted.
4. Select which agents you want to protect (OpenCode, Claude Code, or Both).

**IMPORTANT:** When the installation finishes, completely close your terminal window (Cmd + Q) and open a new one to activate your global commands!

## 💻 How to Use Petze

Petze requires you to state your **Macro Intent** up front. If the AI agent tries to do something that doesn't match your intent, Petze will block it.

Instead of running your agents normally, use your new global wrapper commands:

**For OpenCode:**
`petze-run "Your prompt goes here. Be specific about what you want it to do."`

**For Claude Code:**
`petze-claude "Your prompt goes here. Be specific about what you want it to do."`

## 🧪 Beta Focus: Testing in Your Daily Workflow

For this phase of the beta, we are testing Petze's ability to seamlessly integrate into your daily workflow. The goal is to ensure the firewall is highly secure **without** being overly paranoid or blocking legitimate developer tasks.

We want you to use Petze for your real work:
* Ask it to scaffold a new React component.
* Have it read a massive log file and find a bug.
* Let it refactor a Python script and run the unit tests.

**The Kill Switches**
If Petze ever gets confused and blocks a legitimate complex workflow, you can easily temporarily bypass the firewall to give your AI its native tools back.
* Run `petze-stop` to instantly unhook the firewall (Naked AI mode).
* Run `petze-start` to instantly re-engage the Zero-Trust sandbox.

## 🖥️ The Pro Setup: The Live Security Monitor

Because Petze runs silently in the background, the best way to understand what it is doing is to watch its live telemetry stream. 

Before you start working, we highly recommend opening a SECOND terminal window and running this command:
`petze-dash`

This will spin up your local **Security Operations Center (SOC)** in your browser. Leave this window open off to the side. 
* On the **Live Activity** tab, you will see Petze instantly logging every single tool interception, AWS Cloud check, and security verdict in real-time as your AI works.
* On the **RLHF Training** tab, you can see the exact rationale Petze used for every decision.

## 📊 Training the AI (We need your help!)

Because Petze is in beta, the AWS Cloud AI might occasionally block something it shouldn't (or allow something weird). 

This is where you come in. Go to the **RLHF Training** tab in your `petze-dash` and review the verdicts. 
Please click the **👍 Good** or **👎 Bad** buttons! 

This sends RLHF (Reinforcement Learning from Human Feedback) data back to our servers. We use Direct Preference Optimization (DPO) to continuously train the firewall's brain, meaning your feedback directly makes the AI smarter for everyone.

Welcome to the future of secure AI. Happy building!
