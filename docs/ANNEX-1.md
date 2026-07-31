## Choosing and configuring your LLM model

This application relies on the combined use of two Python libraries to allow easy "swap" of LLM models so you can test the capability of various ones of just "plug" the one you are used to: LiteLLM & Google Agent Ddevelopment Kit.

LiteLLM provides a unified interface to call 100+ LLMs using OpenAI-compatible formats. When configuring the `LLM_MODEL_NAME` environment variable in Hbntory, LiteLLM relies on a standardized **`provider/model_name`** convention to route requests to the correct API endpoint.

Google ADK further streamlines use by handling some integration process which would have otherwise required custom code with potential variations depending on the chosen model.

### Defining the model to use

#### 1. Syntax Pattern ("Machine Name")

The standard format for model string resolution is either:

```
# Syntax for complex providers
[provider_prefix]/[vendor_or_organization]/[model_identifier]
# Syntax for simple providers such as Ollama local models
[provider_prefix]/[model_identifier]
```
Depending on the model, filling in an API Key (in the aforementioned LLM_MODEL_API_KEY) may be either useless (ex ollama) or mandatory (ex Google Gemini).

#### 2. Non-exhaustive list of supported models (defined on 2026-07-30).

| Provider / Ecosystem | Syntax Example | Environment Variable / Config Requirement |
| :--- | :--- | :--- |
| **OpenAI** | `openai/gpt-4o`<br>or `gpt-4o` | `OPENAI_API_KEY` |
| **Google Gemini (API Key)** | `gemini/gemini-1.5-flash`<br>`gemini/gemini-1.5-pro` | `GEMINI_API_KEY` |
| **Google Vertex AI** | `vertex_ai/gemini-1.5-pro` | GCP Service Account credentials |
| **Anthropic** | `anthropic/claude-3-5-sonnet-20240620` | `ANTHROPIC_API_KEY` |
| **NVIDIA NIM** | `nvidia_nim/meta/llama-3.1-70b-instruct`<br>`nvidia_nim/minimaxai/minimax-m3` | `LLM_MODEL_API_KEY` |
| **OpenRouter** | `openrouter/anthropic/claude-3.5-sonnet` | `OPENROUTER_API_KEY` |
| **Groq** | `groq/llama-3.1-70b-versatile` | `GROQ_API_KEY` |
| **Mistral AI** | `mistral/mistral-large-latest` | `MISTRAL_API_KEY` |
| **Ollama (Local)** | `ollama/llama3` or `ollama_chat/llama3` | Local Ollama daemon running |

### How to Find Supported Models

You have three ways, depending on your preferences.

#### Option A: Official Documentation Matrix

- LiteLLM Providers & Syntax: https://docs.litellm.ai/docs/providers
- LiteLLM Complete Model Cost & Token Matrix (JSON): https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json

#### Option B: Programmatically via Python

You can inspect supported models and provider mappings directly using the litellm package by creating this small script and running it (python3 llm-models_listing.py) (for that you need Python3 and the related libraries installed on your host system, confer installation guide).

```
#Copy those lines in a file named llm-models_listing.py)
import litellm

# Get the list of model mapping dictionaries by provider
print(litellm.models_by_provider.keys())

# Check all built-in recognized model strings
print(litellm.model_list)
```

#### Option C: Providers catalogs

- NVIDIA NIM: Browse models on build.nvidia.com. Prefix the model ID with nvidia_nim/ (e.g., nvidia_nim/meta/llama-3.1-405b-instruct).
- OpenRouter: Browse models on openrouter.ai/models. Prefix the model string with openrouter/.
