# MoveOut Stage 5.4 — Adversarial Testing and Runtime Readiness

**Stage status: PARTIAL.** Local deterministic verification passes, but the review found a supplemental-request closure bypass that needs a separately authorized remediation. Visual-model evaluation and target-feature hosted verification were not performed. No production contract or prompt was changed; no deployment, hosted transaction, migration, or release occurred.

## Executive summary

The Stage 5.1–5.3 implementation has substantial deterministic safeguards for target nomination, observation schema validation, authorization, frozen evidence, digest/provenance binding, supplemental linkage, and cross-photo conflicts. The complete local suite passes with the additional Stage 5.4 adversarial and property-based tests.

One **MEDIUM** lifecycle defect is confirmed: after a requester closes a supplemental request, assessing already-frozen supplemental evidence appends a later event. The request’s `lifecycle_status` is computed from its last event, and the inspection-creation and evidence-submission paths reject a request only when that last event is `CLOSED`. The assessment therefore makes the request appear open again and permits a new supplemental inspection and photo. Original frozen records remain unchanged, and participant authorization still applies, but the explicit closure is not terminal.

The controlled image set is synthetic and generated for the benchmark. It is not a real-photo evaluation set, and this turn did not run a real vision model against any image. Real-world visual accuracy is **BLOCKED**. Local Direct Mode tests and GenVM lint do not demonstrate StudioNet committee behavior, finality, or state rollback.

## Scope and baseline

- Requested baseline `ee929993fef82e431839919ea803a2565f5930c2` was local `main` and the worktree was clean before this review. The initial sandboxed `git ls-remote` failed to connect to GitHub; the elevated read-only check succeeded and confirmed `origin/main` at the same baseline SHA before staging.
- Read the Stage 4.3–4.7 and Stage 5.1–5.3 reports. Stage 4.7 remains authoritative for majority-aware consensus: a successful result is not unanimity, and a majority-accepted model output is not real-world truth.
- Contract dependency header pins `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`.
- `genvm-lint` version is 0.11.0. The verification script runs `gltest` Direct Mode on its default localnet configuration with mocked web/LLM behavior in the relevant tests.
- Only `tests/test_moveout_stage53_supplemental.py` and this report are changed. Production contract, production prompts, fixtures, and benchmark labels are unchanged.

## Architecture and security review

### Target nomination and target-aware observations

`create_target_nomination` (`contracts/moveout_protocol_v1.py:1768`) creates contract-issued target IDs, requires an inspection/area participant scope, validates optional reference evidence and normalized box input, versions superseding nominations, and binds the nomination digest to immutable metadata. Inspection freeze snapshots nomination IDs. Target observations use `_prepare_target_visual_assessment` and `observe_nominated_target` (`:3126`, `:3177`) to require the frozen latest nomination, snapshot membership, matching parent hierarchy, verified evidence, and exact target/evidence binding.

`_normalize_target_observation` and `_target_assessment_summary` (`:541`, `:576`) enforce the bounded seven-field schema and reject `feature_presence=ABSENT` unless location, target visibility, obstruction, frame coverage, and clarity satisfy the locked gate. Obstruction and frame coverage are separate fields. These are deterministic consistency checks on a model candidate; they cannot prove the model mapped the correct pixels.

### Supplemental workflow and confirmed finding

`create_supplemental_request` (`:2000`) binds a request to a frozen original inspection, latest frozen target nomination/digest, original photo/digest/provenance, and an insufficient observation. `create_supplemental_inspection` (`:2094`) creates a separate inspection pointing backward. `submit_supplemental_evidence` (`:2142`) binds each new photo to the request and delegates to the normal evidence constructor/freeze lifecycle. `_prepare_continuity_pair` (`:2222`) checks request, target, parent, freeze, provenance, and digest bindings. `_evaluate_continuity_pair` (`:2329`) retrieves both images independently in each callback and sends the ordered pair to one bounded vision request. `_continuity_equivalent` (`:2449`) compares safety-critical bindings, continuity, and observation fields; `assess_supplemental_continuity` (`:2481`) writes the assessment only after the nondeterministic operation returns and the candidate binding/schema checks pass.

