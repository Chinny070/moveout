# GenLayer Intelligent Oracle Research for MoveOut

**Research date:** 2026-10-04  
**Scope:** Stage 0 architecture gate only. No contract implementation was started.

## Stage 0 gate

# REQUIRES HOSTED PROOF

Current GenLayer documentation and SDK references establish that the API surface supports webpage screenshots, image inputs to LLM prompts, and validator equivalence mechanisms. They do **not** establish that MoveOut's target hosted runtime (StudioNet, chain ID 61999) successfully executes the complete core path: fetch two user-supplied image URLs, deliver both images to vision-capable validators, independently evaluate the visual condition comparison, and reach consensus under the chosen rule. The official Studio documentation specifically says production-critical web reads must be validated against the target network for rendering, timing, and availability behavior. The article's linked Studio examples could not be loaded by the research browser (Studio import URLs returned cache misses). A successful hosted StudioNet proof using the intended contract/API and representative image URLs is therefore still required.

This is not **BLOCKED** or **UNSUPPORTED**: the current official API references positively document the underlying screenshot and image-prompt primitives. It is not **VERIFIED** because those references are not a successful target-runtime execution, and they say nothing specific about MoveOut's two-image comparison, URL provenance, or its end-to-end StudioNet consensus outcome.

## Research method and primary sources

