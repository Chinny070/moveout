# MoveOut Stage 5.6 — Real-Photo AI Accuracy Evaluation

**Stage status: BLOCKED.** Real vision-model evaluation could not be executed in the authorized local environment. No photographs were sent to a model, no inference results or accuracy metrics are claimed, and no contract, prompt, deployment, hosted transaction, or migration was changed or performed.

## Baseline and scope

- Verified baseline: `4a3d0d4e65d1a471012fec1e11dcc89c5dd5bc18` on `main`; the starting worktree was clean and `origin` pointed to `https://github.com/Chinny070/moveout`.
- Read the Stage 4.7 safety policy and Stage 5.2, 5.3, 5.4, and 5.5 reports. Stage 4.7's majority-aware rule remains controlling: protocol acceptance does not prove unanimity or real-world truth.
- This was an environment/dataset feasibility check followed by the existing local verification suite. The scope prohibited hosted transactions and did not authorize an external model service or an alternate photo dataset.

## Vision integration and environment

The production target-visibility path (`contracts/moveout_protocol_v1.py::_observe_target_single`) retrieves the frozen evidence using `gl.nondet.web.get`, checks the response and retrieved SHA-256 against the stored evidence digest, and calls `gl.nondet.exec_prompt(prompt, images=[response.body], response_format="json")`. The prompt requests seven bounded fields: surface visibility, target location, target visibility, foreground obstruction, frame coverage, target clarity, and feature presence. Deterministic validation then derives assessability and blocks confident `ABSENT` unless the target is located, adequately visible, unobstructed, fully in frame, and clear.

The continuity path (`_evaluate_continuity_pair`) independently fetches and digest-verifies both frozen image responses, then calls `gl.nondet.exec_prompt(prompt, images=bodies, response_format="json")` with the ordered original and supplemental image bytes. The result includes `SUPPORTED | NOT_SUPPORTED | UNCERTAIN` continuity and a bounded target observation. `observe_nominated_target` and `assess_supplemental_continuity` run these functions through `gl.vm.run_nondet_unsafe`; validator callbacks repeat retrieval and interpretation and compare safety-critical fields. This describes the deployed contract design; it is not evidence that a real model ran during this stage.

Findings from the available local environment:

- The installed GenLayer CLI reports version **0.39.1**. `genvm-lint` and `gltest` are available; a standalone `genvm` execution runner is not.
- `gltest`'s relevant Direct Mode tests provide `mock_web` and `mock_llm` responses. Those are deterministic contract tests, not vision inference.
- No model/GenVM/API credential environment variable was present, and no project `.env`, `.env.local`, or `.env.test` file exists. Credential values were not read or printed.
- No standalone vision client/runtime (`openai`, `anthropic`, `google`, `transformers`, `torch`, `ollama`, or installed `genlayer` Python package) was available. No `ollama` executable/model was found.
- Docker is installed but its local engine is unavailable (no Docker engine pipe); the GenLayer local RPC at `127.0.0.1:4000` is not listening. The CLI's localnet commands cannot provide an execution environment here without that service.
- `gl.nondet.exec_prompt` does not select a pinned model/provider in MoveOut source. Its image-capable model/version and routing are supplied by a configured GenLayer execution environment. With no local runtime/provider configuration, the actual model and version cannot be identified or invoked.

**Exact blocker:** there is no real, image-capable GenLayer/GenVM inference runtime with an approved model configured for local execution, and the installed Direct Mode test runtime requires mocked model outputs. Running the production nondeterministic path would require a functioning localnet/provider or a hosted GenLayer transaction; the latter is expressly unauthorized. A standalone third-party API would be a different, unapproved model/interface and would not exercise MoveOut's GenLayer callback path.

## Dataset provenance and ground truth

The only relevant local image collection found is `benchmarks/controlled-property-2026-10`:

- **28 PNG images / 14 prepared pairs.**
- Its README and manifest identify it as synthetic, AI-generated with the built-in image generation tool, depicting no real property or person.
- The manifest holds controlled expected labels and hashes; previous stages used these fixtures for technical/hosted feasibility. They are not independently adjudicated real-property photographs. The source generation license/terms are not recorded in the manifest, so no separate license conclusion is made.
- The fixture collection is therefore unsuitable for the requested real-photo accuracy score, and its expected labels cannot be treated as real-world ground truth. Historical synthetic benchmark outputs were not re-scored or relabeled in this stage.
- **Real-property photographs: 0. Independently ground-truthed real target observations: 0. Eligible real original/supplemental pairs: 0.** No new photographs or restricted data were copied into the repository.

