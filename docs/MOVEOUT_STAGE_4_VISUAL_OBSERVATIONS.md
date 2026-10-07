# MoveOut Stage 4 — Visual Observation Engine

**Stage result: implemented and exercised, but the Stage 4 hosted gate failed.** The bounded observation API produced three authoritative records on a disposable StudioNet contract. The required six-case single-image gate did not pass: only one single-image transaction reached majority agreement. Pairwise calls were then exercised and produced two records, but this occurred despite the single-image gate not passing; those pairwise results are diagnostic only and do not authorize progression. Stage 5 is not ready.

## Authority boundary

This layer records what validators support as visible in verified image evidence. It does not establish physical truth, image authenticity, capture time, cause, responsibility, liability, normal wear, repair cost, or deposit deductions. A visual observation is not an Established Condition.

The single-image schema is bounded to `area_visibility` (`VISIBLE`, `PARTIAL`, `NOT_ESTABLISHED`, `UNCERTAIN`) and eleven `YES|NO|UNCERTAIN` flags: crack, stain, other mark, surface damage, occlusion, shadow, low light, blur, crop limitation, text, and possible injection text. The pairwise schema contains `same_area_support` (`SUPPORTED|NOT_SUPPORTED|UNCERTAIN`), feature presence in A and B, visible difference, viewpoint/lighting/shadow/occlusion/crop/scale confounders, and `comparison_uncertainty` (`LOW|MEDIUM|HIGH`). Both schemas reject extra keys, unknown values, invalid combinations, or serialized output above 2,048 bytes; invalid model output normalizes to uncertainty and is marked schema-invalid.

The prompt explicitly treats text inside images as untrusted evidence and forbids following instructions in it. The pair prompt describes Stage 2 continuity only as intended correspondence; area identity must still be judged visually. It forbids condition labels including `NEW_DAMAGE`, `WORSENED`, `REPAIRED`, `PRE_EXISTING`, and `UNCHANGED`.

## Verified-evidence and source policy

Observation requires PHOTO evidence and a frozen inspection/evidence pair, plus a latest Stage 3 record whose outcome is `VERIFIED`, whose retrieved digest equals the frozen expected digest, and whose source hash matches the evidence URL. V1 accepts only HTTPS `raw.githubusercontent.com/Chinny070/moveout/{40-lowercase-hex-commit}/...` paths without query strings, fragments, or dot path components. Image retrieval repeats response status, media type, PNG/JPEG structure, size, and SHA-256 checks immediately before interpretation. A changed body is not sent to vision.

This is a controlled-fixture allowlist, not a production storage-provider policy. Adding a provider requires explicit host/path policy, immutable addressing, content validation, redirect semantics, digest binding, and hosted tests. The current response API provides status, headers, and body but no final URL or redirect history. `web.get` may follow redirects before exposing the response. Therefore the implementation cannot prove or reject a redirect to a different final host. Commit pinning and digest matching bind the bytes, but do not prove the retrieval route. This is a Stage 4 production-hardening blocker.

## Validator and equivalence model

The leader retrieves each image independently, checks it against the frozen digest, invokes `gl.nondet.exec_prompt(..., images=[body], response_format="json")` (or both bodies for a pair), and proposes a compact normalized result. The custom `gl.vm.run_nondet_unsafe` validator callback independently retrieves the same evidence, rechecks the digest and format, runs its own vision interpretation, and compares the complete bounded normalized result dictionary. Consensus therefore covers the identifiers, verification references, digests, stage/failure outcome, schema-valid bit, and every enum observation field; there is no free-form prose whose similarity can mask a critical-field difference. Validators may disagree; a finalized `MAJORITY_DISAGREE` creates no accepted Observation Record. This happened repeatedly in hosted tests.

## Hosted result summary

The exact deployment and transaction evidence is in [the Stage 4 verification record](MOVEOUT_STAGE_4_VERIFICATION.md). Three calls reached `FINALIZED / MAJORITY_AGREE` and were confirmed by separate authoritative reads:

| Record | Type | Result | Important bounded output |
|---|---|---|---|
| `OBS-1` | Single, `EVID-1` / `EVER-1` | `FINALIZED`, `MAJORITY_AGREE` (3 AGREE, 2 DISAGREE; 3 rounds) | Area `VISIBLE`; crack/stain/mark/surface damage `NO`; occlusion, shadow, and crop limitation `YES`; other flags `NO`. |
| `OBS-2` | Pair, `EVID-2` + `EVID-10` / `EVER-3` + `EVER-4` | `FINALIZED`, `MAJORITY_AGREE` (3 AGREE, 1 DISAGREE, 1 IDLE; 1 round) | Same-area `SUPPORTED`; feature A `NO`, B `YES`; visible difference `YES`; confounders `NO`; uncertainty `LOW`. |
| `OBS-3` | Lookalike pair, `EVID-7` + `EVID-15` / `EVER-13` + `EVER-14` | `FINALIZED`, `MAJORITY_AGREE` (3 AGREE, 2 IDLE; 2 rounds) | Same-area, both feature states, difference, every confounder `UNCERTAIN`; uncertainty `HIGH`. |

Five of six single-image cases finalized `MAJORITY_DISAGREE`; only the simple-image case created a record. Six of eight pairwise cases finalized `MAJORITY_DISAGREE`; the visible-difference and lookalike cases created records. All those unsuccessful transactions had successful leader execution but did not achieve consensus. No record was created for a disagreement.

The synthetic single-image “clean/simple” record reported occlusion, shadow, and crop limitation despite its case label. This is a material fixture-level interpretation concern and another reason the engine is not ready for promotion. The positive pairwise difference record establishes only that the bounded visual comparison was accepted by consensus for this fixture; it does not prove real property accuracy.

## Safety and readiness

Separate authoritative rereads of `INSP-1` and `INSP-2` showed both inspections `FROZEN`, with `condition_record_ids: []`. The three records were append-only `SINGLE_IMAGE`/`PAIRWISE` Observation Records carrying evidence IDs, Stage 3 verification IDs, digests, scope, schema status, and adjudication provenance. No Established Condition was created.

The Stage 0.9 ambiguous-mark concern remains segregated: Stage 4 has no visual-observation path that writes an Established Condition or emits a condition finding. The hosted ambiguous-mark visual transaction itself disagreed and produced no record. Shadow, occlusion/crop, and prompt-injection calls also disagreed and produced no records; that is not proof that their semantic behavior is safe, only that this run failed closed at consensus. The lookalike result is explicitly uncertain. Prompt-injection resistance is not demonstrated by a disagreement.

**Stage 4 usefulness: partial. Stage 4 safety: no condition promotion observed. Stage 4 gate: FAIL. Ready for Stage 5: NO.** Do not use these synthetic observations as real tenancy evidence or promote them into findings. First fix the redirect/provenance gap and improve validator reproducibility, then rerun the complete single-image gate. Pairwise tests must follow only after that gate passes.
