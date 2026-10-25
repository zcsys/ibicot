# Native artifact inventory — independent client review

Scope: M5-03 / S39 collector integrity and packaged declarations. This is a different-author review of the lead's collector. No Flutter, build, install, simulator, device, ad SDK initialization, traffic capture or publication was performed. Author source is unchanged by this reviewer.

**Finding: repair the collection-time input stability boundary before qualifying the collector for the next current candidate.** Normal historical recollection is exact, but three synthetic in-flight mutations are accepted and can break the published source/artifact binding.

## Frozen source and reproduced controls

| Input | SHA-256 |
|---|---|
| `release/native-privacy/inspect_artifacts.py` | `1ea9422501ef96219391d2520d59538c29a3f6c113b78f2da68ad323ad935b55` |
| `release/native-privacy/test_artifact_inventory.py` | `b10f353624658c53d4388691ebcf439d34912b004403e1928220980b99d98500` |
| `.tooling/bundletool/download.json` | `0133074289d48c76b4b4a0ed7f26970268fea090493b4f0e4facc8bf433f1d82` |

`before.json`, `after.json` and `source/` preserve five inspected inputs, including the author's handoff and verification. All five remained unchanged during this review's original runs.

- Reproduced the 11 author tests: all pass (`author-tests.log`).
- Reran the actual read-only collector over historical candidate `152805bf9e269f49d14486286656ac0174a808384d10e6623533a4f92690dc11`: all five exports collected (`reproduction.json`, `historical-rerun.log`).
- The independent `historical-rerun/inventory.json` is **byte-for-byte identical** to the author's inventory, SHA-256 `0c7e7ea24f4c9c4e7586a0a079ffaffa3dc3faa4d467c7fa1fbb620399e19486`.
- Independently rehashed all **205** selected raw metadata members: every recorded length and SHA matches (`historical-comparison.json`). This covers debug iOS/Android/macOS and release iOS/Android.
- Independently fetched the official [Google bundletool 1.18.3 release API](https://api.github.com/repos/google/bundletool/releases/tags/1.18.3). Its asset digest, size and download URL match the local jar and `download.json`: SHA `a099cfa1543f55593bc2ed16a70a7c67fe54b1747bb7301f37fdfd6d91028e29`, 32,520,401 bytes. Raw response and comparison are retained in `vendor-release.json` and `vendor-provenance.json`. TLS verification was not bypassed.

The eight independent synthetic probes produce **five pass, three fail** (`reviewer-tests.log`). Positive controls establish that a normal five-export fixture succeeds with every nonapproval flag false, while preexisting artifact drift, a different candidate report, a truthy-string source-verification field and a duplicate platform/mode report reject.

## INV001 — Published inputs can drift during collection (P2)

The collector hashes source pins and each artifact before decoding, then reads current paths again later for result metadata, without validating that the full input set remained stable before publication. Actual decoder calls create a nonzero interval in which an input can change. Three deterministic synthetic callbacks exercise that boundary; none modifies a historical artifact or live production file.

1. **Artifact changes after validation/member decoding.** The probe changes the first reviewer-owned artifact after `selected_members` has read the original bytes. The collector completes and publishes `artifact_sha256` for the changed bytes even though its own referenced successful build report contains the original hash, while members still describe the original archive. `accepted-artifact-drift.json` preserves the contradictory hashes. The initial preexisting-drift negative control does reject, so this is specifically an intra-run gap.
2. **Candidate source changes during manifest decoding.** A fake decoder callback changes one reviewer-owned pinned source after the initial validation loop. Collection still publishes the original candidate fingerprint. `accepted-source-drift.json` records the final source hash versus the pinned source hash. No final source stability check runs.
3. **Collector source changes after its raw copy is preserved.** The probe points `__file__` to a reviewer-owned copy and changes that copy during decoding. The published `collector_sha256` then identifies the later bytes, while preserved `collector.py` still contains the original implementation. `accepted-collector-drift.json` records the mismatch. This never writes the live collector file.

These are one related evidence-integrity defect, not three separate runtime/privacy violations. Preserve the input identities at entry, decode stable copies where practical, and reject changed candidate/report/artifact/tool inputs before writing the inventory; bind the collector hash to the exact preserved source. The existing positive and negative probes should continue to pass. A simple end check closes the demonstrated lasting-mutation cases; an immutable snapshot is stronger when claiming resistance to mutation-and-restore races.

## Other reviewed boundaries

- `safe_relative` rejects absolute paths, parent traversal and backslashes; archive entries are read as data, never extracted to their supplied path. Selected raw data uses generated member filenames. Duplicate archive names, selected-member/total limits and corrupt/non-dictionary plists reject in the reproduced author tests.
- Artifact identity is tied to the supplied successful build reports and their exact hash/size, with source fingerprint and candidate-directory checks. This is evidence collection, not an independent rebuild or cryptographic authentication of whoever authored the reports.
- AAB declarations use actual local Java/bundletool; APK declarations use actual local aapt2. The observed tool hashes match the historical run. The collector records tool hashes and a Java path, but does not itself enforce the external vendor download record; this review independently verified the supplied bundletool binary. A future run must retain that provenance rather than infer it from an arbitrary tool path.
- Apple results are individual packaged Info/privacy plists, not an official Xcode aggregate privacy report. Raw bytes preserve types even where JSON serialization is a presentation conversion.
- The inventory correctly leaves `runtime_traffic_observed`, `store_disclosure_approved` and `release_acceptance` false. Permissions, SDK versions and packaged declarations establish presence and declared configuration, not collection/noncollection, consent behavior or provider operation.

## Decision and remaining work

Hold collector-integrity qualification pending INV001 repair and replay of the same probes. The successful historical run remains useful tooling evidence and is **not current native proof**. A new current-candidate inventory, process-attributed native traffic/storage evidence, actual provider/consent validation and final disclosures/physical checks remain separate outstanding obligations. This review edits no program, scope or acceptance status.
