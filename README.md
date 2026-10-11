# CWA workshops

Hands-on workshops for [Context Window Architecture](https://contextwindowarchitecture.io) (CWA), the draft specification for assembling every model call from typed slots. This repository is a monorepo: one directory per workshop, each self-contained, all built on the fictional product Fernway from the [examples](https://github.com/contextwindowarchitecture/examples) repository and on the reference assembler, [assembler-python](https://github.com/contextwindowarchitecture/assembler-python).

CWA treats a model request as compiled output, not a string you concatenate. Producers propose typed items for named slots. The application freezes them, with a versioned route policy and a budget, into a snapshot. An assembler turns the snapshot into the request and a trace that says what was sent, what was left out and why, and never calls a model. The workshops teach each of those roles, in order, with code you can take back to your own system.

Every lab runs without a model: committed snapshots, traces and recorded runs replay to the same bytes. A model is optional and, when used, is any OpenAI-compatible endpoint. See [docs/setup.md](docs/setup.md).

## Catalog

| Code | Workshop | Format | Status |
| --- | --- | --- | --- |
| [W0](00-foundations/) | Context engineering foundations: the prompt is compiled output | 90 min, browser only | ready |
| [W1](01-cwa-tour/) | The CWA tour: planes, slots, snapshot, trace | half day, model-free | ready |
| [W2](02-producers/) | Building a conformant producer | half day, model-free | ready |
| [W3](03-integration/) | Integrating CWA into an existing application | full day | planned |
| [W4](04-budgets-routes/) | Budgets, variants, routes and refusals | half day | planned |
| [W5](05-tools-mcp/) | Tools, MCP and capability policy: agents under CWA | half day | planned |
| [W6](06-profiles-caching-eval/) | Placement profiles, prompt caching and profile evaluation | half day | planned |
| [W7](07-production/) | Production: snapshot store, telemetry, evals and the promotion gate | half day | planned |
| [W8](08-assembler-kata/) | Inside the assembler: the repair kata | full day | planned |
| [W9](09-adapters/) | Adapters: tool-to-producer, assembler protocol, provider, host seam | half day per module | module A ready, B to D planned |
| [W10](10-conformance-contribution/) | Conformance and contributing to the specification | half day | planned |
| [W11](11-benchmarking/) | Benchmarking CWA: does it help, and what does the number mean | half day | planned |
| [C1 to C3](capstones/) | Capstones: build a conformant application in a domain | one day each, teams | planned |

Each workshop's README states its objectives, goals, outcomes, calls to action and the requirements it covers. The full catalog with the reasoning behind it is [docs/plan/workshops.md](docs/plan/workshops.md).

## Tracks

Everyone starts with W0 and W1. Then:

| Track | Who | Sequence |
| --- | --- | --- |
| Application builder | engineers shipping an LLM feature | W2, W9a, W3, W4, W5, W6, W7, then a capstone |
| Contributor to the assemblers | engineers who want to work on the reference implementations | W8, W9b, W10, W11 |
| Integrator | framework and host owners | W9a, W9c, W9d, W3b, W5 |
| Evaluator and architect | leads deciding adoption, eval engineers | W6, W7, W11, then critique a capstone |
| Spec contributor | anyone joining the project | W2 or W8, then W10 |

Conference cuts: W0 alone as a talk, W0 plus W1 as a half-day tutorial, W1 plus W3a as a one-day "migrate your app" workshop. Every module marks its own cut.

## Running a lab

```sh
python3 shared/siblings.py                 # which sibling repositories are present
python3 shared/tools/clone_siblings.py     # clone the missing ones at their pinned releases
cd 01-cwa-tour && uv sync && uv run scenarios.py --check
```

The siblings live beside this repository by default; set `CWA_SIBLINGS_ROOT` to put them anywhere else. The specification's contract is vendored once in [shared/contract/](shared/contract/) and locked by SHA-256. Details, pins and offline notes are in [docs/setup.md](docs/setup.md).

## Two rules

Participant code in this repository never assembles, and never patches an assembler's output. Assembly belongs to a conformant assembler; the payload goes to the provider as rendered. `shared/tools/lint_no_assemble.py` enforces both.

## Layout

```
00-foundations/ … 11-benchmarking/   one directory per workshop, each a uv project with its own README and scenarios
09-adapters/{a,b,c,d}-*/             W9's four modules
capstones/                           C1 to C3
docs/plan/workshops.md               the catalog and the decisions behind it
docs/setup.md, docs/providers/       toolchain, siblings, pins, the model endpoint
docs/facilitator/                    run sheets, one per workshop
docs/glossary.md                     generated from the website's glossary
shared/contract/                     the vendored specification contract and its lock
shared/siblings.py, shared/tools/    sibling resolution, vendoring, lint, scenario runner, glossary generator
```

## Related repositories

- [contextwindowarchitecture](https://github.com/contextwindowarchitecture/contextwindowarchitecture): the specification, its schemas, contract and conformance cases.
- [examples](https://github.com/contextwindowarchitecture/examples): Fernway, before and after CWA, from a help-center bot to a production-shaped agent. The workshops build on it and link to it; the two repositories stay independent.
- [assembler-demo](https://github.com/contextwindowarchitecture/assembler-demo): the inspector and the four assemblers compared on the same bytes.
- [website](https://github.com/contextwindowarchitecture/website): the pages W0 and W6 use.

## Shoulders of giants

CWA rests on earlier research and work; see [SHOULDERS.md](SHOULDERS.md).

## License

Apache-2.0. See [LICENSE](LICENSE).
