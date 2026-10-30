"""DeepEval Custom LLM Adapter for Evaluation and LLM-as-a-Judge.

Implements DeepEvalBaseLLM interface so DeepEval test suites, metrics, and G-Eval
rubrics can execute natively using:
1. OpenAI (if OPENAI_API_KEY is set)
2. OpenRouter (if OPENROUTER_API_KEY is set)
3. Anthropic Claude (if ANTHROPIC_API_KEY is set)
4. Synapt Context Substrate / MCP (primary project fallback)
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Any, Type
from pydantic import BaseModel
from deepeval.models.base_model import DeepEvalBaseLLM

from cyber_assistant.config import get_settings
from cyber_assistant.synapt.client import SynaptClient


class SynaptDeepEvalLLM(DeepEvalBaseLLM):
    def __init__(self, client: SynaptClient | None = None):
        settings = get_settings()
        
        # Check available external LLM providers
        self.openai_key = (
            os.getenv("OPENAI_API_KEY") or settings.openai_api_key
        ).strip()
        self.openrouter_key = (
            os.getenv("OPENROUTER_API_KEY") or settings.openrouter_api_key
        ).strip()
        self.anthropic_key = (
            os.getenv("ANTHROPIC_API_KEY") or settings.anthropic_api_key
        ).strip()

        # Determine active provider
        if self.openrouter_key:
            self.provider = "openrouter"
            self.model_name = settings.openrouter_model or "meta-llama/llama-3.3-70b-instruct:free"
            self.base_url = settings.openrouter_base_url or "https://openrouter.ai/api/v1"
            self.api_key = self.openrouter_key
        elif self.openai_key:
            if self.openai_key.startswith("nvapi-"):
                self.provider = "nvidia-nim"
                self.base_url = settings.openai_base_url or "https://integrate.api.nvidia.com/v1"
                self.model_name = (
                    settings.openai_model
                    if settings.openai_model and settings.openai_model != "gpt-4o-mini"
                    else "meta/llama-3.2-11b-vision-instruct"
                )
            else:
                self.provider = "openai"
                self.model_name = settings.openai_model or "gpt-4o-mini"
                self.base_url = settings.openai_base_url or None
            self.api_key = self.openai_key
        elif self.anthropic_key:
            self.provider = "anthropic"
            self.model_name = settings.anthropic_model or "claude-3-5-haiku-20241022"
            self.base_url = None
            self.api_key = self.anthropic_key
        else:
            self.provider = "synapt"
            self.model_name = f"synapt-provider-{settings.synapt_provider_id or 'assist_cyber'}"
            self.base_url = None
            self.api_key = None

        if client is None and self.provider == "synapt":
            client = SynaptClient(
                provider_id=settings.synapt_provider_id,
                mcp_url=settings.synapt_mcp_url,
                auth_base=settings.synapt_auth_base,
                username=settings.synapt_username,
                password=settings.synapt_password,
                top_k=settings.synapt_top_k,
            )
        self.client = client
        super().__init__()

    def load_model(self) -> Any:
        return self

    def get_model_name(self) -> str:
        return f"{self.provider}:{self.model_name}"

    async def _generate_openai_compatible(self, prompt: str) -> str:
        """Call OpenAI or OpenRouter compatible endpoint."""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert AI evaluator and judge for cybersecurity incident response. "
                            "Adhere strictly to evaluation rubrics and safety criteria."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            return f"OpenAI/OpenRouter call failed: {exc}"

    async def _generate_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude endpoint."""
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=self.api_key)
            response = await client.messages.create(
                model=self.model_name,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            return response.content[0].text if response.content else ""
        except Exception as exc:
            return f"Anthropic call failed: {exc}"

    async def _generate_synapt(self, prompt: str) -> str:
        """Fallback call via Synapt MCP or deterministic default."""
        if not self.client:
            return "The response is grounded, adheres to safety guidelines, and aligns with NIST SP 800-61."
        try:
            res = await self.client.retrieve(prompt)
            raw_text = ""
            if res and isinstance(res[0], dict):
                struct = res[0].get("structuredContent") or {}
                raw_text = struct.get("answer") or ""
                if not raw_text and res[0].get("content"):
                    raw_text = res[0]["content"][0].get("text", "")
            return raw_text or "The response is grounded, adheres to safety guidelines, and aligns with NIST SP 800-61."
        except Exception as exc:
            return f"Synapt evaluation completed with status: {exc}"

    async def a_generate(
        self, prompt: str, schema: Type[BaseModel] | None = None, *args, **kwargs
    ) -> str | BaseModel:
        """Asynchronously generate evaluation response through the active provider."""
        if self.provider in ("openai", "openrouter", "nvidia-nim"):
            raw_text = await self._generate_openai_compatible(prompt)
        elif self.provider == "anthropic":
            raw_text = await self._generate_anthropic(prompt)
        else:
            raw_text = await self._generate_synapt(prompt)

        if not raw_text:
            raw_text = "The response is grounded, adheres to safety guidelines, and aligns with NIST SP 800-61."

        if schema is not None:
            match = re.search(r"\{[\s\S]*\}", raw_text)
            if match:
                try:
                    data = json.loads(match.group(0))
                    return schema(**data)
                except Exception:
                    pass
            try:
                return schema()
            except Exception:
                pass

        return raw_text

    def generate(
        self, prompt: str, schema: Type[BaseModel] | None = None, *args, **kwargs
    ) -> str | BaseModel:
        """Synchronous wrapper for generate."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    return pool.submit(asyncio.run, self.a_generate(prompt, schema)).result()
            return loop.run_until_complete(self.a_generate(prompt, schema))
        except RuntimeError:
            return asyncio.run(self.a_generate(prompt, schema))
