# MoveOut Visual Verdict Architecture Review

**Status: architecture review complete. Stage 1 implementation has not started.** This review changes how MoveOut represents visual results; it does not change the product thesis, and it does not claim that visual condition classification is production accurate.

## Decision

MoveOut remains **“Move in with proof. Move out without arguments.”** It remains a visual property-condition protocol for tenants and landlords: a Property Condition Passport, guided room-by-room move-in and move-out inspections, frozen evidence, Visual Continuity, side-by-side comparison, Damage Map, maintenance history, Repair Timeline, RepairCheck, Same Damage Guard, Evidence Quality Warnings, Condition Receipts, disagreement/challenge flow, Deposit Report, and landlord/tenant review.

The architectural change is an authority boundary. A visual observation is retained as evidence, while an established condition is a separate, more consequential protocol finding. Consensus on an observation does not itself promote it to a finding.

**Stage 1 decision: READY for the deterministic protocol foundation only.** Stage 1 may build records, authorization, freezing, append-only history, and read APIs. It must not deploy production visual adjudication or imply that its condition labels are accurate. The prior Stage 0.9 visual safety gate remains failed. Real-world property visual accuracy remains **NOT YET VERIFIED**.

## What the experiments establish

Stages 0.5–0.9 established a bounded technical path on StudioNet (chain 61999): contract-side web retrieval, PNG vision inputs, structured observations, independent validator code paths, consensus outcomes, finalized transactions, and authoritative reads. Stage 0.9's pinned source fetched both commit-pinned PNGs independently on leader and active validator executions, checked their response digests, ran a bounded multimodal prompt, and required validators to support a consequential leader-derived classification. All 14 final v2 benchmark transactions finalized with majority agreement and authoritative rereads; 28/28 image digests matched the frozen manifest.

The synthetic benchmark recovered clear `NEW_DAMAGE` cases 2/2 and the clear `WORSENED` case 1/1, with no false `NEW_DAMAGE` or `REPAIRED`. It also produced a false `WORSENED` for the ambiguous mark (MOV-SYN-12), while three active validators agreed and one disagreed. Clear `PRE_EXISTING` cases were 0/2; clear `UNCHANGED` cases were 2/3; several low-quality, shadow, occlusion, crop, and lookalike cases failed closed. These results and transaction evidence are detailed in [the Stage 0.9 report](MOVEOUT_STAGE_0_9_POSITIVE_SIGNAL_RECOVERY.md).

The experiments do **not** establish real-world property accuracy, reliable handling across real camera/viewpoint variation, forensic provenance, legal responsibility, or production readiness. The dataset is synthetic and small. Consensus demonstrates agreement under the tested validator protocol; it does not establish physical truth. Correlated model interpretation can be wrong even when validators agree.

## Two levels of visual result

### Level 1: Visual Observation

Observations describe what the frozen visual evidence appears to show. Examples include `POSSIBLE_CHANGE`, `VISIBLE_MARK_PRESENT`, `VISIBLE_MARK_APPEARS_LARGER`, `POSSIBLE_NEW_DEFECT`, `POSSIBLE_REPAIR`, `VIEW_NOT_COMPARABLE`, `SHADOW_OR_LIGHTING_CONFOUNDER`, and `AREA_IDENTITY_UNCERTAIN`.

An observation is not an accusation, responsibility assignment, or established condition. Keep its evidence links and uncertainty even when the protocol cannot promote it.

### Level 2: Established Condition

Established conditions are bounded protocol findings: `UNCHANGED`, `PRE_EXISTING`, `NEW_DAMAGE`, `WORSENED`, `REPAIRED`, or `INSUFFICIENT_EVIDENCE`. Each finding is derived only when its class-specific evidence predicates are satisfied. Otherwise, retain the observation and record `INSUFFICIENT_EVIDENCE` or an unresolved state.

The Condition Receipt must show three distinct things: the leader's proposal, the consensus outcome (including disagreement or failure), and the established condition after deterministic promotion rules. Validator agreement on “the mark appears longer” is not enough to establish `WORSENED`.

## Promotion gates

The following are protocol gates, not accuracy guarantees. Deterministic code should apply the predicates to the accepted structured observation and frozen evidence references; it should not invent missing visual facts.

