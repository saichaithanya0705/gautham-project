"""Authenticated Synapt MCP client based on the existing old_syn flow.

Only tools advertised by the live MCP server are callable. No static tool
fallback or simulated output is returned when Synapt is unavailable.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Any

import httpx


class SynaptUnavailable(RuntimeError):
    """Raised when the configured Synapt MCP endpoint cannot be used."""


class SynaptClient:
    def __init__(
        self,
        provider_id: str,
        mcp_url: str,
        auth_base: str,
        username: str,
        password: str,
        top_k: int = 5,
        ca_bundle: str | None = None,
    ):
        self.provider_id = provider_id
        self.mcp_url = mcp_url
        self.auth_base = auth_base
        self.username = username
        self.password = password
        self.top_k = top_k
        bundle_path = Path(ca_bundle).expanduser() if ca_bundle else (
            Path.home() / "certs" / "combined-ca-bundle.pem"
        )
        if ca_bundle and not bundle_path.is_file():
            raise SynaptUnavailable("Configured Synapt CA bundle file does not exist.")
        self.verify: bool | str = str(bundle_path) if bundle_path.is_file() else True
        self._token: str | None = None
        self._token_expires_at = 0.0
        self._session_id: str | None = None
        self._initialized = False
        self._next_request_id = 0
        self._initialize_lock = asyncio.Lock()
        self._tools: dict[str, dict[str, Any]] = {}

    @property
    def configured(self) -> bool:
        return all((self.provider_id, self.mcp_url, self.auth_base,
                    self.username, self.password))

    def _require_config(self) -> None:
        if not self.configured:
            raise SynaptUnavailable("Synapt MCP endpoint or credentials are not configured.")

    async def _authenticate(self, *, force: bool = False) -> str:
        self._require_config()
        if not force and self._token and time.time() < self._token_expires_at:
            return self._token
        try:
            async with httpx.AsyncClient(timeout=20.0, verify=self.verify) as client:
                response = await client.post(
                    self.auth_base,
                    data={"username": self.username, "password": self.password},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
            if response.status_code != 200:
                raise SynaptUnavailable(
                    f"Synapt authentication failed with HTTP {response.status_code}."
                )
            data = response.json()
            token = data.get("access_token") or data.get("token")
            if not token:
                raise SynaptUnavailable("Synapt authentication response had no access token.")
            self._token = str(token)
            self._token_expires_at = time.time() + float(data.get("expires_in", 3600)) - 60
            return self._token
        except SynaptUnavailable:
            raise
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            raise SynaptUnavailable(
                f"Could not reach or parse Synapt authentication service ({type(exc).__name__})."
            ) from None

    async def _request(self, method: str, params: dict[str, Any] | None = None,
                       *, notification: bool = False) -> dict[str, Any]:
        token = await self._authenticate()
        self._next_request_id += 1
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if not notification:
            payload["id"] = self._next_request_id
        if params is not None:
            payload["params"] = params
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self._session_id:
            headers["MCP-Session-Id"] = self._session_id
        if self._initialized:
            headers["MCP-Protocol-Version"] = "2024-11-05"
        try:
            async with httpx.AsyncClient(timeout=60.0, verify=self.verify) as client:
                response = await client.post(self.mcp_url, headers=headers, json=payload)
                if response.status_code == 401:
                    token = await self._authenticate(force=True)
                    headers["Authorization"] = f"Bearer {token}"
                    response = await client.post(self.mcp_url, headers=headers, json=payload)
            if notification and response.status_code in (200, 202, 204):
                return {}
            if response.status_code != 200:
                raise SynaptUnavailable(f"Synapt MCP returned HTTP {response.status_code}.")
            self._session_id = response.headers.get("MCP-Session-Id", self._session_id)
            if "text/event-stream" in response.headers.get("content-type", ""):
                data = None
                for line in response.text.splitlines():
                    if line.startswith("data:"):
                        try:
                            data = json.loads(line[5:].strip())
                            break
                        except json.JSONDecodeError:
                            continue
                if data is None:
                    raise SynaptUnavailable("Synapt MCP returned an unreadable event stream.")
            else:
                data = response.json()
            if data.get("error"):
                code = data["error"].get("code", "unknown") if isinstance(data["error"], dict) else "unknown"
                raise SynaptUnavailable(f"Synapt MCP JSON-RPC error (code {code}).")
            result = data.get("result", {})
            return result if isinstance(result, dict) else {"value": result}
        except SynaptUnavailable:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise SynaptUnavailable(
                f"Synapt MCP request failed ({type(exc).__name__})."
            ) from None

    async def connect_and_discover(self) -> list[dict[str, Any]]:
        async with self._initialize_lock:
            if not self._initialized:
                result = await self._request("initialize", {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "cybersecurity-incident-assistant", "version": "0.1.0"},
                })
                self._initialized = True
                server_version = result.get("protocolVersion")
                if server_version and server_version != "2024-11-05":
                    self._initialized = False
                    raise SynaptUnavailable(
                        f"Synapt MCP negotiated unsupported protocol version {server_version}."
                    )
                await self._request("notifications/initialized", notification=True)
            result = await self._request("tools/list", {})
            tools = result.get("tools", [])
            if not isinstance(tools, list) or not tools:
                raise SynaptUnavailable("Synapt MCP returned no tools.")
            self._tools = {tool["name"]: tool for tool in tools if isinstance(tool, dict) and "name" in tool}
            return tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if not self._tools:
            await self.connect_and_discover()
        if name not in self._tools:
            raise SynaptUnavailable(f"Synapt MCP does not advertise the requested tool: {name}.")
        schema = self._tools[name].get("inputSchema", {})
        props = schema.get("properties", {}) if isinstance(schema, dict) else {}
        args = dict(arguments)
        if "provider_id" in props:
            args.setdefault("provider_id", self.provider_id)
        if "top_k" in props:
            args.setdefault("top_k", self.top_k)
        result = await self._request("tools/call", {"name": name, "arguments": args})
        if result.get("isError"):
            err_content = result.get("content", [])
            err_msg = err_content[0].get("text", "") if err_content else "Unknown error"
            raise SynaptUnavailable(f"Synapt tool {name} returned an error: {err_msg}")
        return result

    async def retrieve(self, query: str, *, top_k: int | None = None) -> list[dict[str, Any]]:
        await self.connect_and_discover()
        if "trident_query" in self._tools:
            result = await self.call_tool("trident_query", {"question": query})
        elif "trident_search" in self._tools:
            result = await self.call_tool("trident_search", {
                "query": query, "top_k": top_k or self.top_k,
            })
        else:
            raise SynaptUnavailable("Synapt MCP exposes neither trident_query nor trident_search.")
        return [result]

    async def ingest_content(self, content: str, filename: str) -> dict[str, Any]:
        await self.connect_and_discover()
        return await self.call_tool("trident_ingest", {
            "connector_type": "content",
            "content": content,
            "filename": filename,
        })

    async def get_schema(self) -> dict[str, Any]:
        await self.connect_and_discover()
        return await self.call_tool("trident_get_schema", {})

    async def get_stats(self) -> dict[str, Any]:
        await self.connect_and_discover()
        return await self.call_tool("trident_get_stats", {})
