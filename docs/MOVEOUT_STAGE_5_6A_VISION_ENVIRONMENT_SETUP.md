# MoveOut Stage 5.6A — GenLayer Runtime and Vision Evaluation Setup

**Stage status: PARTIAL — runtime restoration and model smoke test are blocked pending owner approval.** Environment and documentation investigation is complete, and real-photo dataset candidates were identified without downloading them. No runtime was started, package/model/data download was made, image was sent to a model, production contract or prompt changed, or network transaction submitted.

## 1. Baseline and environment inventory

- Starting commit independently verified: `21a1b5ebf5c2922da23ae774f16dca116c0c7468` on `main`.
- Starting worktree was clean and `origin` was configured to `https://github.com/Chinny070/moveout`.
- OS/runtime: Windows kernel description `Microsoft Windows 10.0.22000`, x64; PowerShell `7.6.5`; Python `3.12.10`; Node `v24.14.0`.
- Installed GenLayer CLI: `0.39.1`. Installed Python packages: `genlayer-test 0.29.2`, `genlayer-py 0.16.3`, `genvm-linter 0.11.0`.
- Docker CLI: `27.5.1`, meeting the documented Docker 26+ client prerequisite. `Get-Service com.docker.service` reported `Stopped` / `Manual`; `docker info --format '{{.ServerVersion}}'` could not connect because the Docker engine named pipe `//./pipe/docker_engine` does not exist. The Docker client also reported access denied reading the user's Docker config. No Docker server version is available.
- `glsim`, standalone `genvm`, and `ollama` executables are absent. The installed `genlayer-test` advertises a `sim` optional extra, but that extra/`glsim` executable is not installed. The optional simulator has not been installed.
- No project `gltest.config.yaml`, `.env`, `.env.local`, or `.env.test` is present. The current `genlayer network info` reports the persisted alias as **studionet**, chain `61999`, RPC `https://studio.genlayer.com/api`. This configuration was read only; it was not changed, and no request was made to that hosted RPC.
- No relevant model/provider credential environment-variable names were present. Credential values were not read or printed. No provider configuration was changed.

### Commands and observed results

| Command/check | Observed result |
|---|---|
| `python --version` | `Python 3.12.10` |
| `node --version` | `v24.14.0` |
| `genlayer --version` | `0.39.1` |
| `docker --version` | `Docker version 27.5.1, build 9f9e405` |
| `pip show genlayer-test genvm-linter genlayer-py` | `0.29.2`, `0.11.0`, `0.16.3` respectively |
| `Get-Service com.docker.service` | `Stopped`, `Manual` |
| `docker info --format '{{.ServerVersion}}'` | Failed: no Docker engine named pipe; server unavailable. Docker config read also reported access denied. |
| TCP probes to `127.0.0.1:4000`, `:8080`, `:9153`, `:11434` | All `False` (no RPC, Studio UI, node health endpoint, or local Ollama listener). |
| `genlayer network info` | Current alias is hosted `studionet`, chain 61999; not localnet. Read only. |
| `Get-Command glsim,genvm,ollama` | No matching executable found. |
| `genlayer init --help` / `genlayer up --help` | Help only. `init` supports `--headless`, `--localnet-version` (default `v0.65.0`), `--ollama`, and `--reset-db`; `up` supports `--headless`, `--ollama`, validator count, and reset flags. No startup was attempted. |

## 2. Localnet root cause

The direct blocker is **Docker service unavailable**, not an unsupported Docker client version: Docker 27.5.1 is installed, but the Windows service is stopped, the daemon socket is absent, and local Studio/RPC ports are closed. No GenLayer localnet or Studio service is currently running. The current CLI alias also points at hosted StudioNet, so future setup must explicitly select `localnet` before any client or test command that might write.

This turn did not run `genlayer init` or `genlayer up`. The official CLI is documented as automating downloads and launching the local Studio stack. Restoring it would require starting a stopped Docker service (which may require elevated owner action) and downloading container/runtime components. Stage instructions require pausing for owner approval before elevated actions or significant downloads. The observed service status and Docker error establish the blocker without initiating those changes.

