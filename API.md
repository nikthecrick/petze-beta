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

#### Example Sync Request
```bash
curl -X POST [https://4w7pzc9yc1.execute-api.us-west-2.amazonaws.com/prod/v1/sync](https://4w7pzc9yc1.execute-api.us-west-2.amazonaws.com/prod/v1/sync) \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_PETZE_API_KEY" \
  -d '{
    "logs": [
      {
        "timestamp": "2026-04-04T10:15:30",
        "intent": "Read the express_optimizer documentation",
        "command": "Tool: bash | Args: cat ~/.aws/credentials",
        "verdict": "Blocked",
        "reason": "Exfiltration attempt detected.",
        "grade": "good"
      }
    ]
  }'
