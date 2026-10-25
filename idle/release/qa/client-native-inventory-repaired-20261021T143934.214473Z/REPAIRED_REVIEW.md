# INV001 repair — independent collector review

Scope: M5-03 / S39 evidence-collection integrity. **The demonstrated INV001 lasting-mutation failures are repaired.** This recommendation concerns the collector only; no program acceptance or production source was edited by the reviewer.

Reviewed collector SHA-256: `b9a8e1f993324efd88ceec60f4c0f035141c1c6574020326a351619854f0643b`. Exact source copies, five before/after pins and the reviewed diff are retained in `source/`, `before.json`, `after.json` and `reviewed-repair.diff`. All inputs remained unchanged during these review runs.

| Independent replay | Result | Evidence |
|---|---:|---|
| Original author parser/source tests | 11 / 11 pass | `author.log` |
| Original eight reviewer probes, unchanged | 8 / 8 pass | `unchanged-review.log` |
| Added publication/drift boundary tests | 9 / 9 pass | `additional-review.log`, `review_repair.py` |
| Actual historical five-export collection | Pass | `historical-rerun.log`, `historical-rerun/inventory.json` |

`runs.json` preserves commands and return codes. Original failure evidence remains unchanged under `release/qa/client-native-inventory-20261021T143056.713149Z`.

## Reviewed repair

The collector now pins the bytes of the candidate manifest, candidate sources, collector implementation, build reports, bundletool and aapt2 before using those inputs. It pins each artifact before decoding, compares the pinned hash against its successful build report, and publishes those original identities rather than replacing them with later reads. It rehashes all pinned paths before constructing and writing the final inventory. The saved collector file uses the same captured bytes as `collector_sha256`.

The unchanged reviewer probes now reject the original artifact, candidate-source and collector mutations. New negative tests change the candidate manifest, debug report, release report, bundletool, aapt2, an already read artifact, and collector source during a decoder callback; another removes a pinned source. Every case raises the explicit drift error and leaves **no `inventory.json`**. Partial raw diagnostic output is allowed to remain; it is not a published success result. Each negative also checks that the preserved collector copy still has its original exact hash. The positive test uses separate bundletool/aapt bytes, verifies their distinct published hashes, verifies the saved collector/report/artifact hashes, and retains false runtime/release approval flags.

## Historical positive control

The actual read-only rerun exercises the new pin/rehash path with the real preserved exports and local Java/bundletool/aapt2 decoder commands. No Flutter, native build, device/simulator, installation, SDK initialization, network traffic observation or publication command was run.

All five artifact records and all tool records are exactly equal to the prior historical inventory. Its only changed top-level field is `collector_sha256`, as expected for this repair; that value exactly matches the preserved `collector.py`. All **205** selected raw member hashes and lengths were independently rechecked. `historical-comparison.json` records the comparison. The bundletool vendor digest/size/URL verification from the original review remains applicable because the tool and download-record pins are unchanged; this replay did not repeat that network lookup.

## Recommendation and remaining limit

Close INV001 for the demonstrated persistent input changes and use this repaired collector for the next current-candidate inventory under the existing frozen-input workflow. Before/after hashing is not an atomic snapshot: a cooperating or adversarial writer that changes bytes and restores them before the final check can evade detection, and an input may change again after its final check. The collector does not claim resistance to that class of race. Stronger claims would require decoding immutable captured artifacts/tool inputs or a stronger isolation protocol. Java is recorded by path, and this review does not qualify an entirely hermetic host toolchain.

Historical candidate `152805bf9e269f49d14486286656ac0174a808384d10e6623533a4f92690dc11` remains **historical tooling evidence only**. It is not current native proof. Packaged SDK/permission/plist declarations are not runtime data-behavior or consent approval, and individual Apple plists are not an official aggregate Xcode privacy report. The current-candidate run, attributed traffic/storage evidence, actual provider/physical validation and final disclosures remain separate work. No scope or approval status changed in this review.
