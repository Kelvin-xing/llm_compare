import os
from openai import OpenAI
import anthropic
from google import genai

# ---------------------------------------------------------------------------
# Model Registry
# Each entry: display_name -> {provider, model_id, base_url (None = default), env_var}
# ---------------------------------------------------------------------------
MODEL_REGISTRY: dict[str, dict] = {
    "GPT-4o (OpenAI)": {
        "provider": "openai",
        "model_id": "gpt-4o",
        "base_url": None,
        "env_var": "OPENAI_API_KEY",
    },
    "GPT-4o-mini (OpenAI)": {
        "provider": "openai",
        "model_id": "gpt-4o-mini",
        "base_url": None,
        "env_var": "OPENAI_API_KEY",
    },
    "Claude Sonnet 4 (Anthropic)": {
        "provider": "anthropic",
        "model_id": "claude-sonnet-4-20250514",
        "base_url": None,
        "env_var": "ANTHROPIC_API_KEY",
    },
    "Gemini 2.0 Flash (Google)": {
        "provider": "gemini",
        "model_id": "gemini-2.0-flash",
        "base_url": None,
        "env_var": "GOOGLE_API_KEY",
    },
    "Qwen-Plus (Alibaba)": {
        "provider": "openai_compat",
        "model_id": "qwen-plus",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "env_var": "DASHSCOPE_API_KEY",
    },
    "Yi-Large (01.AI)": {
        "provider": "openai_compat",
        "model_id": "yi-large",
        "base_url": "https://api.01.ai/v1",
        "env_var": "YI_API_KEY",
    },
}

MODEL_NAMES = list(MODEL_REGISTRY.keys())


def _resolve_key(env_var: str, user_key: str | None) -> str:
    """Return user-provided key if non-empty, else fall back to env var."""
    if user_key and user_key.strip():
        return user_key.strip()
    key = os.environ.get(env_var, "")
    if not key:
        raise ValueError(
            f"No API key provided and environment variable {env_var} is not set."
        )
    return key


# ---------------------------------------------------------------------------
# Provider dispatch
# ---------------------------------------------------------------------------

def _call_openai(model_id: str, prompt: str, api_key: str, base_url: str | None) -> str:
    client = OpenAI(api_key=api_key, base_url=base_url)
    resp = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


def _call_anthropic(model_id: str, prompt: str, api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=model_id,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text


def _call_gemini(model_id: str, prompt: str, api_key: str) -> str:
    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(model=model_id, contents=prompt)
    return resp.text


def call_model(display_name: str, prompt: str, user_key: str | None = None) -> str:
    """Call a reference model from the registry."""
    entry = MODEL_REGISTRY.get(display_name)
    if entry is None:
        raise ValueError(f"Unknown model: {display_name}")

    api_key = _resolve_key(entry["env_var"], user_key)
    provider = entry["provider"]
    model_id = entry["model_id"]
    base_url = entry["base_url"]

    if provider == "openai":
        return _call_openai(model_id, prompt, api_key, base_url)
    elif provider == "openai_compat":
        return _call_openai(model_id, prompt, api_key, base_url)
    elif provider == "anthropic":
        return _call_anthropic(model_id, prompt, api_key)
    elif provider == "gemini":
        return _call_gemini(model_id, prompt, api_key)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def call_custom_endpoint(
    base_url: str, model_name: str, prompt: str, api_key: str
) -> str:
    """Call a user-supplied OpenAI-compatible endpoint (left column)."""
    if not base_url or not base_url.strip():
        raise ValueError("API endpoint URL is required for your custom model.")
    client = OpenAI(api_key=api_key or "no-key", base_url=base_url.strip())
    resp = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content
