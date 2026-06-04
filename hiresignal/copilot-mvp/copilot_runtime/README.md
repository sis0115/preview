# Copilot Runtime

Python runtime loader for normalized HireSignal copilot data.

Current scope:

- Load `copilot-data/manifest.json`
- Resolve company aliases
- Load one company bundle
- Resolve or recommend roles
- Build a compact context packet
- Compose provider-agnostic prompt payloads

This package does not call an LLM. API adapters should be added later after
the context packet format is reviewed.

## Quick Check

```bash
python3 -m copilot_runtime.smoke_test
```
