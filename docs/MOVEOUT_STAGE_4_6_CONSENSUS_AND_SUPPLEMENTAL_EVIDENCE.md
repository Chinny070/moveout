# MoveOut Stage 4.6 — Consensus Safety and Supplemental Evidence Resolution

**Status: PARTIAL — design investigation only.** No production contracts, schemas, prompts, APIs, or records were changed. No deployment, hosted transaction, migration, or Stage 5 work occurred. This report is based on the current repository at baseline `4224128f5852ff77bcd86df9d29060e18c53c941`, current official GenLayer documentation reviewed on 2026-10-09, and source-level inspection. It is not hosted verification of consensus internals.

## 1. Scope and reviewed evidence

Read in full:

- [Stage 4.3 target-region visibility design](MOVEOUT_STAGE_4_3_TARGET_VISIBILITY_DESIGN.md)
- [Stage 4.4 target-visibility decisions](MOVEOUT_STAGE_4_4_TARGET_VISIBILITY_DECISIONS.md)
- [Stage 4.5 implementation readiness](MOVEOUT_STAGE_4_5_IMPLEMENTATION_READINESS.md)

Also inspected `contracts/moveout_protocol_v1.py`, its evidence freeze, capture-slot continuity, observation/equivalence paths, and the existing local verification suite. The working tree was clean at start, `main` was at `4224128`, and `origin/main` was configured. A remote head read is recorded below.

Stage 4.4 has locked a strict invariant: *any* mismatch in safety-critical target/evidence observations must leave the attempt unresolved and must not store the leader proposal as an accepted observation. Stage 4.5 correctly marked implementation readiness blocked because GenLayer documents majority acceptance and does not give a contract the other validators' independent candidate outputs.

## 2. Consensus model findings

### 2.1 Current documented protocol behavior

