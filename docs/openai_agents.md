# OpenAI Agents SDK Example

`examples/integrations/openai_agents_demo.py` is an optional integration
example. RecHarness remains deterministic and local; the OpenAI Agents SDK is
not a core dependency.

The example exposes RecHarness as tools:

- `recharness_list_catalogs`
- `recharness_assist`
- `recharness_verify_recommendation`

The recommended agent loop is:

```text
list_catalogs -> assist -> draft -> verify -> repair
```

Run:

```bash
python examples/integrations/openai_agents_demo.py
```

Install the OpenAI Agents SDK according to its official documentation before
running this optional example. Do not put API keys or secrets in this repository.