| Finding | Minimum promotion evidence | Abstain when |
|---|---|---|
| `NEW_DAMAGE` | Same physical area is established; both move-in and move-out views and image quality are sufficient; the relevant defect is absent before and present after in the shared area; relevant confounders are absent or explicitly not material. | Area identity, absence/presence, quality, visibility, or a material lighting, shadow, viewpoint, scale, crop, or occlusion explanation is uncertain. |
| `WORSENED` | Same physical area and same defect are established; both views are sufficient; a specific physical increase is observed (such as extent, length, width, affected area, breakage, or material loss); evidence quality supports that claim; relevant confounders are absent or explicitly not material. | Defect identity or changed extent is uncertain, a material confounder could explain the apparent change, or validator evaluation disagrees. A larger-looking mark alone is only an observation. |
| `REPAIRED` | Same area and defect are established; before evidence shows the defect, later evidence is sufficiently visible and shows a decrease or absence; the comparison is not materially confounded; surface-restoration evidence supports repair. | Disappearance could be explained by view, lighting, occlusion, crop, or quality, or repair evidence is missing/uncertain. |
| `PRE_EXISTING` | The relevant defect is visible in frozen baseline/move-in evidence tied to the same identified area. Where the finding compares a later image, the later view must establish that it is the same defect, not merely a similar mark in a lookalike area. | Baseline visibility, area identity, or requested cross-image identity cannot be established. Do not equate temporal origin with “unchanged.” |
| `UNCHANGED` | Same area is established, both views and quality are sufficient, and no relevant defect is visible in either image under the bounded inspection scope. | A defect is visible/uncertain, a material view difference prevents comparison, or evidence is insufficient. “Unchanged” is limited to what the evidence can show. |
| `INSUFFICIENT_EVIDENCE` | Default when any required predicate is absent, contradictory, or uncertain. Preserve supported observations and the exact unresolved predicates. | Not applicable; this is the fail-closed result. |

For a consequential positive, validators must independently retrieve and evaluate both frozen evidence references and support the required observation fields. A mismatch in source digest or critical observation must not be converted into certainty. The accepted result should be inconclusive or remain unresolved according to the transaction protocol. Consensus is an additional protocol check, never a substitute for the evidence gates.

## MOV-SYN-12 representation

The Stage 0.9 false `WORSENED` came from a majority-agreed observation asserting same area, same defect/location, sufficient visibility, and `LENGTH_INCREASE` with no material confounder. The established-condition derivation therefore followed its encoded predicates, but the visual interpretation was wrong for the ambiguous pair. The review does not relabel that history or claim a prompt can eliminate correlated error.

Under the reviewed result model, the receipt would preserve an observation such as `VISIBLE_MARK_APPEARS_LARGER` and associate it with the two evidence IDs. Because the pair is ambiguous and physical increase is not established strongly enough, the established condition would be `INSUFFICIENT_EVIDENCE`; the unresolved element would identify whether mark identity, scale/viewpoint, or actual extent change is uncertain. A human challenge or additional comparable capture can append evidence and a later evaluation. The earlier observation and receipt remain in history.

## Evidence and Visual Continuity

Evidence records should bind at least: Evidence ID, Property ID, Tenancy ID, Inspection ID, Room ID, Area/Item ID, submitter, evidence type, source reference, expected SHA-256, submitted timestamp, freeze timestamp, and status. Frozen evidence is immutable. A correction or replacement is a new append-only record that explicitly supersedes or supplements an earlier one; it does not erase it. Hashes identify bytes, while URL, capture metadata, and submitter claims provide provenance context. A digest alone does not prove when, where, or by whom an image was captured.

Visual Continuity remains a core product feature. Stable Room IDs and Area/Item IDs, the previous-photo reference, capture guides or overlays where useful, visible-landmark guidance, and evidence-quality warnings should help tenants and landlords capture approximately comparable views of the same wall, fixture, floor section, appliance, or item. Do not promise perfect alignment or automated camera calibration. If the relevant area cannot be established, the condition result remains insufficient.

Tenant and landlord statements such as “this crack is new,” “this stain was already here,” or “this was repaired in August” are claims and evidence metadata. They can be linked to an inspection, receipt, or maintenance record and evaluated against frozen evidence, but do not set protocol truth by themselves.

## Condition Receipt and challenge

Every Condition Receipt should make the following sections explicit:

1. **Evidence:** evidence IDs, inspection/room/area links, source references, digests, freeze status and timestamps.
2. **Observations:** bounded visual observations, which image(s) support them, and uncertainty/confounders.
3. **Consensus Result:** leader proposal and whether validator evaluation agreed, disagreed, failed, or was inconclusive. A vote summary is not a truth score.
4. **Established Condition:** the class, or `INSUFFICIENT_EVIDENCE`, plus the promotion predicates that passed or failed.
5. **Unresolved/Uncertain Elements:** area identity, visibility, defect identity, change basis, source drift, or other specific open questions.
6. **Challenge/Finality Status:** challenge state and any later append-only review/result, distinct from transaction finality.

