"""
LLM Gateway service — multi-provider LLM interface.

Supports OpenAI-compatible, Anthropic, and local providers.
Handles provider selection, fallback, token tracking, and rate limiting.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
from sqlalchemy import select

from ..core.config import settings

logger = logging.getLogger(__name__)

# Rate limiter: simple in-memory token bucket per provider
_rate_limits: dict[str, list[float]] = {}


@dataclass
class ToolCall:
    """A tool/function call from the LLM."""

    id: str
    name: str
    arguments: str  # JSON string


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""

    content: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    raw_response: dict[str, Any] = field(default_factory=dict)
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str = "stop"


@dataclass
class LLMProviderConfig:
    """Configuration for an LLM provider."""

    provider: str
    base_url: str
    api_key: str
    model: str
    max_tokens: int = 4096
    temperature: float = 0.1
    rate_limit_rpm: int = 60
    is_active: bool = True


def _get_default_provider() -> LLMProviderConfig:
    """Get the default provider from application settings."""
    return LLMProviderConfig(
        provider=settings.LLM_PROVIDER,
        base_url=settings.LLM_BASE_URL,
        api_key=settings.LLM_API_KEY,
        model=settings.LLM_MODEL,
        max_tokens=settings.LLM_MAX_TOKENS,
        temperature=settings.LLM_TEMPERATURE,
    )


def get_provider_from_db(provider_name: str | None = None) -> LLMProviderConfig | None:
    """Load provider config from database (sync, for use in Celery workers).

    Args:
        provider_name: Specific provider to load, or None for the default.

    Returns:
        Provider config or None if not found/inactive.
    """
    try:
        from db import LLMConfig

        from ..worker.db import get_sync_session

        with get_sync_session() as session:
            if provider_name:
                result = session.execute(
                    select(LLMConfig).where(
                        LLMConfig.provider == provider_name,
                        LLMConfig.is_active == True,  # noqa: E712
                    )
                )
            else:
                result = session.execute(
                    select(LLMConfig).where(
                        LLMConfig.is_default == True,  # noqa: E712
                        LLMConfig.is_active == True,  # noqa: E712
                    )
                )
            config = result.scalar_one_or_none()

            if config is None:
                return None

            return LLMProviderConfig(
                provider=config.provider,
                base_url=config.base_url,
                api_key=config.api_key_encrypted or "",
                model=config.default_model,
                max_tokens=config.max_tokens,
                temperature=float(config.temperature),
                rate_limit_rpm=config.rate_limit_rpm or 60,
                is_active=config.is_active,
            )
    except Exception as e:
        logger.warning(f"Failed to load LLM config from DB: {e}")
        return None


def _check_rate_limit(provider: str, rpm: int) -> bool:
    """Check if we're within rate limits for this provider."""
    if rpm <= 0:
        return True  # No rate limit

    now = time.time()
    if provider not in _rate_limits:
        _rate_limits[provider] = []

    # Remove timestamps older than 60 seconds
    _rate_limits[provider] = [t for t in _rate_limits[provider] if now - t < 60]

    if len(_rate_limits[provider]) >= rpm:
        return False

    _rate_limits[provider].append(now)
    return True


def _call_openai_compatible(
    config: LLMProviderConfig,
    messages: list[dict[str, Any]],
    temperature: float | None = None,
    max_tokens: int | None = None,
    response_format: dict | None = None,
    tools: list[dict[str, Any]] | None = None,
) -> LLMResponse:
    """Call an OpenAI-compatible API (OpenAI, local, vLLM, etc.)."""
    url = f"{config.base_url.rstrip('/')}/chat/completions"
    headers = {
        "Content-Type": "application/json",
    }
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"

    payload: dict[str, Any] = {
        "model": config.model,
        "messages": messages,
        "temperature": temperature if temperature is not None else config.temperature,
        "max_tokens": max_tokens or config.max_tokens,
    }
    if response_format:
        payload["response_format"] = response_format
    if tools:
        payload["tools"] = tools

    start = time.time()
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(url, json=payload, headers=headers)
        resp.raise_for_status()

    latency_ms = int((time.time() - start) * 1000)
    data = resp.json()

    usage = data.get("usage", {})
    message = data["choices"][0]["message"]
    content = message.get("content") or ""
    finish_reason = data["choices"][0].get("finish_reason", "stop")

    # Parse tool calls if present
    parsed_tool_calls = []
    if message.get("tool_calls"):
        for tc in message["tool_calls"]:
            parsed_tool_calls.append(
                ToolCall(
                    id=tc["id"],
                    name=tc["function"]["name"],
                    arguments=tc["function"]["arguments"],
                )
            )

    return LLMResponse(
        content=content,
        provider=config.provider,
        model=config.model,
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
        total_tokens=usage.get("total_tokens", 0),
        latency_ms=latency_ms,
        raw_response=data,
        tool_calls=parsed_tool_calls,
        finish_reason=finish_reason,
    )


