# Setup

Every lab runs without a model. The committed snapshots, traces, payloads and recorded runs replay deterministically, so a laptop with Python and uv is enough for W1 to W11. A model is optional and, when used, is any OpenAI-compatible endpoint (see [providers/openai-compatible.md](providers/openai-compatible.md)). W0 needs only a browser.

## 1. Toolchain

| Tool | Version | Needed by |
| --- | --- | --- |
| Python | 3.12 or later | every lab; the shared tools need only 3.10 and the standard library |
| [uv](https://docs.astral.sh/uv/) | current | every lab; each workshop directory is its own uv project |
| git | any recent | cloning the siblings |
| Node | 22 or later, with pnpm 12 via `corepack enable` | W1 and W9 module B, for the demo inspector and harness only |
| A browser | current | W0, W6 and the inspector |

Nothing else. No lab needs Go, Rust or containers. Go and Rust only let W1's inspector run the Go and Rust assemblers beside the Python one; a facilitator can project it instead.

## 2. Sibling checkouts

The workshops do not vendor the examples, the assemblers or the website. They expect those repositories checked out beside this one, so each keeps growing on its own:

```
<root>/
  workshop/                    this repository
  contextwindowarchitecture/   the specification
  assembler-python/            the reference assembler
  assembler-typescript/        optional; W1 part 4's inspector, built so dist/ exists
  assembler-go/                optional; W1 part 4's inspector, needs Go
  assembler-rust/              optional; W1 part 4's inspector, needs Rust
  assembler-demo/              inspector, adapters, MCP servers, scenarios
  examples/                    Fernway: the help-center bot and agent the labs build on
  website/                     optional; the live site at contextwindowarchitecture.io works too
  integrations/                W9 module D only
  benchmark/                   W11 only; its committed Domain 1 and 2 runs are read, nothing is run
```

The root is the parent of this repository by default. To put the siblings anywhere else, set one environment variable to an absolute or relative path:

```sh
export CWA_SIBLINGS_ROOT=/path/to/the/directory/that/holds/them
```

One sibling that lives somewhere else is named on its own with `CWA_SIBLING_<NAME>`, the name upper-cased and dashes as underscores: `export CWA_SIBLING_BENCHMARK=../cwa-extended/benchmark`. The override is a path, absolute or relative, and it wins over the root for that sibling alone.

Clone whatever is missing at the pinned release:

```sh
python3 shared/tools/clone_siblings.py                 # everything shared/contract/pins.json lists
python3 shared/tools/clone_siblings.py examples assembler-python   # just these
python3 shared/siblings.py                             # show the root and what is present
```

Pins live in `shared/contract/pins.json`. The rule is: pin to a release, never to a branch, and when a pin moves, re-vendor the contract in the same commit. Right now the specification is pinned to the commit the reference assembler's `draft-release` tag vendors, and the repositories that have no release yet are pinned to `main` until they get one.

## 3. The contract

`shared/contract/cwa/` is a vendored copy of the specification's contract at the pinned commit: the normative text, the schemas, the requirement and reason tables, the slot defaults, the conformance cases and rejections, the registry fixtures, the guides and the examples. `shared/contract/cwa.lock.json` records every file's SHA-256 and the commit they came from.

```sh
python3 shared/tools/vendor_contract.py --verify     # the vendored files match the lock (CI runs this)
python3 shared/tools/vendor_contract.py --check      # the vendored files match the sibling checkout
python3 shared/tools/vendor_contract.py              # re-vendor from the sibling checkout and rewrite the lock
```

Re-vendor only on purpose, from a clean checkout, with a changelog line, because a contract change can change what a lab's committed scenarios expect.

## 3a. Other languages

The labs are Python. [assemblers.md](assemblers.md) lays the four assemblers side by side and says, module by module, what changes when the application is TypeScript, Go or Rust: the record and the outcomes never do.

## 4. The model, when you want one

Copy `.env.example` to `.env` at the repository root and fill in an OpenAI-compatible endpoint. With no `.env`, every lab prints the request it would have sent instead of sending it. See [providers/openai-compatible.md](providers/openai-compatible.md) for Ollama, vLLM, omlx, LM Studio, llama.cpp and hosted gateways.

## 5. Checks a facilitator runs before a session

```sh
python3 shared/tools/check_all.py --quick           # contract, lint, links, glossary, scenarios: a minute or two
python3 shared/tools/check_all.py                   # the same plus every module's suite, with the solution and with the stubs, and the invariants
```

The steps are scripts of their own, for when one is enough:

```sh
python3 shared/siblings.py                          # every needed sibling present
python3 shared/tools/vendor_contract.py --verify    # contract intact
python3 shared/tools/lint_no_assemble.py            # no participant code assembles or patches a payload
python3 shared/tools/check_links.py                 # every relative link in the Markdown resolves
python3 shared/tools/glossary.py --check            # the glossary matches the website sibling
python3 shared/tools/check_site_links.py            # every link into the site names a page and an anchor it has; --live checks the deployed site
python3 shared/tools/check_scenarios.py             # every workshop's committed scenarios still assemble to the same bytes
python3 shared/tools/run_tests.py                   # every module's suite in its own environment; --labs proves the stubs fail
cd 11-benchmarking && uv run invariants.py          # every committed snapshot replays and validates
```

A module with no scenarios yet is listed and skipped, so a scaffold never fails the build. `run_tests.py --labs` selects each module's stub implementation through its `CWA_<MODULE>_IMPL` switch and expects the suite to fail: a gate the stubs pass is checking nothing.

## 6. Offline venues

The labs need the network for `uv sync` the first time, because the assembler comes from GitHub at its `draft-release` tag, and for the website in W0 and W6. For a venue without reliable connectivity: run `uv sync` in every workshop directory beforehand so uv's cache is warm, clone the website sibling and serve it locally with `python3 -m http.server 8000` from its directory, and keep the vendored contract, which already includes the spec text, the guides and the examples.
