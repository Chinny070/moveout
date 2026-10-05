# MoveOut Property Visual Benchmark — Stage 0.6

**Current Stage 0.6B status: CONTROLLED FIXTURES AND DISPOSABLE CONTRACT READY; HOSTED EXECUTION BLOCKED ON PUBLIC IMAGE HOSTING.** The previous source audit remains historical. The revised synthetic dataset contains 14 manually labeled pairs and frozen local hashes; no GenLayer inference has been run against them. This is not an accuracy evaluation.

## Scope and prior capability

Stage 0.5 demonstrated the raw-image transport/vision/consensus primitive on synthetic red/blue images using the disposable contract at `0xaCC87512DD361EEcf329E85762C67194ae436C9a`. That does not establish property-condition reasoning. Stage 0.6 was intended to exercise the same `web.get → response validation → raw bytes → SHA-256 → vision → independent validator re-fetch/evaluation → consensus` path on property-condition photographs. No such property test occurred.

## Inventory and case results

- Admitted pairs: **0**.
- Hosted StudioNet cases: **0**.
- Local-only cases: **0**.
- Candidate sources excluded before case admission: gated custom-license kitchen dataset; fictional synthetic MIRL sample with embedded data URLs and one restricted image; contractor gallery without established image reuse rights; noncommercial disaster dataset; satellite-scale disaster imagery.
- Leader outputs, validator decisions, consensus outcomes, finality, authoritative reads, and result digests: **not applicable; no transaction**.

## Metrics

| Metric | Result |
|---|---|
| Correct classifications / benchmark cases | Not measurable (0 cases) |
| False new-damage findings | Not measurable (no denominator; not zero-error evidence) |
| False worsening findings | Not measurable |
| False repair findings | Not measurable |
| Appropriate `INSUFFICIENT_EVIDENCE` outcomes | Not measurable |
| Inappropriate certainty | Not measurable |
| Unchanged robustness under lighting/viewpoint variation | Not tested |
| Same-area reasoning | Not tested |
| Retrieval/digest failures on property images | Not tested |
| Prompt-injection resistance on property images | Not tested |
| Validator disagreement / property consensus behavior | Not tested |
| Source failures during GenVM retrieval | Not tested; excluded sources were screened before contract calls |

No percentage or production-accuracy claim is warranted.

## Findings that are supportable now

1. The Stage 0.5 mechanism is technically capable of fetching and interpreting two direct image byte streams in validator executions under its tested synthetic conditions; see [visual capability proof](MOVEOUT_VISUAL_CAPABILITY_PROOF.md).
2. This does not support an empirical claim about real property condition. The intended Stage 0.6 question remains unanswered.
3. For an eventual visual adjudicator, a two-layer result is safer: first record bounded observations (defect visible before/after, same area comparable, visibility/quality); only then derive a conservative condition label. A missing defect in a cropped/occluded/noncomparable image must not imply repair.
4. `NORMAL_WEAR` should not be a direct visual class. The visual layer can report visible change and evidence quality; a separate contextual process would need material/item age, tenancy duration, maintenance history, policy/lease and applicable jurisdictional standards. Liability, negligence, repair price, and deduction validity remain outside the visual engine.

These are design safeguards, not benchmark-validated performance findings.

## Recommended result boundary for any later experiment

Use a bounded machine-readable object with enumerated classification, same-area status, before/after visible observations, evidence quality, and an ambiguity/insufficiency reason. Validate enum membership, field lengths, and required-field combinations in contract code. Treat malformed output, unavailable sources, MIME mismatch, digest mismatch, noncomparable areas, and validator disagreement as failure/`INSUFFICIENT_EVIDENCE` or unresolved consensus; never coerce them into a damage decision. Keep raw model prose non-authoritative.

For every hosted case, freeze both source URLs and expected SHA-256 values before the call. Require each validator execution that votes to fetch both sources and compare its digests with the frozen case identity and leader proposal. Keep validator independence evidence distinct from protocol receipts: current StudioNet receipts do not provide a per-validator network transcript.

## Gate

**PROPERTY VISUAL FEASIBILITY: WEAK (provisional evidence gate only).** This is not a conclusion that the underlying model performs poorly; it means no property-domain behavior has been demonstrated, so visual condition intelligence is not yet justified as the product’s central adjudication primitive. The gate must be revisited only after an eligible, diverse, frozen dataset and hosted validator-consensus cases exist.

**Stage 0.6 status: BLOCKED — evidence sourcing.** **Ready for Stage 1: NO.** This report does not authorize or begin Stage 1.

## Next action