**MEDIUM — Supplemental request closure is not terminal.**

- **Affected code:** `close_supplemental_request` (`:2189`), `_supplemental_request_view` (`:1981`), `assess_supplemental_continuity` (`:2481`), and the “latest event is CLOSED” checks in `create_supplemental_inspection` (`:2094`) and `_submit_evidence_internal` (`:2806`).
- **Reproduction:** `test_stage54_adversarial_assessment_event_reopens_closed_request` closes a request; successfully assesses already-frozen linked evidence; observes `lifecycle_status=ASSESSMENT_APPENDED`; then creates a new linked inspection and submits a new photo. The sequence passes in Direct Mode.
- **Impact:** A requester’s closure can be bypassed by a later assessment event. Request status also ceases to present as closed. Existing participant authorization, immutable original evidence, and per-photo digests still apply; this does not directly create a finding or liability decision.
- **Evidence:** Proven for current local contract/Direct Mode. Hosted behavior is untested.
- **Recommended remediation:** In a separately authorized remediation, model closure as a monotonic terminal status (or add an immutable terminal-closed marker) and guard assessment, inspection creation, and evidence submission consistently. Preserve later audit events without allowing them to supersede the terminal status. Add regression sequences for close→assessment, close→inspection, and close→late submission, including idempotent retries. This report does not change production code.

### Evidence provenance, custody, and compatibility

- A submitted `expected_sha256` is caller-asserted until provenance verification retrieves the body, validates status/MIME/size/basic image structure, and matches SHA-256 (`_classify_verification_response`, `:329`; `verify_evidence_provenance`, `:2988`). Supplemental requests bind the original verification ID and expected/retrieved digest. Each supplement has a separate evidence ID and verification record.
- The target-visual path additionally restricts its source reference through `_validate_visual_source` (`:404`) to a commit-pinned asset under the project’s allowlisted raw GitHub host. The provenance digest establishes byte equality with the caller’s expected digest, not image capture authenticity, capture time/location, photographer identity, physical target identity, or truthfulness of participant metadata.
- No cryptographic camera/capture attestation or verified location/time mechanism was found. The source URL is an input/provenance reference, not proof of who created the photograph. The retrieval code checks the returned status, headers, and bytes; it does not establish at application level that any HTTP redirect chain stayed within the original host. This is an **unverified assumption**, not a demonstrated exploit; target visual URLs are source-host allowlisted and exact body digests are checked.
- Original inspections, evidence, and observations remain append-only/frozen. Supplemental evidence is placed in a separate inspection. Legacy JSON reads and V1 observations have explicit regression coverage; no migration or deployed-record upgrade was attempted.
- Observation writers do not automatically write Established Conditions or liability/deposit outcomes. Participant-created condition records remain a separate, explicitly authorized API path.

## Adversarial test matrix

All cases below are deterministic Direct Mode/API/schema checks unless marked **visual** or **hosted**. Mocked LLM candidates are test inputs, not model performance evidence.

