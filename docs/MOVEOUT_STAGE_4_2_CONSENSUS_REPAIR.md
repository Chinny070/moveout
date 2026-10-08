# MoveOut Stage 4.2 — Visual Consensus Repair

**Status:** Local repair implemented; local gates pass. Hosted gate **failed** on the fourth single-image case (occlusion false negative). Testing stopped immediately; Stage 5 has not started.

## Baseline and scope

- Baseline commit: `6684ec8e74384789e73b57b160ef7f5f73c465ad`.
- Stage 4.1 diagnosis: whole-result equivalence rejected independently generated model observations at nondeterministic block 0; pair normalization accepted semantically contradictory enum sets; accepted clean/simple output included unsupported confounder flags.
- Changed files: `contracts/moveout_protocol_v1.py` and `tests/test_moveout_stage4_observations.py`.
- No canonical contract, frontend, finding promotion, or tenant-liability behavior was added.

## Changes

### Single-image definitions and validation

The visual prompt now defines positive occlusion as an object hiding relevant surface, positive shadow as a shadow/reflection materially obscuring or resembling a defect, and positive crop limitation as framing that cuts off or makes the relevant surface too small to assess. Ordinary camera angle, framing variation, lighting gradients, and unrelated furniture are explicitly not positive flags. Defect flags must describe visible marks, not infer from perspective, edges, lighting, or uncertain cues.

Malformed key sets, unknown enum values, impossible area/feature combinations, text/injection contradictions, and oversized output continue to fail closed. Invalid single-image output is normalized to explicit uncertainty and marked schema-invalid; raw model text is not stored.

### Pair semantic consistency

Pair outputs now fail closed when:

- same-area support is `NOT_SUPPORTED` or `UNCERTAIN` while a positive difference or `LOW` uncertainty is claimed;
- a material viewpoint, lighting, occlusion, crop, or scale confounder is `YES` while difference is positive or uncertainty is `LOW`;
- definite A/B feature states disagree while `visible_difference` is not `YES`;
- definite A/B feature states match while `visible_difference=YES` and no material confounder explains the appearance; or
- `visible_difference=YES` relies on an uncertain feature state.

An invalid pair normalizes to the empty all-uncertain/high-uncertainty pair schema and has `schema_valid=false`, so it can be recorded only as `INCONCLUSIVE`. No new condition label is derived.

### Validator equivalence

Validators still independently GET every image, validate status/MIME/format/size, compute exact SHA-256, and independently call the vision model. Equivalence is now explicit and field-based:

- exact agreement is required for evidence IDs, digests, verification IDs, and pair continuity;
- single-image critical fields (area visibility and four feature/damage fields) must match exactly;
- pair critical fields (same-area support, both feature states, visible difference, and uncertainty) must match exactly;
- secondary flags may differ only if each complete candidate independently passes schema and semantic-consistency validation;
- invalid/inconclusive outcomes may match only by full bounded result equality;
- digest mismatch, malformed/contradictory output, or any critical disagreement rejects that validator.

This tolerates some non-decision visual-detail variance without treating opposite feature/difference conclusions as equivalent. It does not automatically accept disagreement.

## Hosted effect

The disposable StudioNet contract finalized the first four single-image cases. The clear crack, clean surface, and shadow cases passed the safety-critical checks. The occlusion/crop fixture (`MOV-SYN-08`) visibly contains a chair blocking the relevant wall, but the finalized observation returned `occlusion=NO` (and crop limitation `NO`). This is a genuine semantic false negative, so the six-case gate failed and the sequence stopped. Prompt-injection and stain cases and all pairwise cases were not run. Full transaction, vote, result, and source details are in [Stage 4.2 verification](MOVEOUT_STAGE_4_2_VERIFICATION.md).

An initial local runner assertion treated `surface_damage=YES` alongside a visible crack as a contradiction. The contract schema does not make those two broad/defect fields mutually exclusive, and the image supports both. The runner assertion was corrected without changing the contract, fixtures, or expected labels; the authoritative crack result then passed. This correction is recorded to distinguish a test-harness issue from the later genuine occlusion failure.

### Diagnostics and provenance

The current supported validator callback returns a boolean; StudioNet receipts do not retain each validator's candidate fields or fetch digest, and StudioNet trace has previously returned method-not-found. No unsupported trace, validator logging, or per-validator on-chain record was invented. Local tests directly verify the bounded comparison helper and rejection reason through the boolean result; production receipts still cannot identify a dissenting field.

Known HTTP redirects (non-200 response status, such as 3xx) remain rejected by Stage 3 response validation. The contract continues to accept only the commit-path `raw.githubusercontent.com/Chinny070/moveout/{40-lowercase-hex-commit}/...` source policy, with frozen evidence, prior successful verification, exact digest binding, PNG/JPEG signatures, MIME checks, and bounded response size. The web response has no final URL/redirect-chain field; an automatic redirect that is followed and hidden by the runtime cannot be detected. Thus no redirect-dependent production source is verified safe by this change, and requested-host allowlisting plus digest does not prove route provenance.

## Regression coverage

The Stage 4 observation test module now has 53 passing tests, including the preexisting observation/provenance coverage and Stage 4.2 checks for:

- clean-image negative confounder flags;
- pair contradictions and unsupported/uncertain same-area identity;
- low uncertainty with each material confounder;
- ambiguous mark remaining explicit uncertainty;
- critical versus secondary validator disagreement;
- changed digest rejection;
- known unsafe redirect response handling and hidden-final-URL limitation;
- prompt-injection observations remaining observation-only;
- no Established Condition creation or manifest membership change.

Production contract logic contains no benchmark fixture identifiers or expected labels.

## Local verification

The full `powershell -ExecutionPolicy Bypass -File scripts/verify_moveout.ps1` gate passed:

- 208 original tests preserved; 17 added regression cases; **225 total passed**.
- GenVM lint passed (3 checks).
- SDK validation passed (70 methods: 42 view, 28 write).
- Python syntax compilation passed.
- Stage 4 nondeterministic scope scan passed; no finding writer detected.
- Benchmark-specific production logic scan passed.
- Whitespace checks passed (Git emitted only expected LF-to-CRLF notices).

Local tests do not establish general visual accuracy, final-host provenance, or real-world housing condition accuracy. Hosted consensus on the first three passing cases does not overcome the occlusion false negative. Pairwise tests were not run because the single-image gate failed.
