# HTTP Server Design

This is a future design note. RecHarness v0.2 does not include a full HTTP
server.

Potential endpoints:

- `POST /assist`
- `POST /verify`
- `POST /parse`
- `GET /catalogs`
- `GET /health`

The request and response bodies should use the same stable schemas as the SDK
and MCP tools:

- `AssistRequest` / `AssistResponse`
- `VerifyRequest` / `VerifyResponse`
- `ParseRequest` / `ParseResponse`

Errors should use stable response envelopes and should not expose raw Python
exceptions to clients.
