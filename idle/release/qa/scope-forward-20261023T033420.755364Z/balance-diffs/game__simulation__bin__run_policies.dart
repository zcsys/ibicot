--- historical/game/simulation/bin/run_policies.dart
+++ current/game/simulation/bin/run_policies.dart
@@ -151,8 +151,8 @@
             'limitations': [
               'Reproducible policies are not a proof of optimal play or measured retention.',
               'Chapter timestamps are upper bounds at evaluation boundaries, not sub-event completion times.',
-              'The none policy uses no Focus and therefore deliberately does not complete the chapter requiring three calibrations.',
-              'The minimal policy completes the three required accessible calibrations; it is not zero-Focus.',
+              'The none policy uses no Focus or Support; all campaign goals remain eligible.',
+              'The legacy-named requiredCalibrationsOnly policy voluntarily completes three accessible calibrations; it is not zero-Focus and they are no longer required.',
               'Ad-route receipts are synthetic deterministic fixtures of successful delivery, not provider verification or observed fill. Their only purpose is economic route parity.',
               'Dossier automation and best-payback choices are selected without human learning time.',
               'Only retained ready daily contracts can be claimed; allReady does not manufacture three completions per day.',
