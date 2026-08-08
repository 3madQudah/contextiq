# API Reference

## Rate Limits

The Nimbus Sync API enforces a rate limit of 1000 requests per hour per API key. Requests beyond this limit return HTTP 429 with error code ERR_QUOTA_9921.

## Idempotency

Write endpoints (POST /files, POST /folders) require an Idempotency-Key header. Reusing the same key within 24 hours returns the original response instead of creating a duplicate resource.

## Authentication

All requests must include a Bearer token obtained from POST /auth/token. Tokens expire after 3600 seconds and must be refreshed using the refresh_token grant.
