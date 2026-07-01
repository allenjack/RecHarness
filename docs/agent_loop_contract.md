# Agent Loop Contract

This contract defines the recommended RecHarness loop for general-purpose agents.
It is deterministic and agent-framework agnostic.

## Loop

```text
list_catalogs
-> choose explicit domain
-> assist
-> draft from RecommendationBundle
-> verify
-> repair_or_qualify
-> final answer
```

## Agent Rules

- List catalogs before choosing a domain.
- Pass `domain` explicitly to assist and verify calls.
- Draft only from `bundle.recommended` products.
- Do not recommend rejected candidates unless the answer clearly qualifies why they were rejected.
- Do not claim attributes that are missing from the local catalog.
- Do not treat soft preferences as hard guarantees.
- Do not ignore out-of-stock hard exclusions.
- Do not treat every assist warning as a final-answer failure. Assist warnings can describe rejected candidates while safe recommended candidates still exist.
- Always run verification before the final answer when using RecHarness in agent mode.
- Use `repair_answer_from_verification()` or `repair_or_qualify_answer()` when verification returns `warning` or `fail`.

## Drafting

Draft answers should use local catalog wording and cautious attribution:

```text
local catalog indicates ...
本地目录标注 ...
```

Avoid unsupported language such as:

```text
guaranteed
best on the market
definitely waterproof
active noise cancellation
```

unless the catalog evidence supports the claim.

## Repair

When verification reports issues, agents should use the shared repair utility
instead of ad-hoc string edits:

```python
from recharness import repair_answer_from_verification

result = repair_answer_from_verification(
    answer=draft_answer,
    verify_response=verify_response,
    assist_response=assist_response,
)

final_answer = result.repaired_answer
```

The repair layer is conservative:

- It leaves safe verified answers unchanged.
- It corrects catalog-grounded factual mistakes where a deterministic correction is available.
- It replaces hard-constraint-invalid recommendations only when assist provides a safe recommended candidate.
- It replaces unresolved or hallucinated product mentions only when assist provides a safe recommended candidate.
- It repairs factual claim issues before replacing the whole answer when the mentioned product is otherwise valid.
- It uses Chinese repair notes for Chinese answers and English repair notes for English answers.
- It only corrects numeric claims when the number appears with relevant price, battery, weight, or laptop-fit context.
- It qualifies the answer when it cannot safely repair.
- It does not invent product facts.

## Failure Handling

If repair returns `qualified` or `failed`, the agent should avoid presenting the
answer as a confident final recommendation. It can ask the user to relax a
constraint, choose from available recommended candidates, or confirm that a
partially matching option is acceptable.
