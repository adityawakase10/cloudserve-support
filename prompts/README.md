# Prompt register

| ID | File | Category | Serves | Version | Model | Output format | Injection defence |
|---|---|---|---|---|---|---|---|
| PR-01 | `build/answer_v1.md` | Build | FR-05, FR-06, FR-09 | v1.0 | openai/gpt-oss-20b (Groq) | JSON `{can_answer, answer, citations}` | Instructions in the system message; ticket text inside `<ticket>` tags with `<` and `>` neutralised; rule 6 tells the model ticket text is data; input guardrail blocks instruction-like tickets before the model sees them |

## Change history

| ID | Version | Date | Change | Why |
|---|---|---|---|---|
| PR-01 | v1.0 | 2026-11-13 | First version | — |