A landlord or tenant can challenge a receipt by attaching a claim and additional evidence to the relevant Property, Tenancy, Inspection, Room, or Area/Item record. A challenge does not edit frozen evidence or silently overwrite an established result. The protocol records challenge authorization/state, a new evaluation, and its finality; it preserves prior receipts and shows which result is current under the protocol. Product review remains centered on the property images and inspection timeline, not a generic court workflow.

## Condition, normal wear, and deposits

First determine only what physical condition/change the evidence supports. Do not classify `NORMAL_WEAR` from two images alone. Tenancy duration, material, item age, maintenance, lease terms, policy, and jurisdiction belong to a separate later contextual layer. Keep physical condition separate from responsibility, policy, and liability.

`NEW_DAMAGE` does not mean the tenant owes money. MoveOut V1 does not custody or automatically distribute rental deposits. The Deposit Report explains evidence and protocol findings, includes unresolved points and challenges, and does not make an automatic financial allocation.

## GenLayer responsibilities

GenLayer remains materially necessary for the semantic evidence questions; it is not a decorative ledger. The deterministic and nondeterministic responsibilities should be divided as follows:

| Deterministic protocol logic | Nondeterministic evidence interpretation |
|---|---|
| IDs and Property → Unit → Tenancy → Inspection → Room → Area/Item hierarchy; ownership and authority; evidence references/digests; freeze and append-only/supersession semantics; timestamps and lifecycle states; authorization; bounded result/storage schema; deterministic promotion predicates; challenge state; receipt and finality records. | Whether images appear to show the same relevant physical area; what visible conditions appear; whether paired evidence supports a specific physical change; how uncertainty and visual confounders apply; whether supporting repair/maintenance records semantically support a repair observation. |

For visual calls, leader and active validators should independently retrieve the evidence and perform the bounded interpretation, with digest and structured-field checks. Active validators evaluate the leader's proposal against their own execution; inactive/idle participants do not count as independent observations. Disagreement, changing bytes, source failure, malformed model output, or failed quality predicates leads to inconclusive/insufficient handling. A finalized consensus receipt proves protocol completion under that execution, not the physical condition itself.

## Safety principles

- Preserve the original inspection-and-visual-comparison experience.
- Keep observation separate from established condition and from responsibility.
- Fail closed on missing, conflicting, low-quality, non-comparable, or materially confounded evidence.
- Preserve useful observations and dissent even when promotion fails.
- Never let a claimant statement or text embedded in an image act as an instruction or ground truth.
- Treat validator votes as protocol evidence, not proof of physical reality.
- Keep frozen evidence and all later corrections/challenges append-only.
- Avoid certainty language beyond the exact area, views, and predicates the evidence supports.

## Stage 1 revised scope

Stage 1 can build the deterministic foundation without resolving real-world visual accuracy and without deploying production visual adjudication. Its scope may include Property, Unit, Tenancy, Inspection, Room, Area/Item, Evidence, Condition Record, Visual Observation Record, Established Condition Record, authority/ownership, freeze semantics, append-only history, bounded storage, and read APIs. Records should make the two output levels explicit and allow an unresolved/insufficient state, even if no production model is wired in.

The original MoveOut flow can then bind a guided inspection to frozen room/area evidence, carry visual continuity references through the Passport and maintenance/repair timeline, and present receipts and challenges in that product context. Building these protocol primitives is authorized by the Stage 1 readiness decision, but this review task stops before implementation.

Before any production visual adjudication or accuracy claim, further research needs rights-cleared real property image pairs with defensible labels, representative variation in viewpoint, distance, lighting, material and image quality, same-defect and lookalike cases, noncomparable views, repairs, ambiguous marks, and measured false-positive/false-negative behavior. Validator variance and the ability to audit independent evidence access also need assessment.

**REAL-WORLD PROPERTY VISUAL ACCURACY: NOT YET VERIFIED.**

## Sources

- [Stage 0.5–0.9 capability and provenance history](MOVEOUT_VISUAL_CAPABILITY_PROOF.md)
- [Controlled property visual benchmark summary](MOVEOUT_PROPERTY_VISUAL_BENCHMARK.md)
- [Stage 0.9 positive-signal recovery, root-cause review, source/runtime and hosted receipts](MOVEOUT_STAGE_0_9_POSITIVE_SIGNAL_RECOVERY.md)
- Final Stage 0.9 disposable contract: [`moveout_visual_safety_stage09_v2.py`](../contracts/moveout_visual_safety_stage09_v2.py), SHA-256 `0E63BA93464AFF2DF2BA51859E397083FFA3A48ABAE481917869E863694C81E4`.
- Final Stage 0.9 hosted result rows: [`stage09_v2_results.ndjson`](../benchmarks/controlled-property-2026-10/stage09_v2_results.ndjson).
