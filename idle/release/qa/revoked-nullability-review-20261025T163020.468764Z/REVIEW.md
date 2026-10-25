# Independent nullability amendment review

Approve the exact one-line test-only amendment for scoped Dart reanalysis. The original staged c9 harness has a real analyzer type error: ActiveNotification.id is `int?`, so its unqualified mapping produced `List<int?>` where this helper declares `Future<List<int>>`. Preserve that failed analyzer result; the prior independent method review was explicitly conditional on analysis and did not claim compilation success.

The amendment changes only `.map((item) => item.id)` to `.map((item) => item.id!)` immediately after the existing `ReminderPlanner.ids.contains(item.id)` filter. The production constant contains only integers 77101, 77102 and 77103; a null id cannot pass it. The model's id is final. The projection is therefore valid for exactly those already selected notifications and introduces no new admitted IDs or behavior.

Reversing this single projection reconstructs the exact original c9 staged harness byte for byte. All three Python files, original stage evidence and live 330ab harness remain unchanged. Exact new harness SHA: `de04f52b3c2311b3eb8e1c7fb83fcf7da41256a63a9a3b9f0ca4f732e8667eb4`. Exact patch SHA: `eb58a4d47226952af8e6b5f92b826162e96991f1bf9b957bf8c28adcd593da77`.

The prior independent 43-method/42-check protocol review remains applicable through this exact bridge; repeating the unchanged Python behavior suite would add no evidence for this Dart type correction. Scoped Dart analysis and an actual fresh native preparation/recovery pair remain required. No device/Flutter call, live edit, status acceptance, semantics bypass or old-failure relabel occurred in this review.
