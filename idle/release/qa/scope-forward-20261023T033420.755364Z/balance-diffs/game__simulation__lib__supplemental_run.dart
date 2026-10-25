--- historical/game/simulation/lib/supplemental_run.dart
+++ current/game/simulation/lib/supplemental_run.dart
@@ -388,8 +388,8 @@
     final beforeSurveys = main.surveyNotes;
     _main(engine.collectSurveys(main));
     surveyNotesEarned += main.surveyNotes - beforeSurveys;
-    // Three accessible completions are mandatory chapter content; the minimal
-    // policy stops there, so it is explicitly not a zero-Focus experiment.
+    // The legacy minimal policy voluntarily stops after three accessible
+    // completions. They are optional; this is not a zero-Focus experiment.
     while (bonus != BonusPolicy.none &&
         main.focusCharges > 0 &&
         (bonus != BonusPolicy.requiredCalibrationsOnly ||
