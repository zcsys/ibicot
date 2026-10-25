# Independent review of the future study build gate

The lead inspected the actual host-gate control flow and author regressions, then independently reproduced all 23 native-tooling tests and 30 study tests on unchanged source. The failing-study regression executes the real build entry point with an actual failing Python subprocess. The report records a failed study gate and no native export is invoked. The capture regression changes the source fixture after freezing and proves the captured bytes remain immutable; sibling participant exports and study documents are absent.

The bounded `release/study/fixtures` directory is included in future snapshots. Study discovery is explicit alongside the existing native integrity gate, so a study failure prevents exports. Existing frozen candidate 152 and its evidence remain unchanged. These synthetic fixtures establish no actual study enrollment or measured outcome.

A pre-existing ResourceWarning reports that the build entry point relies on object cleanup for its candidate-lock file on early return. It did not change test outcomes or leave the subprocess lock held; explicit structured close would improve the tooling but is not a study-gate defect. No product release criterion is accepted by this narrow review.
