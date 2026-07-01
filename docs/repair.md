# Answer Repair

RecHarness includes a deterministic repair utility for the agent loop:

```python
from recharness import repair_answer_from_verification
```

Use it after `verify` and before returning a final answer.

## API

```python
result = repair_answer_from_verification(
    answer=draft_answer,
    verify_response=verify_response,
    assist_response=assist_response,
)
```

`result` is a `RepairResult`:

```text
status: unchanged | repaired | qualified | failed
repaired_answer: str
changes: list[str]
warnings: list[str]
```

For examples that only need text, use:

```python
from recharness.core.answer_repair import repair_or_qualify_answer

final_answer = repair_or_qualify_answer(
    draft_answer,
    verify_response,
    assist_response=assist_response,
)
```

## Behavior

The repair utility is deterministic and conservative:

- `unchanged`: verification passed, so the answer is returned as-is.
- `repaired`: RecHarness made a catalog-grounded correction.
- `qualified`: verification did not pass, but no safe deterministic repair was available.
- `failed`: no verification report was available.

Current repair behavior covers:

- hard-constraint-invalid recommendations with a safe assist candidate
- noise cancellation overclaims
- battery life mistakes
- price mistakes
- weight and laptop-fit numeric mistakes
- availability caveats
- unresolved or hallucinated product mentions by qualification

## Grounding Rules

Repair output must stay grounded in local catalog data:

- Do not invent attributes.
- Do not promote rejected candidates as safe recommendations.
- Do not turn soft preferences into guarantees.
- Prefer cautious wording such as `local catalog indicates` or `本地目录标注`.

If no deterministic fix is available, the utility qualifies the answer instead
of fabricating a better one.

## CLI

Use `verify --repair` to include repair output alongside verification results:

```bash
recharness verify \
  --catalog examples/headphones/catalog.jsonl \
  --query "想找1000元以内，适合通勤，有降噪的蓝牙耳机" \
  --answer "我推荐 SonicLite AirBuds，售价699元，有主动降噪，续航30小时。" \
  --repair
```

For machine-readable output:

```bash
recharness verify \
  --catalog examples/headphones/catalog.jsonl \
  --query "想找1000元以内，适合通勤，有降噪的蓝牙耳机" \
  --answer "我推荐 SonicLite AirBuds，售价699元，有主动降噪，续航30小时。" \
  --repair \
  --json
```