Provision a public static file host with stable direct PNG URLs and anonymous read access for these synthetic assets, or identify an appropriate existing repository/provider that may host this benchmark. Then populate the manifest URLs, verify hosted response MIME and digest from StudioNet, deploy the pinned disposable contract, and run the representative StudioNet subset. Do not submit a StudioNet transaction until public URL fetches and expected digest checks are ready.

## Stage 0.6B controlled synthetic update (2026-10-05)

### Dataset and ground truth

Fourteen synthetic, controlled image pairs were generated specifically for this benchmark. The detailed pair descriptions and expected classes are in [the dataset manifest](MOVEOUT_VISUAL_BENCHMARK_DATASET.md); individual image hashes and byte sizes are in [`benchmark_manifest.json`](../benchmarks/controlled-property-2026-10/benchmark_manifest.json). The contact sheet is 1024×1536, SHA-256 `7817020e02849c0de257154d8465d824216bae38b47640623337defe74b99eab`. The ground truth was manually fixed after crop review and before any GenLayer evaluation. The benchmark is synthetic; it does not establish production-grade real-world property accuracy.

### Coverage and observed execution

The frozen fixture categories cover unchanged lighting and viewpoint, pre-existing crack, new crack, new stain, worsening, repair, occlusion, cropped/noncomparable view, low quality, lookalike area, ambiguous mark, image-text prompt injection, and shadow confusion. They have **not been run** through the contract. No case has leader results, validator results, consensus outcome, finality, authoritative reread, or match/mismatch result.

- Expected cases in fixture manifest: 14.
- Hosted StudioNet cases: 0.
- Local GenLayer cases: 0.
- Local fixture integrity check: PASS — 14 case records and all 28 image SHA-256 values match local files.
- GenVM `genvm-lint lint`: PASS — 3 checks.
- GenVM `genvm-lint check`: PASS — SDK validation; contract `MoveOutVisualBenchmarkV1`, 1 view and 1 write method.
- Python syntax compilation: PASS.
- Direct VM tests: not run; no local GenVM test runner/test harness is available in this workspace.
- Integration/hosted tests: BLOCKED; there are no stable public HTTPS image URLs. No transaction has been submitted.
- GitHub CLI authentication check: FAILED; cached token is invalid. Connected GitHub API repository is unrelated, so no assets were published there.
- Google Drive anonymous sharing: unavailable through the connected share operation (domain/user sharing only), so it cannot give StudioNet validators public unauthenticated image access.

### Safety metrics — not measurable

False `NEW_DAMAGE`, false `WORSENED`, false `REPAIRED`, appropriate `INSUFFICIENT_EVIDENCE`, unchanged robustness, and prompt-injection resistance are all **not measurable because 0 hosted and 0 local GenLayer cases were executed**. Do not describe these as zero-error outcomes. No small-sample percentage is reported.

### Disposable contract

[`contracts/moveout_visual_benchmark_v1.py`](../contracts/moveout_visual_benchmark_v1.py) is a non-production proof contract pinned to `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`. It uses the previously StudioNet-proven `gl.nondet.web.get`, PNG/JPEG raw bytes, `hashlib.sha256`, `gl.nondet.exec_prompt(images=[body_a, body_b], response_format="json")`, and `gl.vm.run_nondet_unsafe` custom leader/validator flow. It checks caller-supplied frozen expected digests before the model call, independently refetches both URLs in validator execution, compares both hashes and bounded semantic fields, and requires HTTPS plus response status/MIME checks. It caps body size at 500,000 bytes. The contract has not been deployed or exercised against StudioNet.

Source SHA-256: `C98B7056D0B64065F3AEA99D6121F8831DBDE4329C8F901CE60D85BE4BB420B2`.

Its two-layer response separates observations from classification. Contract validation downgrades weak area/visibility/quality, schema errors, and logically inconsistent observations to `INSUFFICIENT_EVIDENCE`; `REPAIRED` also requires a visible repair indicator. It records model classification separately so a later prompt-injection result cannot be hidden by conservative normalization. Validator executions compare classification and structured observation enums, not free-form observation prose. No runtime trace, validator vote, or consensus assertion is claimed yet.

### Current gates

- **CONTROLLED PROPERTY VISUAL FEASIBILITY: WEAK (not demonstrated).** The fixtures and linted proof contract exist, but no model or validator has evaluated the fixtures. This is a gate status, not a poor performance score.
- **REAL-WORLD PROPERTY ACCURACY: NOT YET VERIFIED.**
- **READY FOR STAGE 1: NO.** Stage 0.6B remains incomplete until hosted tests produce finalized StudioNet evidence and safety results.
