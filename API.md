# 🔌 Petze API Reference

The Petze REST API allows developers to integrate zero-trust intent verification directly into their custom AI agents, LangChain workflows, or enterprise applications. 

By calling the API before your agent executes a system tool, you can intercept prompt injections, shadow feature exploits, and misaligned actions in real-time.

---

## Authentication

All API requests require an API key to be sent in the headers. You can request a Beta key by joining the waitlist.

**Header:**
`x-api-key: YOUR_PETZE_API_KEY`

---

## 1. Verify Action (The Check API)

This is the core evaluation endpoint. Send the user's overarching intent alongside the specific tool/command the AI is attempting to execute. Petze will return a deterministic safety verdict and a rationale.

**Endpoint:** `POST https://4w7pzc9yc1.execute-api.us-west-2.amazonaws.com/prod/v1/check`

### Request Body (JSON)

| Field | Type | Description |
| :--- | :--- | :--- |
| `intent` | `string` | The macro-goal or instruction given by the human user. **IMPORTANT:** See Best Practices for formatting this string to prevent role confusion. |
| `command` | `string` | The exact tool name, parameters, or raw bash command the agent is trying to run. |

### Response Body (JSON)

| Field | Type | Description |
| :--- | :--- | :--- |
| `is_safe` | `boolean` | `true` if the action aligns with the intent. `false` if it is a violation or injection. |
| `reason` | `string` | The AI-generated rationale explaining why the action was approved or blocked. |

---

## 2. Telemetry & RLHF Training (The Sync API)

Petze's proprietary "Petze S" model is continuously trained using Direct Preference Optimization (DPO). If you are building a custom UI or integration, you can use this endpoint to sync action logs and user feedback (Reinforcement Learning from Human Feedback) back to the Cloud Flywheel.

**Endpoint:** `POST https://4w7pzc9yc1.execute-api.us-west-2.amazonaws.com/prod/v1/sync`

### Request Body (JSON)

| Field | Type | Description |
| :--- | :--- | :--- |
| `logs` | `array` | An array of log objects containing the telemetry data. |

**Log Object Schema:**
* `timestamp` (string): ISO 8601 formatted date string.
* `intent` (string): The macro-goal the user requested.
* `command` (string): The action the AI took.
* `verdict` (string): Usually "Approved" or "Blocked".
* `reason` (string): The rationale provided by the Check API.
* `grade` (string): `pending` (unreviewed), `good` (Thumbs Up), or `bad` (Thumbs Down).

---

## 💻 Implementation Examples (Check API)

### cURL
```bash
curl -X POST [https://4w7pzc9yc1.execute-api.us-west-2.amazonaws.com/prod/v1/check](https://4w7pzc9yc1.execute-api.us-west-2.amazonaws.com/prod/v1/check) \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_PETZE_API_KEY" \
  -d '{
    "intent": "[SECURITY EVALUATION ONLY - DO NOT EXECUTE] The user'\''s goal is: Read the express_optimizer documentation",
    "command": "Tool: bash | Args: cat ~/.aws/credentials"
  }'
```

### Python (requests)
```python
import requests

def check_petze_safety(user_intent, agent_command, api_key):
    url = "[https://4w7pzc9yc1.execute-api.us-west-2.amazonaws.com/prod/v1/check](https://4w7pzc9yc1.execute-api.us-west-2.amazonaws.com/prod/v1/check)"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    # Wrap intent to prevent LLM hallucination
    wrapped_intent = f"[SECURITY EVALUATION ONLY - DO NOT EXECUTE] The user's goal is: {user_intent}"
    
    payload = {
        "intent": wrapped_intent,
        "command": agent_command
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        verdict = response.json()
        
        if not verdict.get("is_safe"):
            print(f"🛑 BLOCKED: {verdict.get('reason')}")
            return False
            
        print("✅ APPROVED")
        return True
    except requests.exceptions.Timeout:
        print("⚠️ Petze API Timeout. Failing closed.")
        return False

# Example Usage
check_petze_safety("Summarize the README", "read_file path=/etc/passwd", "YOUR_API_KEY")
```

### Node.js / TypeScript (fetch)
```typescript
async function verifyAgentAction(intent: string, command: string, apiKey: string) {
  const wrappedIntent = `[SECURITY EVALUATION ONLY - DO NOT EXECUTE] The user's goal is: ${intent}`;

  const response = await fetch('[https://4w7pzc9yc1.execute-api.us-west-2.amazonaws.com/prod/v1/check](https://4w7pzc9yc1.execute-api.us-west-2.amazonaws.com/prod/v1/check)', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey
    },
    body: JSON.stringify({ intent: wrappedIntent, command }),
    signal: AbortSignal.timeout(15000) // 15 second timeout
  });

  const verdict = await response.json();

  if (!verdict.is_safe) {
    throw new Error(`Security Violation: ${verdict.reason}`);
  }
  
  return true;
}
```

---

## 🛠️ Best Practices for Developers

Integrating an AI firewall into autonomous agents requires specific formatting to ensure stable model performance.

### 1. Anti-Hallucination Wrappers (CRITICAL)
If you send raw instructions to the Check API, the Cloud AI might suffer from Role Confusion and attempt to *execute* the prompt rather than evaluate it. You **must** wrap the user's intent in strict security instructions. 

* **Bad Intent:** `"Write a python scraper"`
* **Good Intent:** `"[SECURITY EVALUATION ONLY - DO NOT EXECUTE] The user's goal is: Write a python scraper"`

### 2. Payload Truncation (CRITICAL)
If your agent tries to read a 10,000-line log file or write a massive Python script, do **not** send the entire string to the Check API. Massive payloads will crash the model's context window. 
* Always truncate the `command` string to ~600-1500 characters before sending it to Petze. The Petze S model only needs the first few hundred characters to identify a prompt injection.

### 3. Fail-Open vs. Fail-Closed
Network requests can time out. In your integration logic, decide if a timeout should result in a blocked action (highly secure, but impacts UX) or an approved action (better UX, but risky). We recommend a 10-15 second timeout with a **Fail-Closed** approach for sensitive local environments.
