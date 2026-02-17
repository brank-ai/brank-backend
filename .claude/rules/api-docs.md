# API Documentation Rules

ALWAYS update `brank-backend.postman_collection.json` when modifying API endpoints.

## When to Update
Any change to `api/routes.py`:
- Add/modify/remove endpoints
- Change request parameters (query, body, headers)
- Modify response structure or status codes

## What to Include
- Request details (method, URL, headers, body)
- Description with parameter details
- Example success responses (200, 201, etc.)
- Example error responses (400, 404, 500, etc.)
- Updated collection variables if needed

CI workflow (`check-postman.yml`) blocks PRs missing Postman updates for API changes.