| Attack / property | Existing or added coverage | Result boundary |
|---|---|---|
| Unauthorized target nomination/request/evidence/observation | Stage 5.1 `test_unauthorized_actor_cannot_nominate`; Stage 5.3 `test_unauthorized_requester_cannot_create_request`, `test_unauthorized_supplemental_evidence_submission_rejected`, Stage 5.2 `test_unauthorized_observation_submission_is_rejected` | Deterministic authorization checks pass. |
| Cross-inspection, cross-area, target/evidence substitution | Stage 5.1 scope and reference tests; Stage 5.2 wrong-target/evidence tests; Stage 5.3 `test_supplemental_evidence_cannot_be_submitted_to_an_unlinked_inspection`, `test_wrong_target_request_cannot_be_used_for_another_request_evidence` | Deterministic binding checks pass. |
| Incorrect nomination/evidence digest, stale version, mismatched verification | Stage 5.1 digest tests; Stage 5.2 tampering/equivalence tests; Stage 5.3 request-binding and `test_equivalence_rejects_safety_critical_mutation` | Deterministic fail-closed checks pass. |
| Duplicate/replay/changed retry | Stage 5.1 idempotency tests; Stage 5.3 `test_same_request_replay_is_idempotent_and_changed_replay_rejected`, `test_supplemental_evidence_replay_is_idempotent_and_duplicate_digest_is_rejected` | Same payload replay is idempotent; conflicting reuse and duplicate content are rejected. |
| Forged/malformed identifiers, missing schema fields, malformed model output | Stage 5.1 `test_bad_identifier_malformed_fields_and_revision_context_rejected`; Stage 5.2 `test_malformed_ai_output_is_not_normalized_to_a_negative`; Stage 5.3 `test_malformed_or_internally_conflicting_model_result_is_not_persisted` | Deterministic schema rejection passes. |
| Frozen-record modification and generic supplemental bypass | Stage 5.1 `test_frozen_inspection_rejects_new_target_and_has_no_mutation_or_delete_api`; Stage 5.3 `test_original_evidence_and_observation_remain_unchanged_after_supplement`, `test_generic_evidence_api_cannot_bypass_supplemental_request_link`, `test_frozen_original_cannot_accept_supplemental_photo_membership` | Frozen original remains unchanged in the local test model. |
| Inadequate visibility with confident absence | Stage 5.2 `test_inconsistent_or_unsafe_absence_candidate_fails_closed`; added Stage 5.4 deterministic Hypothesis property test samples 24 reproducible candidates and verifies every accepted `ABSENT` satisfies all five target gates | Deterministic candidate-invariant coverage only. |
| Conflicting observations, unsupported continuity, misleading close-up | Stage 5.3 `test_unsupported_or_uncertain_continuity_cannot_clear_visibility_or_absence`, `test_conflicting_repeated_continuity_is_retained_as_conflicted`, `test_contradictory_photos_under_one_request_remain_conflicted` | Structured conflict remains unresolved; actual visual continuity accuracy is unmeasured. |
| Leader fallback / validator mismatch | Stage 5.2 `test_direct_callback_models_only_one_validator_vote_not_majority_or_unanimity`; Stage 5.3 parameterized exact-field mutation tests and callback replay tests | Callback logic is locally exercised. Local tests cannot prove committee quorum, state rollback, or hidden dissent behavior. |
| Legacy compatibility and observation-to-liability escalation | Stage 5.1 `test_legacy_inspection_without_target_fields_still_reads_and_freezes`; Stage 5.2 legacy/read/no-finding tests; Stage 5.3 `test_legacy_inspection_without_supplement_fields_remains_readable`, `test_continuity_observation_is_not_an_established_condition` | No automatic promotion path is evidenced in this scope. |
| Request close followed by assessment and new evidence | Added `test_stage54_adversarial_assessment_event_reopens_closed_request` | **Confirmed MEDIUM finding**; see reproduction above. |

The Stage 5.4 additions are two tests: the lifecycle reproduction and the generated invariant check (24 deterministic Hypothesis examples). `hypothesis` is installed. Mutation testing tools `mutmut` and `cosmic-ray` are unavailable; no mutation run is claimed. No test compares a generated fixture’s expected label to actual model output.

## Safety invariant audit

