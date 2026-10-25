# Independent current five-export review

**The five local exports reproduce their recorded identities and packaged-content inventories.** Candidate `3b00cc8f71222f35b60f18ee83a8bb3ba71e39aa5364222dbeb7f6d2a5c45c59` is bound to 1,190 unchanged frozen source files. No archive corruption, source/lock mismatch, omitted Material icon notice or missing checked icon glyph was found. Both public-target release artifacts are unsigned. This is bounded export/inclusion evidence, not final distribution readiness.

## Actual bytes and source binding

| Export | Bytes | Reproduced SHA-256 |
|---|---:|---|
| iOS simulator debug ZIP | 63,872,985 | `53c296abed7f7906a73a11e028852133b6860e449599f4c3dd5763099a62aa07` |
| Android debug APK | 191,034,607 | `b275ae07dcf76fcf7108c64a02dc688295c0e50371f888ea15a8cdc0ec2cec4e` |
| Internal macOS debug ZIP | 47,080,920 | `87b6c124aa42c3b57a23b52e2b34f33aad31421b42fc5d321acb949d70f24765` |
| Unsigned iOS device release ZIP | 12,780,759 | `d0dba4a1f8f1a2119fab041b774286fc6d7fc28ca843682873b6599e6c3b7c3d` |
| Unsigned Android release AAB | 64,920,096 | `3f460a1965511e77bfecbd402c83f676bc31a8a72bd20896cd08850484f1c572` |

All five archives pass full member decompression/CRC, unique-name and safe-path checks. Every one of the author's 211 selected plist/privacy/property members was read independently from the real archives, parsed, and matched to both its declared digest and archived raw bytes. The recorded build reports have successful exports; the debug report records 28/28 host checks. This reviewer did not rerun that host suite.

The source fingerprint is independently reconstructed. All captured inputs in the debug workspace match the frozen source. The release workspace differs only in SDK-generated `GeneratedPluginRegistrant.java`: removal of the integration-test plugin registration. The exact diff is preserved. The live source still matches its frozen version. All 18 dependency-lock comparisons across the two workspaces pass. This is a comparison of captured source inputs, not a claim that build-output directories contain no generated files.

`codesign` on the actual extracted release Runner reports no signature; the release archive has no root signature/provision. `jarsigner` on the actual AAB reports it unsigned, with no JAR signature members. Neither is a signed store-distribution artifact.

## Packaged platform/privacy declarations

Fresh `aapt2` decoding of the debug APK and `bundletool` decoding of the release AAB reproduce the author's exact outputs. The AAB identifies `dev.tideglass.game`, version `0.1.0`/1, minimum API29 and **target API36**. The official Google policy currently requires API36 or higher for new mobile submissions from August31,2026; root's target-level claim is supported by the exact manifest. The separately recorded emulator is API35/Android15 and establishes no API36 runtime qualification. [Google Play target API requirements](https://support.google.com/googleplay/android-developer/answer/11926878?hl=en-EN)

The Android AAB contains 12 permission declarations, including Internet, notifications, vibration, network state, advertising ID/AdServices, billing, wake lock and foreground service. It includes `MobileAdsInitProvider`, ad components and billing activities. Packaged properties report Google ads25.4.0, billing8.0.0, ads identifier18.0.0 and measurement base/SDK API20.1.2. These are actual included SDK components, even though the recorded build commands supply no provider-enabling Dart definitions and the default source configuration disables service/ads/commerce routes.

The actual iOS device app declares iOS16 minimum and both phone/tablet families. Eleven packaged privacy manifests are retained separately, including the app's exact SystemBootTime35F9.1 declaration, Flutter, notifications, Google Mobile Ads13.11.0 and UMP3.1.0. Google Mobile Ads' manifest declares multiple advertising/analytics/diagnostic categories, including tracking-linked DeviceID; UMP declares its own categories. The inventory is not an Xcode aggregate privacy report and these declarations do not establish actual collection, absence of traffic, consent correctness or approved store disclosures.

An unusual UMP `MinimumOSVersion=100.0` also appears in the embedded stub's Mach-O `minos`. Follow-up resolved its local meaning: the cached resolved UMP package contains a real static archive; the exported Runner defines UMP consent and GADMobileAds symbols and has no dynamic dependency on those two resource frameworks. The embedded UMP binary has zero text/symbols. This supports classification as a resource stub for statically linked SDK code, consistent with Apple's static-framework resource model. It does not establish that Tideglass requires iOS100, that a mock provider was substituted, or that store validation will accept this metadata. Preserve the observation for actual distribution validation; no source repair follows from this evidence alone. [Apple static-framework documentation](https://developer.apple.com/documentation/xcode/creating-a-static-framework)

## Packaged fonts and notices

Material Icons is the only `.otf`/`.ttf` font found in these archives. Every export includes the exact 18,531-byte explicit notice, SHA `be698262aecd042c0de6f886cc0af622f8def446462026992cc530275d8a9e74`. Source startup registers it through the existing Licenses UI; the earlier independent UI review establishes that path. This inspection proves inclusion, not a new native UI rendering or legal approval.

The three debug fonts equal the pinned SDK font: 1,645,184 bytes, 8,661 glyphs. Both release artifacts share the same 6,736-byte subset, SHA `fbf926ea08851c5e974cb4ec249bc47091ca053b01fc0fd92bb3f03fe79ff96a`: 44 glyphs/43 mapped Unicode codepoints. Independent OpenType table/cmap inspection confirms subset membership and retained Focus, Survey, contract, completion and water-navigation glyphs. It does not claim full-font equality or screen-level rendering qualification for the subset.

All five `NOTICES.Z` payloads match and decompress to the recorded notices. They mention Apache but do **not** contain the specific “Material Icons” label. The explicit exact license asset and registered Licenses entry supply that attribution; this report does not invent its presence in generated NOTICES.

## Original scope and remaining limits

Original M1-02 concerns the headless economy and event ordering; these exports neither reopen nor extend that accepted criterion. Original M7-03 requires signing, install/update, responsive layouts, licensed assets and store-visible flows in final distribution builds. Original M7-05 requires media/help/credits/release assets to describe the shipped game and offers. Local unsigned packaging, current manifest inventory and bundled notices satisfy only component evidence; their original dependencies, final signing/distribution, native behavior, approved disclosures and current media remain separate. No package or scope status is changed here.

This review made no Flutter, simulator, emulator, UI or device call. It makes no actual network-traffic or store-approval claim. The independent observer repair's Android private-storage limitation remains explicit: storage is unavailable and socket-only results stay partial. Current native/runtime/observer and media work proceeds separately; this report does not borrow completion from it.

`verification.json` records 3,262 successful primary source/export checks; the nine focused SDK-classification checks are separate. Exact command logs, artifact results, privacy plists, font inventory, source/lock comparison, inspected-file pins and the final unchanged-input check are preserved in this folder. Ownership was restricted to this new QA folder.