GenLayer's current Equivalence Principle documentation describes a leader proposal and a validator callback returning accept/reject. Validators independently execute their validation path. The proposal is accepted when a majority agrees; if the majority rejects, the network rotates the leader and retries; if no consensus is reached, the transaction becomes undetermined and does not modify contract state. The accepted leader result is the value the contract receives; validators' independent intermediate answers are not automatically persisted on-chain. `run_nondet_unsafe` treats an uncaught validator exception as disagreement. See the official [Equivalence Principle](https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle) and [Non-determinism](https://docs.genlayer.com/developers/intelligent-contracts/features/non-determinism).

Protocol documents now describe a stake-weighted validator committee, commit/reveal votes, an accepted result on the required majority, and an `Undetermined` result when no consensus is reached. “Accepted” means protocol acceptance, not unanimity or visual truth. The current [Optimistic Democracy protocol reference](https://github.com/genlayerlabs/genlayer-docs/blob/main/pages/understand-genlayer-protocol/core-concepts/optimistic-democracy.mdx) documents that model.

### 2.2 Answers to the Stage 4.6 questions

| Question | Finding | Evidence class |
|---|---|---|
| Is native unanimity required per operation? | **No, not in the documented contract-level Equivalence Principle.** The documented acceptance rule is majority. | Official documentation. No StudioNet transaction run in this stage. |
| Can a contract detect each individual validator's disagreement? | The validator callback knows whether its own independently produced result matches the leader candidate. The contract execution does not receive the complete committee's individual votes/candidates as a value it can inspect. | Official callback signature and independent-execution docs; current contract code. |
| Are votes/candidate outputs accessible to contract code? | The leader candidate is exposed to `validator_fn`; aggregate receipt/vote status is available after protocol execution to external clients. Peer candidate outputs are not automatically stored or passed into the contract. | Official Equivalence Principle; existing hosted Stage 4.1/4.2 reports note vote counts without dissenting fields. |
| Can a custom equivalence callback reject a majority-accepted proposal because one validator disagreed? | **No.** It can return `False` for that validator's own mismatch. That vote contributes to protocol consensus, but the contract callback cannot gather other validators' results and apply a unanimous threshold. A majority may still accept. | Direct consequence of documented callback + majority protocol. |
| What happens if the protocol cannot obtain its required majority? | Validators/leader rotate or retry per protocol. If unresolved after available rounds, transaction is undetermined; no agreed state transition is committed. Client code must render that as unresolved and reread authoritative contract state. | Official docs. Exact StudioNet error/status mapping is version-specific and must be tested for the eventual target operation. |
| Is consensus configuration adjustable per contract, operation, or deployment? | Studio operators can configure the validator set/participants, providers, models, stake, and JSON config. The reviewed public contract/SDK references expose no operation- or contract-level quorum/unanimity selector. No public supported setting to require unanimity on one MoveOut method was found. | Official Studio validators documentation; negative API search is not proof no private/operator feature exists. |

**Important distinction:** exact equivalence means each validator that validates the leader candidate returns agree only if the safety-critical comparison passes. It does *not* mean every validator must agree. Equivalence is a per-validator predicate; the protocol aggregates votes using its quorum rule. A `Comparative` prompt wrapper does not change that quorum rule.

Studio configuration can shape the active validator population and models, but configuring a smaller or more similar population is not an application guarantee of unanimity and is outside this contract-level design. It could also reduce diversity. Local tests or Direct Mode cannot turn this into a StudioNet unanimity guarantee.

### 2.3 Current MoveOut source and local test boundary

In `contracts/moveout_protocol_v1.py`:

- `_observation_equivalent` at lines 430–475 compares evidence provenance and selected critical fields from the leader result and one validator's independently run candidate. For pairwise output it checks continuity/feature/difference/uncertainty fields; it is not a committee vote counter.
- `observe_evidence` at lines 1822–1856 and `observe_evidence_pair` at lines 1859–1911 call `gl.vm.run_nondet_unsafe`, then store the returned accepted candidate via `_record_observation`. The validator independently re-runs retrieval and vision.
- This is good independent evidence evaluation, but it implements the validator's yes/no vote only. It cannot make one dissent veto the network's majority or persist the dissenting candidate.

Existing Direct Mode tests exercise callback comparisons by replaying the captured validator callback with mocks. They prove local helper behavior, not committee quorum, accepted-versus-undetermined network status, rollback, or authoritative post-transaction state. Existing Stage 4.1/4.2 StudioNet records show majority-agree receipts with both `AGREE` and `DISAGREE` votes; those records do not reveal what the dissenters saw. Thus current MoveOut has *observed majority acceptance with dissent*, but not a hosted target-visibility transaction that demonstrates how dissent fields affect stored state.

Evidence classes used in this report:

1. **Docs/API:** current public protocol/Studio docs and callback shape.
2. **Source/local:** checked contract source and local tests; no network quorum simulation.
3. **Hosted history:** previously recorded Stage 4.1/4.2 StudioNet receipts and rereads; relevant evidence but not rerun here.
4. **Not established:** any unanimity mode, per-contract quorum override, or machine-readable per-validator visual candidate payload available to MoveOut code.

## 3. Approaches considered and recommendation

### A — Require native unanimity

This is the only direct match for Stage 4.4's “any dissent blocks” rule. The current documented contract/runtime surface provides majority consensus and no per-operation unanimity control was found. Therefore it is **not currently implementable as a MoveOut contract invariant through the documented APIs**. Do not ship code that claims unanimity merely because all locally replayed callbacks agree or a particular hosted receipt happened to show no dissent.

### B — Additional application-level validation

The current `validator_fn` independently retrieves evidence, runs its own visual interpretation, compares critical fields, and returns a Boolean. This prevents that validator from agreeing when its own result differs, but still leaves protocol majority as the acceptance rule. Adding another `run_nondet_unsafe` call does not reveal the first call's other candidates and gives the second call its own majority threshold; it is not unanimity. App-level checks are still necessary for evidence identity, schema invariants, no-absence gates, and exact candidate equality, but they cannot detect hidden peer dissent.

### C — Conservative `INSUFFICIENT/UNRESOLVED` policy

This is an achievable safety mitigation: invalid or uncertain target visibility must produce an explicit insufficient result; a confident absence must be forbidden unless every Stage 4.4 visibility predicate is satisfied; source/digest mismatch or validator rejection must prevent acceptance; client must treat an undetermined transaction as unresolved; observations must never become liability/deposit conclusions. A leader proposal whose *quorum* of validators accepts it can still be semantically wrong, and minority dissent can remain hidden. Conservative wording reduces harmful inference but does not provide the strict Stage 4.4 no-dissent guarantee.

### D — Independent verification

Independent validator retrieval and interpretation are already the right foundation. Additional independently sourced or human-reviewed verification may reduce correlated model error if it is separately authenticated and explicitly represented. It still does not make a minority veto possible, reveal private candidates, or establish unanimity. A second majority-based call, a frontend vision result, or a local mock is not a substitute. Any separate human adjudication workflow needs its own authority, record, and appeal policy and is outside this stage.

### Recommendation and replacement text requiring owner approval

Keep Stage 4.4's absolute invariant unmodified until the product owner decides. For an implementation to proceed on currently documented GenLayer behavior, the owner would have to explicitly replace the unanimity wording with a majority-aware rule such as:

> “Each validator independently verifies the leader's safety-critical result against the frozen evidence and exact digests. A validator returns agree only on exact agreement for evidence identity, target identity, target visibility, obstruction, frame coverage, clarity, feature observation, and continuity. GenLayer protocol majority determines transaction acceptance; one or more dissenting votes do not by themselves prevent acceptance. If the protocol does not reach its required majority, no observation is accepted and the client records/displays the attempt as unresolved after checking authoritative contract state. An accepted observation is a quorum-validated model observation, not a unanimous validator finding or a statement of physical truth. The application must not claim unanimity and must not infer defect absence unless all target-coverage gates are met.”

This replacement weakens the literal “any mismatch means no accepted observation” rule. It requires owner approval; do not silently adopt it. If the owner will not approve a majority-aware semantics and GenLayer does not expose a supported unanimity mechanism, the safe decision is to keep target-sensitive confident outputs disabled/unresolved and treat this as a blocker to implementation readiness.

## 4. Supplemental evidence after a frozen inspection

### 4.1 Existing lifecycle constraints

Current `freeze_inspection` (around lines 1666–1695) commits room, area, condition, evidence, and capture-slot membership. Current write APIs use `_record_parent_context`, which requires an open inspection for child creation. Existing evidence must be frozen before the inspection can freeze. Therefore a close-up requested after an observation of a frozen inspection **cannot be appended to that same inspection** without violating its immutable snapshot.

Current `create_capture_slot` and `_validate_continuity` (around lines 792–835 and 1348–1397) can link a new inspection's capture slot to an older frozen slot/evidence with the same property/unit/tenancy/room/area hierarchy. That relation means intended workflow correspondence; it is not proof that the new image depicts the same physical target. Stage 4.4 target nomination records and target-specific supplement APIs do not exist yet.

### 4.2 Smallest safe supplemental-capture design

1. Keep the original inspection, target nomination, evidence, digests, and observation immutable. A visibility failure creates an append-only `supplement_request` referencing the original `inspection_id`, `target_id` and version/digest, original `evidence_id`/digest, exact unresolved predicate, creator, and request ID. Do not add a child to the frozen original.
2. Create a new inspection/revision or clearly typed supplemental inspection, referencing the original frozen inspection. Reuse the same property/tenancy/unit/room/area and target nomination version as references, not as proof. A revised target nomination must be a new version and cannot silently inherit an old negative observation.
3. Capture the overview/close-up as a new Evidence record with a new evidence ID, immutable source, independently frozen bytes, digest, freeze metadata, and provenance-verification record. Never overwrite or re-freeze the old image. Multiple submissions remain separate append-only candidates under the same supplement request; retries are idempotent and duplicate digest handling is explicit.
4. Store an append-only relationship/bundle record that references both the frozen original evidence and each supplemental evidence record. It should bind supplement request ID, original and supplemental inspection IDs, target nomination version/digest, both evidence IDs/digests, and the requested purpose. Do not mutate the original inspection to add a backward pointer; query supplements by the new relation index.
5. Independently validate target continuity from the nominated reference region, shared distinctive landmarks, target appearance, and surrounding context. Shared IDs, room label, matching wall color, user assertion, or a capture-slot link alone is insufficient. Record `SUPPORTED`, `NOT_SUPPORTED`, or `UNCERTAIN` separately from each image's visibility result. A same-area but different wall/fixture or a misleading close-up stays unresolved.
6. An image can clear only the visibility blocker for the same target if continuity is supported and that supplemental image independently satisfies target location, frame, obstruction, clarity, and target visibility. Conflicting overview/close-up observations stay unresolved; no “best image wins.” A new clear view cannot erase earlier evidence or make a past image appear adequate.
7. Reject supplements whose request/target/evidence parent bindings mismatch, evidence is not frozen/provenance-verified, digest changes, target version is stale or ambiguous, or inspection chain does not point backward. Reject storage writes to the frozen inspection. Persist each accepted observation as a new append-only version referencing the full ordered evidence set; preserve the earlier unresolved observation.

The existing evidence and capture-slot records provide reusable primitives, but not the target nomination, supplement-request, request status, target-version binding, or append-only supplement bundle. This is a design proposal, not a claim that current APIs already implement these operations.

## 5. Revised test specification

The table separates deterministic rules from any actual visual accuracy claim. `Local` means a pure schema/lifecycle/callback test can verify the invariant with supplied values. `Hosted/visual` means that the visual correspondence or consensus outcome needs a separate live model/runtime evaluation and cannot be proven by injecting the expected answer in a test fixture.

| Case | Expected safe result | Deterministic local proof | Separate runtime / visual proof |
|---|---|---|---|
| 1. Chair hides nominated target crack | `INADEQUATE`/unresolved; never confident absent | Given candidate obstruction/visibility fields, reject `ABSENT`; preserve unresolved | Blind image evaluation for target localization and chair obstruction; hosted consensus and reread |
| 2. Unobstructed crack | May report bounded local `PRESENT` only if nominated pixels are located/clear | Validate candidate consistency and prevent claims about unseen remainder | Human-reviewed visual test; no fixture label-as-model proof |
| 3. Clean but unobstructed nominated target | `ABSENT` is schema-permitted only if every Stage 4.4 predicate is met | Table-driven predicate/invariant test | Blinded false-negative evaluation on held-out property images |
| 4. Unrelated furniture outside nominated region | Target can remain adequate; unrelated furniture alone does not imply obstruction | Validate target-scoped obstruction semantics on supplied candidate | Visual evaluation showing target/furniture spatial relation |
| 5. Target outside image frame | `OUTSIDE`, inadequate, no absence; distinct from obstruction | Reject contradictory absence/crop-obstruction combinations | Curated crop fixture and blind model evaluation |
| 6. Shadow on target | If detail is not assessable, clarity/visibility is insufficient; shadow is not a foreground object/crop label by itself | Enforce insufficient-clarity -> no absence | Human-rated shadow/clarity visual evaluation |
| 7. Target location uncertain | `NOT_LOCATABLE`/`UNCERTAIN`; no invented target or negative | Missing/ambiguous nomination and uncertain location tests | Blind localization on lookalike surfaces |
| 8. Overview and close-up conflict | Preserve both; aggregate unresolved | Deterministic conflict aggregation and append-only storage tests | Validator/model disagreement test and hosted outcome reread |
| 9. Shared IDs, different nominated targets | Reject linkage; close-up cannot resolve target | Mismatched target ID/version/digest rejection | Visual lookalike test to see if continuity model rejects the wrong surface |
| 10. Misleading close-up / same room, different wall | `NOT_SUPPORTED` or `UNCERTAIN`; no defect absence | Ensure unsupported/uncertain continuity cannot clear blocker | Blinded cross-surface correspondence evaluation |
| 11. Supplemental write targets a frozen inspection | Reject; original bytes and membership unchanged | Lifecycle test asserting frozen inspection remains unchanged and no membership append | Hosted test only after approved implementation; authoritative reread of old and new records |
| 12. Two validators disagree on a safety field but protocol majority agrees | Under current protocol, transaction may be accepted with leader candidate; this violates Stage 4.4 absolute invariant | Local callback confirms the dissenting validator returns false, but cannot prove unanimity | Hosted, intentionally divergent validators required to characterize votes/receipt/state; current docs already establish majority semantics |
| 13. No protocol majority | No accepted observation; transaction unresolved/undetermined; no state write | Local unit test can test client state mapping only, not chain rollback | Hosted rejected/undetermined operation followed by authoritative storage reread |
| 14. Same evidence digest, same target, matching candidates | Candidate passes per-validator comparison; quorum still required | Deterministic identity/equivalence tests | Hosted success/finality/reread to verify StudioNet integration |
| 15. Digest or provenance verification differs | Reject candidate; no accepted observation | Exact digest/verification ID mutation tests | Optional hosted provenance test; not needed to prove local guard |
| 16. Model returns malformed/uncertain values | Explicit inconclusive/unresolved; never coerce to absent | Parser/normalizer tests with missing/extra/invalid fields | Hosted model failure behavior and authoritative reread |
| 17. Image contains prompt-injection text | Text remains untrusted pixels; does not modify schema/target/promotion | Input data cannot alter deterministic bindings or enum constraints | Adversarial multimodal visual evaluation |
| 18. Retry after a rejected or duplicate supplement submission | New evidence remains separate; idempotent retry does not mutate original | Request replay/digest uniqueness/append-only tests | Hosted transaction and authoritative reread when implemented |

Local test assertions can prove deterministic validation, authorization, digests, append-only behavior, and what one validator callback returns. They cannot prove visual target identity, actual surface coverage, other validators' hidden outputs, majority/unanimity, network rollback, finality, or model accuracy. Those require purpose-built integration and blinded evaluation.

## 6. Plan and remaining blockers

### Ordered next steps (no implementation performed)

1. Obtain explicit product-owner decision on the Stage 4.4 quorum conflict: retain strict any-dissent rule and block target-aware certainty absent a supported unanimity policy, or approve the majority-aware replacement wording above. Do not implement the replacement implicitly.
2. Before any production work, verify the exact target StudioNet's available consensus/quorum controls against current release documentation and runtime/SDK; if no operation-level unanimity feature is available, mark the strict rule unsupported for that network.
3. Approve a supplemental inspection/revision model that leaves original frozen records immutable, plus the explicit request and relation record schema/API. Determine deployed-record migration strategy separately; no canonical MoveOut deployment exists in the baseline reports.
4. Implement only after authorization: append-only request/bundle and target links, evidence freeze/provenance checks, same-target continuity fields, and deterministic rejection paths. Preserve old V1 reads and never add evidence to a frozen inspection.
5. Add deterministic tests from rows 1–18 and the Stage 4.4 matrix, clearly tagged as schema/lifecycle tests, not visual-model accuracy tests.
6. In a separately authorized integration stage, test a successful quorum, deliberate validator dissent that still reaches majority, no-majority/undetermined behavior, receipt visibility, finality, and authoritative rereads. Do not use a leader-only test mode.
7. Separately conduct a blinded visual evaluation with independently reviewed target regions, including wrong-wall close-ups and obstruction/crop/shadow cases. Report uncertainty and false-negative rates; never convert consensus into a truth claim.

### Blockers

- **Hard product/runtime blocker:** Current documented protocol uses majority; no supported per-contract/per-operation unanimity control or peer-candidate access was identified. Stage 4.4's strict no-dissent acceptance cannot be guaranteed by current contract callbacks.
- **Owner decision blocker:** A majority-aware rewrite of Stage 4.4 is a product safety change and needs explicit approval.
- **Supplement lifecycle blocker:** Current frozen inspection cannot accept later evidence. A new supplemental inspection/revision and immutable relation/request APIs are design additions, not present functionality.
- **Runtime proof blocker:** This stage did not run hosted transactions. StudioNet-specific dissent visibility, no-majority finality, and authoritative state behavior for this feature remain to be verified in an authorized integration stage.
- **Visual truth limitation:** Independent model agreement can be correlated and wrong. Even unanimity would not establish physical truth or legal responsibility.

## 7. Checks, changes, and stop state

- Files changed: this report only.
- Production code/schema/prompt: unchanged.
- Hosted transactions/deployments: none.
- Stage 5: not started.
- Existing local verification: run after writing this report; results are recorded in the completion response and are checks of the unchanged production baseline.
- Commit/push: documentation-only commit after checks pass; remote head and worktree status must be confirmed before completion.
- Readiness: **PARTIAL**; design conclusions are clear, but implementation remains blocked on explicit owner decision for consensus semantics and supplemental capture lifecycle approval.

## References

- [GenLayer Equivalence Principle](https://docs.genlayer.com/developers/intelligent-contracts/equivalence-principle) — validator callback, majority acceptance, leader rotation, undetermined outcome, peer outputs not automatically stored, and unsafe callback errors.
- [GenLayer Non-determinism](https://docs.genlayer.com/developers/intelligent-contracts/features/non-determinism) — independent execution; storage writes after consensus.
- [GenLayer Error Handling](https://docs.genlayer.com/developers/intelligent-contracts/features/error-handling) — validator disagreement and error handling.
- [GenLayer Studio: Accessing and Configuring Validators](https://docs.genlayer.com/developers/intelligent-contracts/tools/genlayer-studio/validators) — configurable participants/models/stake/config; no contract-level unanimity selector documented.
- [GenLayer Optimistic Democracy](https://github.com/genlayerlabs/genlayer-docs/blob/main/pages/understand-genlayer-protocol/core-concepts/optimistic-democracy.mdx) — stake-weighted committee, majority decision, commit/reveal and protocol outcomes.
- [Stage 4.1 consensus diagnostics](MOVEOUT_STAGE_4_1_CONSENSUS_DIAGNOSTICS.md) and [Stage 4.2 verification](MOVEOUT_STAGE_4_2_VERIFICATION.md) — prior hosted majority/dissent observations; receipts did not disclose dissenting visual values.
