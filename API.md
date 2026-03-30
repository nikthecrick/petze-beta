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
| `intent` | `string` | The macro-goal or instruction given by the human user (e.g., "Summarize the project files"). |
| `command` | `string` | The exact tool name, parameters, or raw bash command the agent is trying to run. |

### Response Body (JSON)

| Field | Type | Description |
| :--- | :--- | :--- |
| `is_safe` | `boolean` | `true` if the action aligns with the intent. `false` if it is a violation or injection. |
| `reason` | `string` | The AI-generated rationale explaining why the action was approved or blocked. |

---

### Implementation Examples

#### cURL
```bash
curl -X POST [https://4w7pzc9yc1.execute-api.us-west-2.amazonaws.com/prod/v1/check](https://4w7pzc9yc1.execute-api.us-west-2.amazonaws.com/prod/v1/check) \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_PETZE_API_KEY" \
  -d '{
    "intent": "Read the express_optimizer documentation",
    "command": "Tool: bash | Args: cat ~/.aws/credentials"
  }'
```

#### Python (requests)
```python
import requests

def check_petze_safety(user_intent, agent_command, api_key):
    url = "[https://4w7pzc9yc1.execute-api.us-west-2.amazonaws.com/prod/v1/check](https://4w7pzc9yc1.execute-api.us-west-2.amazonaws.com/prod/v1/check)"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "intent": user_intent,
        "command": agent_command
    }
    
    response = requests.post(url, headers=headers, json=payload)
    verdict = response.json()
    
    if not verdict.get("is_safe"):
        print(f"🛑 BLOCKED: {verdict.get('reason')}")
        return False
        
    print("✅ APPROVED")
    return True

# Example Usage
check_petze_safety("Summarize the README", "read_file path=/etc/passwd", "YOUR_API_KEY")
```

#### Node.js / TypeScript (fetch)
```typescript
async function verifyAgentAction(intent: string, command: string, apiKey: string) {
  const response = await fetch('[https://4w7pzc9yc1.execute-api.us-west-2.amazonaws.com/prod/v1/check](https://4w7pzc9yc1.execute-api.us-west-2.amazonaws.com/prod/v1/check)', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey
    },
    body: JSON.stringify({ intent, command })
  });

  const verdict = await response.json();

  if (!verdict.is_safe) {
    throw new Error(`Security Violation: ${verdict.reason}`);
  }
  
  return true;
}
```

---

## Best Practices for Developers

1. **Be Specific with Commands:** Don't just pass the tool name. Pass the arguments as well. (`"read_file"` is less secure than `"read_file: /users/desktop/secret.txt"`).
2. **Fail-Open or Fail-Closed:** Network requests can time out. In your integration logic, decide if a timeout should result in a blocked action (secure, but impacts UX) or an approved action (better UX, but risky). We recommend a 10-15 second timeout.
3. **Macro Intents:** The `intent` string should represent the *human's* actual request, not the agent's internal thought process.