def _call_anthropic(
    config: LLMProviderConfig,
    messages: list[dict[str, Any]],
    temperature: float | None = None,
    max_tokens: int | None = None,
    response_format: dict | None = None,
    tools: list[dict[str, Any]] | None = None,
) -> LLMResponse:
    """Call the Anthropic Messages API."""
    url = f"{config.base_url.rstrip('/')}/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": config.api_key,
        "anthropic-version": "2023-06-01",
    }

    # Extract system message if present
    system_msg = None
    chat_messages = []
    for msg in messages:
        if msg["role"] == "system":
            system_msg = msg["content"]
        else:
            chat_messages.append(msg)

    payload: dict[str, Any] = {
        "model": config.model,
        "messages": chat_messages,
        "max_tokens": max_tokens or config.max_tokens,
        "temperature": temperature if temperature is not None else config.temperature,
    }
    if system_msg:
        payload["system"] = system_msg

    # Convert OpenAI tool format to Anthropic format
    if tools:
        anthropic_tools = []
        for tool in tools:
            anthropic_tools.append({
                "name": tool["function"]["name"],
                "description": tool["function"].get("description", ""),
                "input_schema": tool["function"].get("parameters", {"type": "object"}),
            })
        payload["tools"] = anthropic_tools

    start = time.time()
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(url, json=payload, headers=headers)
        resp.raise_for_status()

    latency_ms = int((time.time() - start) * 1000)
    data = resp.json()

    usage = data.get("usage", {})
    finish_reason = data.get("stop_reason", "end_turn")

    # Parse content and tool_use blocks
    content_parts = []
    parsed_tool_calls = []
    for block in data.get("content", []):
        if block["type"] == "text":
            content_parts.append(block["text"])
        elif block["type"] == "tool_use":
            parsed_tool_calls.append(
                ToolCall(
                    id=block["id"],
                    name=block["name"],
                    arguments=json.dumps(block["input"]),
                )
            )

    # Map Anthropic stop reasons to OpenAI finish reasons
    if finish_reason == "tool_use":
        finish_reason = "tool_calls"

    return LLMResponse(
        content="\n".join(content_parts),
        provider=config.provider,
        model=config.model,
        prompt_tokens=usage.get("input_tokens", 0),
        completion_tokens=usage.get("output_tokens", 0),
        total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
        latency_ms=latency_ms,
        raw_response=data,
        tool_calls=parsed_tool_calls,
        finish_reason=finish_reason,
    )


# Provider dispatch map
_PROVIDER_CALLERS = {
    "openai": _call_openai_compatible,
    "local": _call_openai_compatible,
    "anthropic": _call_anthropic,
}


