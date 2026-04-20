---
trigger: always_on
---

# API Error Handling Rule

You are a Senior Frontend Engineer. Whenever you write or modify API fetching logic, you MUST implement robust error handling to prevent silent UI failures.

---

## 🛑 Silent Failure Prevention

### 1. HTTP 204 No Content
* **Definition:** A successful API request that intentionally returns no body.
* **Problem:** Many JSON parsers (like `response.json()`) will throw an error when attempting to parse an empty string, causing the application to silently fail and drop execution.
* **Requirement:** You MUST check for `response.status === 204` before attempting to parse the response body as JSON.

### 2. Awaiting Promises & UI Updates
* **Definition:** Updating a React state (or similar UI state) after an asynchronous API call completes.
* **Problem:** Firing an asynchronous reload function without `await` might result in stale data rendering before the backend finishes processing. Conversely, overly eager loading spinners can cause UI flicker.
* **Requirement:** Ensure API wrapping functions properly use `async/await` throughout the entire call chain so that data refetching is guaranteed to occur chronologically *after* the mutation succeeds.

---

## 🕵️ API Handling Review Checklist
1. Am I blindly calling `response.json()` without checking checking if the body actually contains JSON or if the status is 204?
2. If this is a `DELETE` or `PUT` request, does the backend return a 204? Have I accounted for that?
3. Am I catching API errors and visually informing the user, rather than just `console.error`?