The 15 requested scenario classes (visibility, partial visibility, obstruction, cropping, lighting, blur, lookalikes, room similarity, genuine and incorrect pairs, unrelated furniture, uncertain location, visible/no visible defect, and contradictory supplemental evidence) were **not model-evaluated**. With no suitable labeled real images and no inference runtime, creating labels or claiming cases pass would fabricate the evidence this evaluation is meant to measure. Training data was not used or prepared.

## Evaluation results

No production prompt was modified or executed. No real inference call was attempted because the approved execution interface was unavailable.

| Measure | Result |
|---|---|
| Visibility accuracy, obstruction, crop, clarity, target-location behavior | **NOT MEASURED** (0 eligible real images; 0 model outputs) |
| Insufficient-evidence and structured-output behavior under actual vision | **NOT MEASURED** (0 model outputs) |
| Physical-target continuity accuracy | **NOT MEASURED** (0 eligible real pairs; 0 model outputs) |
| Unsafe accepted confident defect-absence cases | **NOT MEASURED** (no raw model output or accepted real-model result) |
| False `SUPPORTED` continuity cases | **NOT MEASURED** (no pair inference) |
| Structured-output failures | **NOT MEASURED** (0 outputs; no valid denominator) |
| Confusion matrices, rates, confidence intervals | **NOT CALCULABLE** |

These values are not zero-error findings. There were zero evaluation outputs, so false-absence, false-continuity, abstention, and schema failure rates have no denominator. No raw model response exists to contrast against deterministic validation. Consequently there are no model errors to attribute to an image, prompt, or validator in this stage.

## Safety interpretation and recommendations

The production deterministic gates are designed to reject unsafe combinations in structured outputs, but Direct Mode tests that mock the model cannot measure whether a vision model actually recognizes occlusion, cropping, blur, wrong targets, or contradictory photos. They cannot establish visual accuracy or prove how a configured provider interprets the prompt.

To resume Stage 5.6 without hosted transactions, the evaluation environment must provide both:

1. A supported local GenLayer runtime capable of executing the actual `gl.nondet.web.get` and image-bearing `gl.nondet.exec_prompt` paths with a named/pinned image-capable model and a way to invoke leader and independent validation callbacks without submitting a hosted transaction; and
2. Rights-cleared/consented real property photographs with independent, documented ground truth for target location, visibility, obstruction, crop, clarity, defects, and physical target identity/continuity. The pair labels must be set by reviewers who are not shown model outputs. Conflicts or unverifiable cases must be marked unsuitable/unresolved, not forced into a binary label.

Once available, run blinded visibility and pair evaluations separately, preserve each raw response and validated outcome, report counts and denominators by scenario, and treat false accepted `ABSENT` and false `SUPPORTED` continuity as high-severity errors. Do not change production prompts/contracts as part of this evaluation; any correction requires separate authorization.

## Regression verification

`powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify_moveout.ps1` passed after the report was added:

- Complete local suite: **380 passed, 0 failed, 0 skipped**. Relevant inference-path tests use mocked web/model responses.
- GenVM lint: **PASS** (3 checks).
- SDK validation: **PASS** (`MoveOutProtocolV1`, 84 methods: 49 views and 35 writes).
- Python syntax compilation: **PASS**.
- Stage 4–5.3 nondeterministic-scope scan: **PASS**.
- Benchmark-specific production logic scan: **PASS**.
- Secret scan: **PASS**.
- `git diff --check` and cached whitespace check: **PASS**.

These checks verify deterministic implementation shape and regressions only. They are not actual vision inference or hosted validator-consensus evidence.

## Readiness and stage boundary

- Local real-photo visual evaluation: **BLOCKED**.
- Ready for hosted GenLayer verification: **NO**; no real-photo accuracy evidence exists, and Stage 5.7 is not authorized here.
- Production changes: **NONE**.
- Deployment/hosted transactions/migrations: **NONE**.
- Ready for Stage 5.7: **NO**. Await the missing local real-model capability, rights-cleared ground-truthed data, and separate owner authorization for any later stage.
