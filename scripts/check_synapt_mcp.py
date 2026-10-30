"""Check live Synapt MCP discovery and read-only provider tools."""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cyber_assistant.config import get_settings  # noqa: E402
from cyber_assistant.synapt.client import SynaptClient  # noqa: E402


async def main() -> int:
    settings = get_settings()
    client = SynaptClient(
        provider_id=settings.synapt_provider_id,
        mcp_url=settings.synapt_mcp_url,
        auth_base=settings.synapt_auth_base,
        username=settings.synapt_username,
        password=settings.synapt_password,
        top_k=settings.synapt_top_k,
        ca_bundle=settings.synapt_ca_bundle or None,
    )
    if not client.configured:
        print("Synapt configuration is incomplete; values were not displayed.")
        return 2
    try:
        tools = await client.connect_and_discover()
        print("MCP connection: successful")
        print("Remote tools: " + ", ".join(sorted(t["name"] for t in tools if "name" in t)))
        await client.get_schema()
        print("Provider schema tool: successful")
        await client.get_stats()
        print("Provider stats tool: successful")
        return 0
    except Exception as exc:
        print(f"Synapt MCP check failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