def call_llm(
    messages: list[dict[str, Any]],
    provider_name: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    response_format: dict | None = None,
    fallback: bool = True,
    tools: list[dict[str, Any]] | None = None,
) -> LLMResponse:
    """Call an LLM provider with automatic fallback.

    Args:
        messages: Chat messages in OpenAI format [{role, content}].
        provider_name: Specific provider to use, or None for default.
        temperature: Override temperature.
        max_tokens: Override max tokens.
        response_format: Optional response format (e.g. {"type": "json_object"}).
        fallback: Whether to try fallback providers on failure.
        tools: Optional list of tool definitions in OpenAI format.

    Returns:
        LLMResponse with content and metadata.

    Raises:
        RuntimeError: If all providers fail.
    """
    # Try to get config from DB first, fall back to settings
    config = get_provider_from_db(provider_name)
    if config is None:
        config = _get_default_provider()
        if provider_name and provider_name != config.provider:
            logger.warning(
                f"Requested provider '{provider_name}' not found in DB, "
                f"using default: {config.provider}"
            )

    providers_tried = []
    last_error = None

    # Try the primary provider
    providers_to_try = [config]

    # If fallback is enabled, add other providers
    if fallback:
        for name in ["openai", "anthropic", "local"]:
            if name != config.provider:
                fb_config = get_provider_from_db(name)
                if fb_config and fb_config.is_active:
                    providers_to_try.append(fb_config)

    for provider_config in providers_to_try:
        provider = provider_config.provider
        providers_tried.append(provider)

        # Rate limit check
        if not _check_rate_limit(provider, provider_config.rate_limit_rpm):
            logger.warning(f"Rate limit exceeded for provider {provider}, trying next")
            last_error = f"Rate limit exceeded for {provider}"
            continue

        # Get the caller function
        caller = _PROVIDER_CALLERS.get(provider, _call_openai_compatible)

        try:
            response = caller(
                provider_config,
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                tools=tools,
            )
            logger.info(
                f"LLM call successful: provider={provider}, model={provider_config.model}, "
                f"tokens={response.total_tokens}, latency={response.latency_ms}ms"
            )
            return response

        except httpx.HTTPStatusError as e:
            logger.error(
                f"LLM HTTP error from {provider}: {e.response.status_code} - "
                f"{e.response.text[:200]}"
            )
            last_error = f"{provider}: HTTP {e.response.status_code}"
        except httpx.TimeoutException:
            logger.error(f"LLM timeout from {provider}")
            last_error = f"{provider}: timeout"
        except Exception as e:
            logger.error(f"LLM error from {provider}: {e}")
            last_error = f"{provider}: {str(e)[:200]}"

    raise RuntimeError(
        f"All LLM providers failed. Tried: {providers_tried}. Last error: {last_error}"
    )


def call_llm_json(
    messages: list[dict[str, str]],
    provider_name: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    fallback: bool = True,
) -> tuple[dict[str, Any], LLMResponse]:
    """Call LLM and parse response as JSON.

    Adds JSON instruction to the system message and attempts to parse the response.

    Args:
        messages: Chat messages.
        provider_name: Specific provider.
        temperature: Override temperature.
        max_tokens: Override max tokens.
        fallback: Whether to try fallback providers.

    Returns:
        Tuple of (parsed JSON dict, raw LLMResponse).

    Raises:
        RuntimeError: If LLM call fails.
        ValueError: If response cannot be parsed as JSON.
    """
    response = call_llm(
        messages=messages,
        provider_name=provider_name,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
        fallback=fallback,
    )

    # Try to parse JSON from response
    content = response.content.strip()

    # Handle markdown code blocks
    if content.startswith("```"):
        lines = content.split("\n")
        # Remove first and last lines (``` markers)
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines)

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON response: {e}\nContent: {content[:500]}")
        raise ValueError(f"LLM returned invalid JSON: {e}") from e

    return parsed, response


def check_provider_health(provider_name: str | None = None) -> dict[str, Any]:
    """Check health of an LLM provider.

    Args:
        provider_name: Provider to check, or None for default.

    Returns:
        Health status dict.
    """
    config = get_provider_from_db(provider_name)
    if config is None:
        config = _get_default_provider()

    try:
        response = call_llm(
            messages=[{"role": "user", "content": "Say 'ok'"}],
            provider_name=config.provider,
            max_tokens=5,
            fallback=False,
        )
        return {
            "provider": config.provider,
            "model": config.model,
            "status": "healthy",
            "latency_ms": response.latency_ms,
        }
    except Exception as e:
        return {
            "provider": config.provider,
            "model": config.model,
            "status": "unhealthy",
            "error": str(e)[:200],
        }
