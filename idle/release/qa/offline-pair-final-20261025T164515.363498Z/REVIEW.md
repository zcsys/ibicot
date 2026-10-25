# Actual Android offline guest pair — bounded outcome review

**Recommendation:** accept the executed Android API 35 airplane-mode guest start/purchase/save/new-process reload as supported evidence. Keep original **S02 not_verified**: actual isolated-network execution on iOS is still unproven. This review changes no original criterion, package dependency or canonical status and does not establish a finished v1.

## Exact execution and result

| Evidence | Outcome |
|---|---|
| `integration-android-offline-20261025T163852.724871Z/verification.json`, SHA b77fc2974c7e5a0c5606e80118cc6ebaa031e275b14ef0fce3bc9bd0b6435e5d | Strict start pass, PID 9280, 105 actual app socket samples |
| `integration-android-offline-20261025T164119.025808Z/verification.json`, SHA 9c44fc5645005e16de0988d51d3ee2e70479602f4028a33191923ed6b07730c5 | Strict reload pass, distinct PID 9798, 66 actual app socket samples |
| `offline-operator-20261025T163838.795705Z/checkpoint.json`, SHA d7cb2c58a36f6e519f6ff5ad62040b1e6042dbafebb2d6905cc0b7d926648eb1 | Raw operator, both terminal reports and immutable listener prefixes sealed; listener stopped normally |

The same unique profile, nonce, local endpoint and guest save directory bind the two runs. The start asserts an absent guest directory, uses the real bootstrap, waits 35 real seconds while repeatedly checking a failed app socket and resumed lifecycle, then taps the actual `buy-0` control. Counts change from one to two Spark Skiffs. Lifetime earnings minus wallet is exactly 33,600,000 micros, the actual second Skiff price. Native elapsed time is 38,187 ms. The save succeeds and the native checkpoint is flushed and exported.

Reload uses the exact successful predecessor report, unchanged checkpoint bytes (a5591758b150e5ddf8b70a905c45158a15c26450534cfeac9c3a9d3e68329d53), same isolated save path and a different OS process. The restored two-Skiff fleet and nondecreasing saved wallet/lifetime are asserted in the real client; legitimate elapsed earnings mean the numerical balances are not expected to remain byte-identical. The captured client image visibly shows two Skiffs at 2 R/s.

## Network and operator evidence

| Stage | Airplane / raw Wi-Fi / data | Actual default network |
|---|---|---|
| Before start | 0 / 1 / 1 | 106 |
| Offline start and reload operation checkpoints | 1 / 3 / 1 | none |
| After restored UI and app reconnection | 0 / 1 / 1 | 108 |

I viewed the actual Quick Settings images: Airplane Off with network available; Airplane On with Internet in airplane mode and Bluetooth Off; and restored Airplane Off/Bluetooth On. Grounded tap coordinates fall inside the observed control bounds, with matching pre-image/hierarchy hashes. Current Tideglass icon actions are bound to their observed launcher nodes. Recorded post-return receipts use screenshots/activity only; no new UiAutomation session overlaps either return through native completion.

Actual failed `10.0.2.2:49774` challenges bracket bootstrap, sustained earnings, purchase, save and reload checks. Independently bound host listener health surrounds the app failures, using measured host/app clock offset rather than assuming synchronized wall clocks. The final reconnect probes succeed and the raw radio settings equal the original baseline. An active default network is restored; a new default-network ID is expected. This is local endpoint plus actual Android OS network-state qualification, not an Internet test, a production-traffic absence claim, paid-provider validation, or physical-device evidence.

## Independent verification and limits

`review.py` reproduces the archived pure qualification on both real payloads, the strict native/framework log checks, 140 assertions and 108 file pins. It rehashes native saves, checkpoint, report, source archives, raw UI artifacts, both listener prefixes and the completed journal. Five bounded synthetic mutations are rejected (PID inconsistency, changed checkpoint, endpoint reachable at bootstrap, missing listener health evidence, and no restored successful reachability); late framework failure remains rejected. These are wrapper checks on copies, not additional native executions or a repeated broad matrix.

Both runs used the reviewed unchanged harness 90dbf5a3…, helper f726ab53… and runner ec56e668… against frozen candidate 3b00cc8f…. Production and harness differences are empty in the reports. QA originally authored the staged offline instrumentation/helper; root separately reviewed and reproduced it before native execution. This packet independently audits the native verifier's execution and raw operator outcomes. It does not present the original author as an independent approver of that instrumentation.

The first failed start (db58df8f…, unrecognized raw Wi-Fi value 3) and second failed start (5b1e4511…, operator did not resume the app within the unchanged deadline) remain failed and unchanged. Neither was used as this pair's predecessor.

## Exact original S02 disposition

S02 asks for “Guest offline core, optional cloud, English externalized text and pseudolocalization,” verified by “Airplane-mode guest flow and localized-layout tests; fresh network services are separate dependencies.” The existing sealed scope audit's localization/guest/cloud-separation proofs remain applicable to unchanged production inputs. This addendum replaces only its statement that actual network-disabled guest execution had not occurred: the Android path now has direct evidence.

The roadmap release contract covers iOS and Android. This Android pair cannot establish actual iOS network isolation. Therefore the complete cross-target scope criterion remains unverified; the exact remaining local/platform qualification is isolated-network iOS guest operation, not an inferred code defect or a new requirement for fresh cloud service availability. No macOS host networking was changed and no iOS offline result is claimed. Broader physical, provider, human and store gates remain in their original packages.