| Stage 4.7 invariant | Enforcement / tests | Guarantee type and remaining failure mode |
|---|---|---|
| No confident defect absence without adequate target visibility | `_normalize_target_observation`; Stage 5.2 absence tests; Stage 5.4 generated property test | Deterministic gate on returned fields; a vision model can still falsely assert the fields. |
| No absence without sufficient coverage and clarity | `_normalize_target_observation`; Stage 5.2 parameterized target/clarity tests | Deterministic candidate consistency; visual adequacy is semantic/model-dependent. |
| No invented target locations | Contract-issued target IDs and immutable nomination; target schema requires `LOCATED` before feature polarity | Deterministic identity/binding; model localization correctness is unproven. |
| Obstruction and cropping stay separate | Separate enums in V2 schema and exact equivalence; Stage 5.2 obstruction/crop cases | Deterministic schema; model may confuse the image phenomena. |
| No silent resolution of conflicting observations | `_target_candidate_summary`, `_continuity_summary`; Stage 5.2/5.3 conflict tests | Deterministic for detected conflicts; undiscovered visual contradictions remain possible. |
| No unsupported cross-photo continuity | `_prepare_continuity_pair` binding plus tri-state model result; unsupported/uncertain tests | IDs/digests deterministic; physical continuity is model-dependent and not accurate-by-test. |
| No modification of frozen evidence | Freeze/snapshot checks and append-only records; frozen-parent and immutability tests | Deterministic within contract APIs; no hosted storage test in this stage. |
| No unsupported claim of validator unanimity | Stage 4.7 policy; contract stores bounded adjudication provenance, not all peer outputs | Documentation/presentation invariant. Majority can accept with minority dissent; no hosted Stage 5.4 receipt examined. |
| No leader fallback if consensus unresolved | `run_nondet_unsafe` is followed by validation and then writes in `observe_nominated_target` / `assess_supplemental_continuity` | Source-order and local callback behavior only; runtime undetermined rollback and authoritative reread need hosted proof. |
| No automatic liability/deposit deduction | Target/supplement paths write observations only; no target observation writer to Established Conditions; separation tests | Deterministic API separation; client must not display observations as legal outcomes. |

## Deterministic correctness versus visual accuracy

The repository contains 28 synthetic AI-generated PNG fixtures, with 14 designed pairs and manifest labels. The benchmark README states that they depict no real property or person and are not representative of rental inspection photos. The benchmark report further notes that labels were manually assigned by one reviewer and that earlier synthetic runs had false `WORSENED`/`NEW_DAMAGE` decisions. No licensed/consented real-photo dataset with independently reviewed target-region ground truth was available in this workspace.

No vision model was invoked during Stage 5.4. Direct Mode tests supply mocked model answers. Therefore all 12 requested visual scenario groups are **NOT EVALUATED**: fully visible wall; obstruction; crop; poor lighting; blur; lookalike walls; different rooms; same-target overview/close-up; different-target close-up; conflicting supplemental images; unrelated furniture; uncertain target location. Ground-truth visual target identity, actual output, invariant violation rate, abstention rate, visibility accuracy, false-absence rate, and false-continuity rate are unmeasured. Visual evaluation status: **BLOCKED** pending an appropriately rights-cleared/consented or governed synthetic set with independent labels, a real vision execution environment, and a blinded evaluation protocol. Do not infer visual accuracy from the 378 local tests.

## GenLayer compatibility and runtime readiness

### Locally verified

- `contracts/moveout_protocol_v1.py` uses the pinned `py-genlayer` dependency in its source header.
- `genvm-lint` 0.11.0 lint and SDK validation pass; SDK validation recognizes `MoveOutProtocolV1` with 84 methods (49 view, 35 write).
- Python syntax compilation and the AST nondeterminism scope allowlist pass.
- Stage 5.2/5.3 source uses `gl.nondet.web.get` for independently fetched image bytes, `gl.nondet.exec_prompt(..., images=bodies, response_format="json")` for the two images, and `gl.vm.run_nondet_unsafe` with independent callback retrieval/interpretation. Image/body types and output schema are guarded before persistence. GenLayer’s current docs describe image bytes in `images` and a maximum of two images; they also warn structured output still needs schema validation.
- Writes to supplemental continuity storage occur after the nondeterministic function returns and the output binding/schema/equivalence checks pass.

