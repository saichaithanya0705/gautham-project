# Synapt Connection Reference (Sanitized)

Use only the destination machine's local `.env` for credentials and provider
scope. Do not copy credentials from examples or commit `.env`.

The supplied connection specification described form-encoded authentication,
then MCP JSON-RPC `initialize` using protocol version `2024-11-05`, followed by
`tools/list` and `tools/call`. The provider ID must be passed where the live
tool schema supports it. The application's client discovers live tool schemas;
it does not assume a static tool count or return simulated tool results.

The platform UI showed a `POST /api/mcp/tool` route, while the supplied agent
guide described the Trident MCP endpoint. These are distinct interfaces; use
the endpoint and authentication flow confirmed for the actual runtime. Do not
change endpoint paths based only on the UI route.

On office networks with TLS inspection, use only a CA bundle approved by IT.
Keep certificate verification enabled. A TLS verification failure happens
before credentials are validated and should not be treated as an authentication
failure.
