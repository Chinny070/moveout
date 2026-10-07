# MoveOut Stage 3: validator-side evidence retrieval and provenance

## Purpose and boundary

Stage 3 adds a bounded, append-only record of whether a frozen PHOTO evidence URL independently returns the expected original PNG/JPEG bytes. The verification is deterministic byte/provenance checking. It does not interpret the photograph, decide a property condition, create a visual observation, establish a damage finding, or adjudicate a deposit.

The Stage 2 evidence record is frozen before verification. Its source URL and caller-declared SHA-256 are immutable metadata. Stage 3 retrieves the URL again on the leader and independently on participating validators, validates the response and image structure, hashes the original bytes, and compares compact normalized results through a custom nondeterministic validator function. Raw bodies are not returned or persisted.

## Contract behavior

`verify_evidence_provenance(tenancy_id, evidence_id, request_id)` requires:

- the caller to be a participant in the tenancy;
- exact tenancy, property, unit, inspection, room and area bindings;
- both the inspection and evidence to be frozen;
- `evidence_type == PHOTO`;
- a lowercase 64-character hexadecimal expected digest;
- an HTTPS source URL passing the contract's string-level public-host checks.

The leader calls `gl.nondet.web.get(source_url)` and normalizes the response to status, normalized content type, body size, expected digest, retrieved digest (when a body is eligible), source URL digest, outcome and failure code. The validator callback receives the leader proposal, independently makes the same GET, and compares its normalized result with the proposal. The custom callback compares deterministic compact data rather than large, mutable raw response bodies.

The accepted response is exactly HTTP 200 with a nonempty `bytes` body no larger than 8 MiB. The content type must be `image/png` or `image/jpeg`; PNG signature/chunk framing/IHDR dimensions/IEND marker or JPEG SOI/EOI markers must match the declared media type. Only then does the contract compute SHA-256 and compare it with the expected digest.

Outcomes include `VERIFIED`, `DIGEST_MISMATCH`, `INVALID_CONTENT`, `UNAVAILABLE`, and `UNSUPPORTED`. HTTP non-200 responses become `UNAVAILABLE/HTTP_STATUS`; fetch exceptions become `UNAVAILABLE/FETCH_ERROR`; HTML or missing/non-image media type becomes `INVALID_CONTENT/NON_IMAGE_CONTENT`; unsupported image MIME and oversize bodies fail closed. No unstable exception text, full URL, response body, or image bytes are stored in the verification record. The record stores a SHA-256 of the source URL, expected/retrieved digest, outcome, status, content type, body size, timestamp, and previous-record link.

Verification records are append-only and bounded. Re-verification preserves earlier records and updates a latest pointer. `get_evidence_verification`, `get_evidence_verification_status`, and paginated `list_evidence_verifications` expose the results. The summary distinguishes historical verification from latest result and reports whether the latest digest/outcome differs from the first record.

## Validator execution and disagreements

Each validator that invokes the callback re-fetches the URL and re-runs response validation, format checks and hashing; validators do not rely on bytes supplied by the leader. The leader proposes the normalized retrieval result. The callback compares the validator's independent normalized result to the leader proposal. On a mismatch, that validator does not agree with the proposal. GenLayer consensus may obtain more votes/rotate leaders; if required consensus cannot be reached, the transaction does not produce a finalized provenance record. There is no claim that all validators are guaranteed to execute if quorum has already been reached.

Direct Mode tests explicitly vary the mocked bytes between leader and validator and confirm the independent callback rejects the changed bytes. StudioNet proof calls finalized with `MAJORITY_AGREE`; their receipts showed three `AGREE` votes and two `IDLE` votes for each provenance transaction. This establishes validator-supported agreement for those retrievals, not universal participation by every validator in each finalized round.

## Provenance model and risk

- `evidence_id` binds a frozen protocol record to a source URL string and caller-supplied expected digest.
- The expected digest is not independently proved at submission time; it becomes supported only when a verification record reports the retrieved bytes' digest.
- The verification stores a hash of the source URL rather than the full URL, reducing stored source data while preserving exact URL-string binding.
- `created_at` is the chain/runtime time of the verification record. `frozen_at` is the evidence metadata freeze time. The contract does not prove when the remote image was originally captured.
- A URL hash plus a matching content digest establishes what bytes validators retrieved for this verification, not authorship, capture time, camera provenance, property identity, or truth of any visual claim.
- A commit-pinned URL can reduce source mutability; it does not replace independent retrieval. Live mutable URLs can produce different leader/validator bytes, which is a consensus/retrieval disagreement risk. Local Direct Mode covers this by changing the mocked response between leader and validator; no hosted mutable-source change was performed.
- Source validation checks HTTPS and rejects malformed authority forms, user-info, fragments, whitespace, backslashes, ports and percent escapes in the authority. It does not implement a maintained domain allowlist, DNS resolution policy, or independent guarantee that the host cannot redirect. Redirect behavior was not hosted-tested. Only a response status of 200 is accepted; whether `gl.nondet.web.get` follows redirects before exposing the final status is runtime behavior that still needs a dedicated test.
- Remote availability, content-type correctness, host behavior, rate limiting, content length and body stability remain external dependencies. A successful retrieval at one time is not a guarantee of future availability.

## MoveOut application

Stage 3 supplies a deterministic provenance gate that can be required before later workflows consume image evidence. It does not authorize a visual observation or condition verdict by itself. Any later visual adjudication must consume the frozen evidence binding and an explicit successful provenance result, preserve uncertainty, and remain a separate protocol action. The Stage 3 code contains no prompt call, vision API, visual classification, finding writer, or benchmark selector.

## Implementation recommendations

1. Keep evidence freezing and provenance verification separate; never silently replace a frozen URL or digest.
2. Require `VERIFIED` for workflows that need byte identity. Keep `UNAVAILABLE`, `INVALID_CONTENT`, `DIGEST_MISMATCH`, and `UNSUPPORTED` as non-success states.
3. Prefer immutable/commit-pinned public assets or a future content-addressed storage design. If mutable sources are permitted, expose each verification in history and treat changed bytes as a provenance change.
4. Add a documented domain/redirect policy before production deployment. The current HTTPS syntax checks are not an allowlist or SSRF defense.
5. Keep provenance and semantic visual interpretation separate; a content hash does not establish that an image depicts the claimed room, area, date, or condition.
6. Retain Stage 3 as an undeployed protocol revision until subsequent stages and deployment reviews are complete. The deployed proof address below is disposable and is not a canonical MoveOut deployment.

## Stage 3 hosted proof pointer

Hosted transactions, fixture URLs/digests, receipts, authoritative rereads, exact tested outcomes, environment details and limitations are recorded in [`MOVEOUT_STAGE_3_VERIFICATION.md`](MOVEOUT_STAGE_3_VERIFICATION.md). The disposable StudioNet contract was `0x6Fad38356E9ce08c6464542334B71B84E745D7F2`; no canonical MoveOut contract was deployed.
