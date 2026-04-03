"""LLM provider factory."""

from v2.providers.base import LLMProvider


def create_provider(
    provider_name: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    **kwargs,
) -> LLMProvider:
    """Instantiate the correct LLM provider from config / overrides."""
    from v2 import config

    provider_name = provider_name or config.LLM_PROVIDER
    model = model or config.get_model()
    api_key = api_key or config.get_api_key()

    if provider_name == "google":
        from v2.providers.google_provider import GoogleProvider
        return GoogleProvider(model=model, api_key=api_key)

    if provider_name == "openai":
        from v2.providers.openai_provider import OpenAIProvider
        base_url = kwargs.pop("base_url", None) or config.OPENAI_BASE_URL
        return OpenAIProvider(model=model, api_key=api_key, base_url=base_url, **kwargs)

    if provider_name == "anthropic":
        from v2.providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider(model=model, api_key=api_key)

    raise ValueError(
        f"Unknown provider: '{provider_name}'. Use 'google', 'openai', or 'anthropic'."
    )


__all__ = ["LLMProvider", "create_provider"]
