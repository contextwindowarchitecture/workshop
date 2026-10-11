# Capstones

Status: planned. Team exercises of one day each; see the plan, section 3, Capstones.

Each starts from the skeleton of W5 and W7 and ends with a W7-style gate: write cases, record, grade, promote. The three domain blueprints that seed them live in `cwa-extended` and predate the current snapshot shape; they are rewritten here, under each capstone, before use. The pre-assembly scorer they assumed is replaced by a generic, deterministic one so every scenario stays replayable.

| Capstone | Directory | Seeds |
| --- | --- | --- |
| C1 Scribe and diagnostic assistant | [scribe-diagnostic/](scribe-diagnostic/) | transcript as untrusted history, EHR as protected task state, gated prescription capability, SOAP-note contract |
| C2 Customer support and logistics router | [support-logistics-router/](support-logistics-router/) | intent-selected routes, CRM history with variants, dedupe and per-source caps, escalation, PII guard |
| C3 Wealth management and triage | [wealth-triage/](wealth-triage/) | ledger precedence in fact groups, protected user state, strict output contract, trade guard, cache-stable placement |

C2 is built first: it is closest to Fernway.