The required article was read in full: [Intelligent Oracles & the World Wild Web](https://genlayer.com/blog/intelligent-oracles-the-world-wild-web) (published 2025-12-30). Its design claims were cross-checked against current official [GenLayer Web Access](https://docs.genlayer.com/developers/intelligent-contracts/features/web-access), [Image Processing](https://docs.genlayer.com/developers/intelligent-contracts/features/image-processing), [Equivalence Principle](https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle), [Non-determinism](https://docs.genlayer.com/developers/intelligent-contracts/features/non-determinism), [Studio limitations](https://docs.genlayer.com/developers/intelligent-contracts/tools/genlayer-studio/limitations), [Studio validators](https://docs.genlayer.com/developers/intelligent-contracts/tools/genlayer-studio/validators), [network configuration](https://docs.genlayer.com/developers/intelligent-contracts/deploying/network-configuration), the [GenLayer Python SDK API/source reference](https://sdk.genlayer.com/main/_modules/genlayer/gl/nondet/web.html), and the current upstream [write-contract skill](https://github.com/genlayerlabs/skills/blob/main/plugins/genlayer-dev/skills/write-contract/SKILL.md).

The workspace was empty at research start, with no existing MoveOut contract, contract inputs, or local GenLayer instructions to inspect. Therefore, “MoveOut” is treated as a visual property move-out/condition comparison based on before/after image evidence. Exact image semantics and target network were not specified in the workspace; the current hosted stable Studio environment, `studionet`, is the target assumed for this gate, per the requested StudioNet check.

## Article findings

### Intelligent Oracle architecture

The article describes an Intelligent Oracle as an Intelligent Contract that retrieves public web data (text, HTML, or images), interprets it using LLMs, and reaches consensus under Optimistic Democracy. The article's conceptual loop is web access (`gl.nondet.web.render()`), LLM interpretation (`gl.nondet.exec_prompt()`), and an equivalence principle. Current references confirm those capabilities in distinct current APIs and explain that web access/LLM operations run in nondeterministic execution.

For MoveOut, this architecture is relevant if the contract must settle a consequential, validator-reviewed claim about visual evidence. The contract should own only the adjudication and state transition; the user-facing upload flow, auth, previews, and image hosting are outside the on-chain visual judgment itself.

### Reader Pattern

The article's Reader Pattern fetches text or HTML from a source and asks an LLM to extract facts. Current docs distinguish `gl.nondet.web.get(url)` for HTTP content (default text from the fetched response) from `gl.nondet.web.render(url, mode="text"|"html")` for browser-rendered pages; `html` returns page markup, and `wait_after_loaded` can wait for dynamic content. Reader pattern is useful for evidence manifests, property metadata, timestamps, image labels, or source pages, but cannot establish visual condition by itself. For MoveOut's core before/after visual comparison, it is not a substitute for image input.

### Vision Pattern and multimodal interpretation

The article's Vision Pattern uses screenshots and a multimodal LLM, observing that visual judgments are subjective and should use semantic alignment. The current official Image Processing page documents the precise flow: `gl.nondet.web.render(url, mode="screenshot")` returns an image object; pass image data as `images=[...]` to `gl.nondet.exec_prompt(..., response_format="json")`. The `images` input accepts raw bytes (PNG/JPEG) or `gl.nondet.Image` objects, and image reasoning requires vision-capable models. Network model selection is handled by validators; local Studio users must configure vision-capable validators.

For MoveOut, a structured comparison should express observed changes and materiality (for example, cleanliness, damage, missing fixtures, or agreed exceptions) and produce constrained fields such as `decision`, `findings`, and `confidence`—not a free-form verdict alone. The contract must define the comparison scope and standards; “same condition” without an inventory/exception baseline is under-specified.

### Exact current web-access modes and evidence mechanism

The current GenVM SDK source types `gl.nondet.web.render` as:

- `mode="text"` → `str`
- `mode="html"` → `str`
- `mode="screenshot"` → `gl.nondet.Image`
- optional `wait_after_loaded` duration (examples: `"1000ms"`, `"1s"`)

The SDK default is `mode="text"`. HTTP access is separately exposed through `gl.nondet.web.get`, `.post`, `.delete`, `.head`, `.patch`, and `.request` (supported request methods include GET, POST, DELETE, HEAD, OPTIONS, PATCH; response carries status/headers/body). The exact screenshot-to-multimodal evidence path is therefore **browser-render the URL with `render(..., mode="screenshot")`, then pass its returned image object (or raw image bytes) in `exec_prompt(images=[...])`**.

Important distinction: this documents a screenshot of a web page, not a direct image-file fetch method. For direct public image URLs, current docs establish general HTTP GET bytes through `gl.nondet.web.get(url).body`; image processing accepts bytes; however, they do not give a canonical direct-image-fetch/decode example, MIME/size constraints, redirect behavior, or a current official `Image` constructor/decoder example for fetched bytes. Nor do they establish that screenshotting a raw image URL yields a suitable image-only rendering in StudioNet. The direct image URL path remains an API/runtime proof item. Do not assume `render(image_url, mode="screenshot")` behaves like fetching image bytes without a hosted proof.

### Validator execution model

Optimistic Democracy selects a leader and validator committee. The leader proposes a result; validators independently execute nondeterministic work and check the proposal according to the contract's equivalence rule. Current docs state that validators make independent web requests, so each may see changing content and independently generated LLM outputs. Consensus does not make an image source authentic or immutable; it establishes agreement under the configured procedure.

### Equivalence strategies

- **Strict Equivalence (`gl.eq_principle.strict_eq`)** requires exact output equality. Suitable for deterministic/canonical output, not raw screenshots or unconstrained LLM prose. A normalized boolean/JSON result might occasionally match exactly, but strict equality does not itself make that visual decision robust.
- **Comparative Equivalence (`gl.eq_principle.prompt_comparative`)** has leader and validators each perform the task, then an LLM evaluates both answers against a developer-defined principle. This is the strongest documented convenience fit for subjective visual classification/comparison, provided each run receives the same well-defined, accessible evidence and the comparison principle specifies the decision fields/material differences.
- **Non-Comparative Equivalence (`gl.eq_principle.prompt_non_comparative`)** has validators judge the leader's output against input/source and criteria without generating a second candidate. Appropriate for open-ended work when validators can independently inspect the same source and check faithfulness. Weaker fit for MoveOut settlement unless its validator prompt is explicit and grounded in both source images; it must not simply accept leader output.
- **Custom Equivalence** uses custom leader/validator functions (current docs recommend `gl.vm.run_nondet_unsafe` for custom logic), enabling explicit error classification, decision-field comparison, confidence buckets, and policy. This is likely the best production shape if generic comparative judging cannot adequately express MoveOut's material-change policy. It must independently retrieve/inspect evidence on the validator side.

**Recommended strategy:** begin with comparative equivalence over normalized structured outcomes for both independently evaluated images (or paired-image comparison), with explicit criteria and an `inconclusive`/failure path. Promote to custom validator logic if needed for image-fetch errors, missing/invalid evidence, or field-by-field decision rules. Never use strict equality on image bytes/screenshots as the condition comparison. Never use non-comparative leader-only validation for a payment/escrow decision.

## What applies to MoveOut / what does not

**Applies:** nondeterministic public evidence retrieval; multimodal image interpretation; independently validating the leader's result; semantic/field-level equivalence for subjective condition judgments; source allowlists and mutable evidence-source policy; explicit handling of unavailable or inconsistent evidence.

**Does not directly apply:** price-oracle tolerance examples, private authenticated APIs, news summaries, uptime checks, and generic page-content extraction are not the MoveOut core comparison. Domain whitelisting is relevant only where the contract controls retrieval domains; it is not a substitute for proving that a specific submitted image is the intended property evidence. The article's webpage screenshot demo does not demonstrate direct user-image URL retrieval or paired-image condition adjudication.

## URL/source validation and provenance risks

The article recommends domain whitelisting and treating URLs as mutable state, with canonicalization and route/domain policy. This is sound for untrusted URLs, but MoveOut's submitted before/after evidence needs a provenance design beyond host allowlisting. A malicious URL could redirect, vary content by requester/time, serve a different image later, or return an HTML challenge/login page. Validate HTTPS, parse and normalize the hostname (do not use substring matching), enforce exact allowed hosts where applicable, constrain redirects/paths, reject unexpected content types and empty/oversized responses, and ensure fetched bytes are actually a supported image. Record content digest and evidence identifiers/timestamps when submission occurs, if compatible with contract/app design. Domain allowlists cannot prove image authorship, capture time, physical location, or that the two photos depict the same unit.

Current official web docs warn that evidence can change, be personalized, fail, or contain adversarial instructions. Treat fetched page/image data as untrusted input and explicitly delimit it in prompts; do not follow instructions embedded in evidence. Use stable, public, durable image hosting with testable validator access, but recognize that URL persistence is not on-chain evidence persistence.

## Mutable sources, availability, and failure modes

Leader and validators independently fetch data, so mutable URLs and live pages may return different images, even during one consensus attempt. If validators compare different image contents then observed disagreement may correctly prevent consensus but can also cause retries/failure. Prefer immutable content-addressed URLs or store the evidence bytes/digest in a durable, verifiable source where the runtime can retrieve the same payload. Define a deterministic business response for unavailable, malformed, or inconsistent evidence (for example, fail closed / mark inconclusive and permit resubmission or appeal), and classify transient network failures separately from invalid evidence. Do not make settlement depend on a temporary URL being alive indefinitely.

The web docs show HTTP error handling and recommend stable fields or derived summaries. The Studio docs say web access depends on its browser/WebDriver service and available network access; production-critical web reads require target-network validation for rendering, timing, and availability. These are direct reasons the hosted proof is mandatory.

## Public image retrieval and limitations

There are two candidate current mechanisms, with different confidence levels:

1. **Documented:** `render(url, mode="screenshot")` for a webpage; pass the returned `Image` into `exec_prompt(images=[...])`.
2. **Surface-composable but not yet proven end-to-end:** HTTP GET via `gl.nondet.web.get(url)` returns a response with `body: bytes`; image processing says `images` accepts raw bytes. The current official docs do not show the exact composition for a fetched direct image, supported MIME/size limits, URL redirect safety, or hosted StudioNet behavior.

Other limitations: image LLM support depends on vision-capable validators; lighting, angles, occlusion, resolution, timestamps, and mismatched framing can undermine comparison; validators may independently fetch mutable sources; agreement is not forensic proof; screenshot rendering may capture surrounding webpage/UI, not just the image; there is no official guarantee in the inspected references of image hashes, camera metadata preservation, or browser/runtime support for arbitrary image hosts. A model can miss subtle damage or infer facts outside pixels. MoveOut should state that the system adjudicates submitted visual evidence, not physical truth.

## StudioNet compatibility

Current official docs identify `studionet` as stable hosted Studio at `studio.genlayer.com` (chain ID 61999). Current image docs say validators on GenLayer select models and local Studio users should ensure their models support images; hosted Studio's exact vision/model behavior should still be exercised. Studio limitations explicitly caution that web behavior depends on its local browser/WebDriver and network environment and require target-network checks for production-critical web reads. The fetched docs demonstrate capability and documented syntax but are not proof that StudioNet's deployed chain accepts and successfully executes the exact MoveOut path.

The article dates to 2025-12-30, whereas the inspected documentation/SDK includes newer runtime and deployment details. Use the current documented API signatures above, not older article snippets blindly. The upstream Skill additionally requires a pinned concrete GenVM runner version for contracts and rejects `test`, `latest`, and unversioned runner aliases on GenLayer networks; choose the runner only after target compatibility is confirmed.

## Linked examples inspected

From the required article:

- Bitcoin Price Oracle Studio import, contract `0xb8D3D40dBdf221d321298fb416927ACa4C3978f3` (article link 15): attempted; Studio returned a cache miss, so source was **not inspectable**.
- Proof of Steak Studio import, contract `0x2a19547A1824959dE29531F6e2128e9B9FD98d0a` (article link 17): attempted; Studio returned a cache miss, so source was **not inspectable**.
- Domain-whitelisting Studio import, contract `0x8eD02BB59027754e361fe4d2bf697146F2BA8F37` (article link 26): attempted; Studio returned a cache miss, so source was **not inspectable**.
- Article's alternate image/snippet asset (link 14): attempted; image fetch returned a cache miss.
- Current official `FetchWebContent` example was inspected for `get`, rendered text, HTML mode, wait behavior, and mutable-source guidance.
- Current official Image Processing example was inspected for screenshot capture, `images=[screenshot]`, direct bytes inputs, and vision-capable model requirement.
- Current SDK source reference was inspected for precise `render` modes and `Image` return type.
- Current upstream `genlayerlabs/skills` `write-contract` skill was inspected for runner pinning, validator independence, and equivalence guidance.

The unavailable historical contracts are not represented as having been read. The present docs' screenshot/vision example clarifies current syntax; the examples do not provide MoveOut's needed hosted proof.

## APIs that still require verification

- Whether `gl.nondet.web.get(image_url).body` can be supplied directly to `exec_prompt(images=[...])` on the target current runner and hosted StudioNet; exact type/decoder behavior.
- Redirect handling, image content-type checks, maximum image bytes/dimensions, supported formats, and errors.
- Whether `gl.nondet.web.render(..., mode="screenshot")` works consistently for MoveOut's real evidence hosts and produces useful full-page/viewport dimensions.
- Whether comparative equivalence can pass two visual inputs and validators independently refetch the same stable content on Studionet; exact dual-image prompt format.
- Vision-capable model availability/routing on hosted StudioNet validators and resulting consensus transaction lifecycle.
- Whether a content-addressed or submitted-image-byte design is compatible with transaction input/state/storage limits and StudioNet's current pinned runner.

## Limitations and blockers

There is no codebase or MoveOut product specification in the workspace to identify exact condition categories, source rules, or image submission model. The article's linked Studio contracts were unavailable via the research browser's cache, so their bodies could not be inspected. Official current docs prove API declarations and examples, not successful target-host execution. No hosted StudioNet contract/proof transaction was run in this Stage 0 research; no contract was implemented.

## Implementation recommendations after the gate

1. Before contract architecture, define MoveOut's comparison policy: room/asset inventory, pre-existing exceptions, materiality thresholds, permitted capture interval, evidence responsibility, and appeal/inconclusive outcomes.
2. Produce a tiny throwaway compatibility proof on the intended stable hosted `studionet`: submit/retrieve two public immutable sample images, invoke a multimodal comparison under comparative/custom equivalence, confirm actual validator execution and final consensus receipt. Keep it separate from the MoveOut contract.
3. Test direct image GET bytes and screenshot mode separately; use only the path that demonstrably works on the target network. Capture transaction traces/errors and pinned runtime/SDK versions as proof.
4. Prefer immutable evidence references or durable content-addressed storage and bind each pair with a digest/ID. Validate hostname and response type/size; handle redirects deliberately.
5. Ask the model for compact structured outputs, for example per-category `unchanged | changed | unclear`, cited visual observations, and an overall disposition. Validators must independently evaluate the same pair. Compare settlement-critical fields with explicit policy; keep explanations non-authoritative.
6. Use comparative equivalence as the initial semantic approach. Use custom validator logic for explicit field matching, errors, retry/inconclusive handling, and policy enforcement. Keep all storage mutation and settlement after the agreed nondeterministic result.
7. Pin the supported GenVM runner version according to current GenLayer Skills and verify with current lint/integration tooling once implementation begins.

## References

- [Required article](https://genlayer.com/blog/intelligent-oracles-the-world-wild-web)
- [Web Access](https://docs.genlayer.com/developers/intelligent-contracts/features/web-access)
- [Image Processing](https://docs.genlayer.com/developers/intelligent-contracts/features/image-processing)
- [Equivalence Principle](https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle)
- [Non-determinism](https://docs.genlayer.com/developers/intelligent-contracts/features/non-determinism)
- [FetchWebContent example](https://docs.genlayer.com/developers/intelligent-contracts/examples/fetch-web-content)
- [Studio limitations](https://docs.genlayer.com/developers/intelligent-contracts/tools/genlayer-studio/limitations)
- [Studio validators](https://docs.genlayer.com/developers/intelligent-contracts/tools/genlayer-studio/validators)
- [Networks & RPCs](https://docs.genlayer.com/developers/intelligent-contracts/deploying/network-configuration)
- [GenLayer SDK current web module](https://sdk.genlayer.com/main/_modules/genlayer/gl/nondet/web.html)
- [Current GenLayer Skills repository](https://github.com/genlayerlabs/skills)
- [write-contract skill](https://github.com/genlayerlabs/skills/blob/main/plugins/genlayer-dev/skills/write-contract/SKILL.md)
