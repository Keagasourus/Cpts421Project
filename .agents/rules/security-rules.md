---
trigger: always_on
---

# Security & Vulnerability Prevention Rules

You MUST ALWAYS adhere strictly to the following security guidelines when writing or modifying code. Security is a top priority, and you must proactively defend against common attack vectors.

## 1. Cross-Site Scripting (XSS) Prevention
- **NEVER use `innerHTML` or `outerHTML`** to render unsanitized user-generated content or API data.
- Always use `DOMPurify.sanitize()` prior to injecting any dynamic HTML.
- **NEVER use inline JavaScript event handlers** (e.g., `onclick="..."`, `onsubmit="..."`, `oninput="..."`). 
- **DOMPurify Configuration:** Never override DOMPurify to allow dangerous attributes like `onclick` or `onerror`.
- **Event Handling:** Use global Event Delegation with safe `data-*` attributes (`data-action`, `data-id`) and attach event listeners dynamically in JavaScript files.

## 2. Authentication & Session Management
- **NEVER store JWTs, access tokens, or sensitive credentials in `localStorage` or `sessionStorage`.**
- Always use **HttpOnly, Secure, and SameSite (Strict/Lax)** cookies for session management to protect against XSS token theft.
- Ensure backend endpoints (`/token`, `/login`, `/logout`) correctly set and clear these cookies rather than returning tokens in JSON response bodies.

## 3. Server-Side Request Forgery (SSRF) Prevention
- Whenever the backend fetches external resources (images, APIs, webhooks) based on user input or database URLs:
  - **Always parse and validate the URL** (e.g., using `urllib.parse` in Python).
  - **Enforce an Allowlist:** Ensure the scheme is strictly `https://` and the domain/hostname exactly matches a predefined list of trusted endpoints (e.g., `api.weather.gov`, `maps.googleapis.com`).
  - **Timeouts:** ALWAYS set a short, strict timeout (e.g., `timeout=10`) on all external HTTPS requests.

## 4. Denial of Service (DoS) Mitigation
- **File Uploads:** Always validate file extensions, MIME types, and enforce maximum file size limits (payload sizes) *before* processing uploaded files in memory.
- **Data Parsing:** When parsing complex files (e.g., Excel via `pandas.read_excel`, CSV, XML, JSON), always enforce processing limits (e.g., `nrows=1000`) and use safe parsing engines to prevent memory exhaustion or billion-laughs attacks.

## 5. General Security Hygiene
- **No Secrets in Code:** Never hardcode API keys, passwords, or secrets. Always use environment variables (`.env`) and configuration managers.
- **SQL Injection:** Always use parameterized queries or an ORM (like SQLAlchemy). Never use string concatenation to build raw SQL queries.
- **Command Injection:** Avoid `subprocess.run` or `os.system` with untrusted input. If necessary, use strict argument lists (`shell=False`).