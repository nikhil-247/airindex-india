# Free-First API Policy

## Principle

The AirIndex core must run without any paid API.

The core pipeline is:

```text
collection → validation → normalization → storage → index → API → dashboard
```

No LLM or commercial airfare API belongs in this critical path.

## Optional AI providers

AI is reserved for explanatory analytics such as summarising already-computed metrics. It must never be the source of truth for numerical calculations.

### OpenRouter

Use an OpenAI-compatible provider adapter so free models can be swapped without changing application code. Free model availability and quotas can change, so model IDs are configuration rather than hardcoded business logic.

### Google Gemini

Gemini's API free tier may be used as a second optional provider when available for the project account/region. Treat quotas as temporary infrastructure constraints, not a guarantee.

### Hugging Face

Hugging Face inference can be evaluated for optional NLP tasks. It must remain non-critical because provider availability and free allowances can change.

## Provider contract

Every provider implements:

```text
provider_id
model_id
capabilities
is_enabled()
generate()
health_check()
```

The application chooses providers by configuration and capability.

## Cost controls

- AI disabled by default in local development.
- Cache repeated analytical prompts/results.
- Limit context to computed facts, not raw databases.
- Set request timeouts.
- Set daily request budgets.
- Never retry indefinitely.
- Never put API keys in source control.
- Never allow provider failure to block the statistical pipeline.

## Recommended development order

1. deterministic analytics without AI
2. provider interface
3. local/mock provider
4. optional OpenRouter/Gemini adapter
5. cached analytical explanations

This keeps the SIH demo functional even if every external AI provider is unavailable.
