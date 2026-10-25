# Font notice integration

Preserved the exact pinned SDK MaterialIcons notice as a bundled asset, added Google attribution and an idempotent startup LicenseRegistry entry, and recorded source/notice hashes in source/art/ui/font-manifest.json. Existing Credits → Open software licenses is the player route. The manifest distinguishes OS typography and host-only Roboto, and records the SDK/upstream license-label discrepancy without claiming relicensing.

Two actual Flutter tests pass: loaded packaged notice paragraphs match the supplied SDK notice; repeated registration yields one Google Material icons entry in the global registry. Scoped analysis passes with no warnings; six promoted files and dependency lock are unchanged. Compiled-native inclusion and independent UI/license review remain pending. No asset/package/release approval was added.