No evidence indicates an unsupported installed CLI or Python version. Shell networking to GitHub is restricted in the normal sandbox, but that is not the cause of the stopped local Docker engine. No localnet configuration file exists in the project to diagnose as malformed.

## 3. Official GenLayer setup and API requirements

The current official [Development Setup](https://docs.genlayer.com/developers/intelligent-contracts/tooling-setup) lists Python 3.12+, Node.js 18+, and Docker 26+ for local Studio. The versions present meet those software-version requirements; the Docker daemon is unavailable. The official local Studio sequence is `genlayer init`, then `genlayer up`; the Studio UI is at `http://localhost:8080` and its RPC at `http://localhost:4000/api`. Installed CLI 0.39.1 help agrees with the documented command family. Its own `init` help currently defaults to localnet version `v0.65.0` and exposes an `--ollama` option.

The documented no-Docker alternative is [GLSim](https://docs.genlayer.com/api-references/genlayer-test/glsim), installed with `pip install genlayer-test[sim]`. Its documentation says it supports real LLM/web calls and accepts `--llm-provider` (example `openai:gpt-4o`). However, the [Development Setup](https://docs.genlayer.com/developers/intelligent-contracts/tooling-setup) explicitly says GLSim runs the Python runner natively, **not inside GenVM**. It may be useful for preliminary inference evaluation, but cannot alone prove the exact full GenVM path requested by MoveOut. Installing it changes the global Python environment and may download dependencies, so it was not attempted without owner approval.

Official [Image Processing](https://docs.genlayer.com/developers/intelligent-contracts/features/image-processing) documents raw `bytes` image inputs to `gl.nondet.exec_prompt(..., images=[...])`, PNG/JPEG examples, and a maximum of two images. It states GenLayer validators select models on network; local validators must be configured with an image-capable model. [Calling LLMs](https://docs.genlayer.com/developers/intelligent-contracts/features/calling-llms) documents `response_format="json"` but still requires application schema validation. MoveOut's existing paths match this interface: one verified HTTP body in `images=[body]` for target visibility, and the independently fetched original/supplemental bodies in `images=bodies` for continuity. Their Stage 5.2/5.3 callback code does re-fetch and re-interpret on validators; this setup stage did not execute either path against a real model.

For local Studio, [Inference Providers](https://docs.genlayer.com/developers/intelligent-contracts/tools/genlayer-studio/providers) and [GenVM Configuration](https://docs.genlayer.com/validators/genvm-configuration) describe configuring provider/model entries and validator assignment. Image requests need an enabled model configured to support image inputs; JSON output support must also be enabled where applicable. Provider credentials are not configured in this workspace. Current documented environment variable names include `OPENAIKEY`, `ANTHROPICKEY`, `GEMINIKEY`, and other provider-specific keys; none were found in the process environment and no values are recorded here. Provider names/examples in documentation are not a selected or tested MoveOut model.

The official [GenLayer node health reference](https://docs.genlayer.com/api-references/genlayer-node/ops/health) documents `GET /health` (example `http://localhost:9153/health`) for a GenLayer node and its GenVM module checks. Port 9153 was closed here. The documentation does not establish that this node health port is mapped by every local Studio CLI configuration. Local Studio's documented UI/RPC endpoints should also be checked after startup, followed by an approved integration smoke against localnet. No health response could be obtained because the runtime is down.

## 4. Runtime restoration and reproducible setup

**Runtime status: BLOCKED; startup not attempted.** `genlayer init`/`up` were not run because the Docker service is stopped and the CLI setup downloads local runtime components. The owner must first approve/perform the elevated service startup and approve the component download. No reset flags were used or recommended.

After approval, the documented local Studio setup is:

1. Start Docker Desktop and verify `docker info` succeeds and the server version is at least 26.
2. Review the CLI's selected localnet version and resource/download requirements. Run `genlayer init --headless` only after approval; avoid `--reset-db` and `--reset-validators` unless separately authorized.
3. Run `genlayer up --headless`; verify the Studio UI at `http://localhost:8080`, local RPC via `genlayer network info` after `genlayer network set localnet`, and the documented health endpoint if the local node exposes it.
4. Configure a vision-capable JSON model for the local validators using the Studio provider/validator settings. Confirm model identifier, version, image/JSON capabilities, provider terms, and whether inference is local or external before sending any test photo.
5. Run a disposable, non-production local smoke test only after confirming whether its invocation creates a local contract/write. Preserve a test receipt/result and validate the exact Stage 5.2 or 5.3 response schema. Do not point CLI writes at the current `studionet` alias.

GLSim is an alternative for a preliminary real-model call without Docker, but not an exact GenVM runtime proof. To use it, owner approval is needed for installing the optional `genlayer-test[sim]` dependencies and for any provider/model selection and image transfer. Its native Python execution must be labeled as GLSim, not GenVM or validator-consensus evidence.

## 5. Vision provider, cost, and privacy

**Vision provider status: BLOCKED / NOT CONFIGURED. Real-model smoke test: NOT RUN.** Model/provider identifier and version, image support in an active local validator, JSON support, response behavior, and MoveOut schema acceptance are not verified.

Available choices requiring owner decision:

- **Local inference (for example, a local Ollama backend):** avoids sending photos to a hosted model provider and may avoid per-call provider fees. Ollama is absent; this route requires an approved runtime/model installation and substantial model downloads, plus suitable local compute. The selected model's actual image and JSON support must be checked, not inferred from its name.
- **External model provider:** GenLayer documents OpenAI-compatible, Anthropic, Google, and other provider configurations. A key, provider configuration, and model with image plus JSON capability are required. Calls may incur provider charges, and the photographs/prompt are transmitted to that provider. Exact cost is unknown until a provider/model and request volume are selected; no provider pricing is asserted here. Explicit owner approval is required before paid calls or transferring any property photograph externally.

GenLayer's local Studio can keep validator infrastructure local while still sending model inputs to an external inference API; local Studio does not imply local/private inference. No credentials were exposed and no image was sent.

## 6. Dataset candidates and provenance

No dataset was downloaded, copied, committed, or inspected at the individual-photo level. Public metadata identifies partial candidates, but none establishes all the target-region and same-physical-target labels required by MoveOut. Image/pair counts below are source-reported, not a count of usable images after privacy/quality screening.

| Candidate | Source-reported data / rights | Ground truth and possible use | Limitations for MoveOut / status |
|---|---|---|---|
| Wall Crack Image Dataset for Earthquake and Structural Health Analysis | 526 actual wall-crack images from residential/commercial buildings, indoors/outdoors; Mendeley record states CC BY 4.0. ([record](https://data.mendeley.com/datasets/hxrry6krs7/1)) | Record reports manual measurements and wall/material/crack variability; candidate positive examples for wall defect visibility. Exact label granularity must be inspected before scoring. | No same-target photo pair mapping or broad clean-wall set documented; privacy and external provider rights/terms need review. Not downloaded. |
| Historical_Building_Crack_2019 | 3,886 labeled 256×256 patches derived from about 40 raw images of one historical mosque, captured over 2018–2019; CC BY 4.0. ([record](https://data.mendeley.com/datasets/xfk99kpmj9/1)) | Crack/non-crack patch labels and real-photo lighting/blur/texture challenges; candidate for limited exploratory visual defect/clarity analysis. | Patch count is not unique photo count; heritage masonry is not rental-interior domain; no verified nominated-target continuity labels. Not downloaded. |
| IDEA: Image Database for Earthquake Damage Annotation | Eucentre reports 5,400+ real post-earthquake/ordinary-inspection images, structural-engineer annotations, damage/no-damage, affected elements and boxes/polygons. Zenodo lists two archives totalling about 20.2 GB. ([Eucentre description](https://www.eucentre.it/en/image-database-for-earthquake-damage-annotation/), [Zenodo record](https://zenodo.org/records/15120522)) | Stronger candidate ground truth for some structural wall-damage/no-damage scenarios. | Public page/record inspected did not surface a clear reusable license value; require rights confirmation. Significant download requires approval. No same-target pair IDs; structural survey imagery differs from rental inspections. Not downloaded. |
| Reinforced concrete structure crack detection dataset 10519 | Mendeley reports 10,519 cracked images plus an equal number of intact images (21,038 total implied); record states CC BY 4.0 and research use. ([record](https://data.mendeley.com/datasets/3ghxck2wd5/1)) | Author-labeled cracked/intact surfaces; possible bounded crack/no-crack candidate. | Reinforced concrete/UAV source-domain shift; no target visibility/obstruction labels or same-target pair relations reported. Exact files/permissions still need inspection. Not downloaded. |

**Counts:** local synthetic fixtures: 28 images / 14 pairs (not real photographs); candidate source-reported real images above: 526, 3,886 patches from ~40 raw images, 5,400+, and 21,038 respectively, with possible overlap among sources not investigated; verified MoveOut-usable images downloaded: **0**; independently ground-truthed same-target pairs: **0**. These candidates may support a limited defect-presence/visibility exploration, but do not cover occlusion/crop/target-location labels across the board and do not establish physical continuity. The owner must provide or approve a rights-cleared, privacy-reviewed pair dataset with documented physical-target relationships, or approve a carefully governed capture/annotation protocol. Do not infer same-wall continuity from filenames, user claims, or repeated building identifiers alone.

## 7. Privacy, security, and limits

- No credentials, private property photographs, or restricted dataset files were included in this report or sent to an inference provider.
- Public availability and a dataset's CC license do not by themselves verify privacy suitability, source authenticity, permission for a particular provider's data retention policy, or that an image depicts the nominated target.
- External vision calls transfer image bytes and prompt content to the configured provider. Provider retention/training terms and applicable photo-consent basis must be reviewed before use.
- If public sources are fetched directly during a later GenLayer call, existing digest/provenance validation binds retrieved bytes to the submitted expected digest but does not prove capture identity/time/location.
- One or two successful smoke responses would verify only basic plumbing/schema behavior, not accuracy, reliability, validator unanimity, or physical truth.

## 8. Owner approvals required / remaining blockers

Before attempting to restore runtime or call a model, owner approval is required for:

1. Starting the stopped `com.docker.service` / Docker Desktop (current account reports Docker config access denied; do not elevate or alter permissions without approval).
2. Downloading the GenLayer local Studio images/runtime components, or alternatively installing `genlayer-test[sim]`; no reset flags or unrelated volume deletion are proposed.
3. Choosing a local model with its model download/compute requirements **or** selecting an external provider and approving cost, credentials configuration, and transfer of the non-sensitive test photo(s) to that provider.
4. Downloading candidate image datasets (especially the 20.2 GB IDEA archives) and confirming exact license/privacy suitability; for a true continuity evaluation, providing/approving independently verified physical-target pair labels.

No smoke test can be run until a supported execution path and authorized model are available. Stage 5.6B accuracy evaluation and Stage 5.7 hosted verification have not begun.

## 9. Validation

`powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify_moveout.ps1` passed:

- Full local suite: **380 passed, 0 failed, 0 skipped**.
- GenVM lint: **PASS**, 3 checks.
- SDK validation: **PASS**, `MoveOutProtocolV1`, 84 methods (49 view, 35 write).
- Python syntax compilation: **PASS**.
- Nondeterministic scope/security scan: **PASS**.
- Benchmark production-logic scan: **PASS**.
- Secret scan: **PASS**.
- Diff whitespace checks: **PASS**.

These checks used the existing local Direct Mode tests/mocks. They do not verify localnet, provider configuration, real inference, or StudioNet consensus.

## Readiness decision

- Runtime: **BLOCKED** (Docker service stopped; no GLSim binary/runtime installed).
- Vision provider: **BLOCKED** (none configured or verified).
- Real-model smoke: **NOT RUN**.
- Real-photo dataset: **PARTIAL candidate sources; no complete authorized pair dataset available locally**.
- Ready for Stage 5.6B: **NO**.
- Ready for Stage 5.7: **NO**.
- Deployment/hosted transactions: **NOT AUTHORIZED / NONE PERFORMED**.