Official references reviewed: [GenLayer Calling LLMs](https://docs.genlayer.com/developers/intelligent-contracts/features/calling-llms), [Web Access](https://docs.genlayer.com/developers/intelligent-contracts/features/web-access), [Equivalence Principle](https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle), [Error Handling](https://docs.genlayer.com/developers/intelligent-contracts/features/error-handling), and [GenVM Configuration](https://docs.genlayer.com/validators/genvm-configuration). The docs describe independent leader/validator retrieval and a majority decision. This agrees with Stage 4.7’s explicit policy: exact per-validator equivalence does not mean unanimity.

### Not verified here

No real GenVM service, StudioNet transaction, validator set, actual vision provider, committee vote, finality/rollback, or post-transaction authoritative reread was exercised. The `gltest` run is Direct Mode/localnet with mocked web and model calls. Runtime resource-limit behavior for maximum body size/calldata, provider routing for two-image JSON calls, and actual model availability remain deployment-environment checks. GenLayer’s docs note that a request fails if the configured model set has no model that supports image inputs. Runtime readiness is **PARTIAL** locally and **NOT VERIFIED** for hosted StudioNet behavior.

### Separate hosted verification plan — not executed

After closure remediation and separate explicit authorization, perform on StudioNet (chain 61999) with a disposable setup only:

1. A successful target-aware assessment with independently frozen, digest-verified photo; verify transaction finality, receipt, and authoritative observation reread.
2. An insufficient-visibility case; verify an explicit insufficient record with no confident `ABSENT`.
3. Deliberately conflicting evaluator outputs; characterize accepted majority vs undetermined outcomes, never label a majority result unanimous.
4. Supplemental request, linked inspection, separately identified evidence submission, freeze, provenance verification, and assessment.
5. Supported and unsupported continuity cases with distinct, commit-pinned visual resources.
6. Attempted mutation/addition against frozen original inspection/evidence; verify rejection and reread original records.
7. Accepted consensus and unresolved outcomes; record receipts/votes/finality and verify unresolved attempts do not create an accepted observation.
8. After rejected/undetermined outcomes, perform authoritative reads for request, inspection, evidence, and observation indexes to confirm state persistence/rollback semantics.

No deployment or hosted transaction is authorized by this Stage 5.4 request.

## Findings and required remediation

| Severity | Finding | Status | Required next work |
|---|---|---|---|
| HIGH | No Stage 5.4 real-photo / blinded visual evaluation, so real-world visibility and continuity accuracy remain unknown. Existing synthetic benchmark reports contain false confident classifications. | Verified evidence gap; not a new code defect | Further evaluation with independently labeled, rights-cleared images and an actual vision model; report per-scenario denominators, false absence/continuity, and abstention. |
| MEDIUM | Supplemental request closure can be superseded by a later assessment event, then permits new inspection and evidence writes. | Proven locally by multistep adversarial test | Separate authorized remediation; make closure terminal and add regression tests. |
| INFORMATIONAL | GenLayer majority acceptance may conceal minority validator disagreement; local mocks cannot prove hosted quorum or rollback behavior. | Stage 4.7 policy and official docs; no Stage 5.4 hosted test | Hosted verification only after explicit authorization; do not claim unanimity. |
| INFORMATIONAL | Digest/source binding establishes retrieved-byte consistency, not capture authenticity, physical identity, time, or location. Redirect destination behavior is not demonstrated at the application layer. | Source review limitation; no exploit demonstrated | Preserve as a provenance limit; evaluate redirect/final-URL policy in an authorized hardening stage. |

No CRITICAL finding was identified in this bounded source/local-test review. The closure defect is not fixed in Stage 5.4 because production contract edits are prohibited.

## Validation results

`powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify_moveout.ps1` completed successfully:

- Complete local suite: **378 passed, 0 failed, 0 skipped**.
- New Stage 5.4 tests: **2 tests passed**; the property test ran **24 deterministic generated candidates**.
- GenVM lint: **PASS**, 3 checks.
- SDK validation: **PASS**, `MoveOutProtocolV1`, 84 methods (49 view, 35 write).
- Python syntax compilation: **PASS**.
- Nondeterministic scope scan: **PASS**; no new contract calls were added.
- Benchmark-specific production logic scan: **PASS**.
- Secret scan: **PASS**.
- `git diff --check` and cached whitespace check: **PASS** (line-ending conversion warning only).
- Mutation testing: `mutmut` and `cosmic-ray` unavailable; no mutation run claimed.
- Hosted runtime: **NOT PERFORMED**.

## Deployment readiness and stage boundary

**Ready for deployment: NO.** Remediate terminal request closure, conduct blinded visual evaluation, then seek a separate authorization for hosted StudioNet verification. Any hosted proof must establish transaction finality and authoritative state, and must preserve Stage 4.7’s majority-not-unanimity wording. Stage 5.4 ends here; no remediation, hosted verification, migration, release, or later stage has started.
