--- historical/game/core/lib/src/daily_engine.dart
+++ current/game/core/lib/src/daily_engine.dart
@@ -90,6 +90,7 @@
     int? utcOffsetMinutes,
     List<String> availableDiscoveryKinds = const [],
   }) {
+    _requireRules(state);
     final previous = state.daily;
     if (previous.initialized &&
         ((accountSeed != null && accountSeed != previous.accountSeed) ||
@@ -176,6 +177,7 @@
   }
 
   TransitionResult rerollContract(GameState state, String contractId) {
+    _requireRules(state);
     final matches = state.daily.contracts.where((c) => c.id == contractId);
     if (matches.isEmpty) return _reject(state, 'contract_not_retained');
     final contract = matches.single;
@@ -197,6 +199,7 @@
 
   TransitionResult claimContract(GameState state, String contractId,
       {DailyContractAlternative? alternative}) {
+    _requireRules(state);
     final matches = state.daily.contracts.where((c) => c.id == contractId);
     if (matches.isEmpty) return _reject(state, 'contract_not_retained');
     final contract = matches.single;
@@ -238,6 +241,7 @@
   /// Repeated operation delivery cannot count the same discovery twice.
   TransitionResult recordDiscovery(GameState state, String kind,
       {BigInt? operationSequence, String? operationId, String? contentId}) {
+    _requireRules(state);
     if (!{'calibration', 'archive', 'challenge'}.contains(kind))
       return _reject(state, 'invalid_discovery');
     if (operationId != null)
@@ -271,6 +275,7 @@
 
   TransitionResult completeCalibration(GameState state, String patternId,
       {BigInt? operationSequence, String? operationId}) {
+    _requireRules(state);
     if (!RegExp(r'^calibration\.(0[1-9]|1[0-2])$').hasMatch(patternId))
       return _reject(state, 'unknown_calibration');
     final sequence = operationSequence ?? state.nextDiscoverySequence;
@@ -290,6 +295,7 @@
   }
 
   TransitionResult buyPlanSlot(GameState state) {
+    _requireRules(state);
     if (state.charts < BigInt.from(10))
       return _reject(state, 'automation_requires_10_charts');
     if (state.extraPlanSlots >= 5)
@@ -306,6 +312,7 @@
   }
 
   TransitionResult saveAutomationPlan(GameState state, AutomationPlan plan) {
+    _requireRules(state);
     if (state.charts < BigInt.from(10))
       return _reject(state, 'automation_requires_10_charts');
     if (plan.autoResetEnabled && state.charts < BigInt.from(100))
@@ -327,6 +334,7 @@
   }
 
   TransitionResult selectAutomationPlan(GameState state, String planId) {
+    _requireRules(state);
     if (!state.automationPlans.any((plan) => plan.id == planId))
       return _reject(state, 'unknown_plan');
     if (state.selectedAutomationPlanId == planId)
