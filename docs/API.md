# API Documentation

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required. Rate limiting is enforced per session ID.

---

## Endpoints

### POST /assist

Processes a user query and streams the response.

#### Request Headers

```
Content-Type: application/json
Accept: text/event-stream
```

#### Request Body

```json
{
  "query": {
    "id": "string (ULID)",
    "prompt": "string"
  },
  "session": {
    "processor_id": "YouTube Summarizer",
    "activity_id": "string (ULID)",
    "request_id": "string (ULID)",
    "interactions": []
  }
}
```

**Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query.id` | string | Yes | Unique query identifier (ULID format) |
| `query.prompt` | string | Yes | User's message (YouTube URL or question) |
| `session.processor_id` | string | Yes | Must be "YouTube Summarizer" |
| `session.activity_id` | string | Yes | Activity identifier (ULID format) |
| `session.request_id` | string | Yes | Request identifier (ULID format) |
| `session.interactions` | array | Yes | Previous interactions (empty for new sessions) |

#### Response

Server-Sent Events (SSE) stream with the following event types:

**Status Updates:**
```
data: {"type": "text_block", "id": "STATUS", "text": "Thinking about your query..."}
```

**Response Chunks:**
```
data: {"type": "text_chunk", "id": "FINAL_RESPONSE", "text": "chunk of text"}
```

**Completion:**
```
data: {"type": "done"}
```

#### Example Request

```bash
curl -N --location 'http://localhost:8000/assist' \
  --header 'Content-Type: application/json' \
  --data '{
    "query": {
        "id": "01K6YDCXXV62EJV0KAP7JEGCGP",
        "prompt": "Summarize https://youtu.be/dQw4w9WgXcQ"
    },
    "session": {
        "processor_id": "YouTube Summarizer",
        "activity_id": "01JR8SXE9B92YDKKNMYHYFZY1T",
        "request_id": "01JR8SY5PHB9X2FET1QRXGZW76",
        "interactions": []
    }
}'
```

---

## Response Types

### Success Response

**For YouTube URLs:**
Streams a structured summary with:
1. General summary (2-3 paragraphs)
2. Section breakdown with timestamps
3. Source URL footer

**For Identity Questions:**
Streams agent introduction and capabilities

**For Greetings:**
Streams friendly greeting with agent purpose

**For Non-YouTube Queries:**
Streams explanation of agent's YouTube-specific purpose

### Error Responses

**Invalid YouTube URL:**
```
❌ **Invalid YouTube URL**

**This could be due to:**
- Malformed or incomplete YouTube URL
- Missing characters in the video ID
- URL format not recognized
...
```

**Transcript Extraction Failed:**
```
❌ **Failed to extract transcript from video**

**This could be due to:**
- Video doesn't have English captions/subtitles
- Video is private or age restricted
...
```

**Rate Limit Exceeded:**
```
❌ **Rate Limit Exceeded**

Rate limit exceeded: 10 requests per minute. You have been temporarily blocked.

Please wait before making another request.
```

**Security Violation:**
```
❌ **Security Alert: Potential SQL injection detected**

**For your security:**
- Malicious patterns were detected in your input
- Please revise your request and try again
...
```

---

## Rate Limits

### Per User (Session ID)

| Limit | Value | Violation Response |
|-------|-------|-------------------|
| Requests per minute | 10 | 5-minute block |
| Requests per hour | 50 | 5-minute block |

### Platform-Wide

| Limit | Value |
|-------|-------|
| Concurrent queries | 200 |

**Note:** Greetings and identity questions are NOT rate-limited.

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success - streaming response |
| 422 | Validation error - check request format |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

---

## Generating ULIDs

For query IDs and session fields, use ULID format:

**Python:**
```python
import ulid
query_id = str(ulid.new())
```

**JavaScript:**
```javascript
import { ulid } from 'ulid';
const queryId = ulid();
```

**Command Line:**
```bash
python3 -c "import ulid; print(str(ulid.new()))"
```

---