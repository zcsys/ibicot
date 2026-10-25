--- historical/game/core/lib/src/state.dart
+++ current/game/core/lib/src/state.dart
@@ -9,6 +9,8 @@
 /// Immutable production state. Wallet/lifetime/Charts are never doubles.
 /// Native persistence wraps this payload in the separate save envelope.
 class GameState {
+  /// Selected by a compiled, trusted rules registry, never inferred from a save.
+  final String rulesVersion;
   final List<int> counts;
   final BigInt walletMicros;
   final BigInt lifetimeMicros;
@@ -43,6 +45,7 @@
       automationPlans.firstWhere((plan) => plan.id == selectedAutomationPlanId);
 
   GameState({
+    this.rulesVersion = economyVersion,
     List<int> counts = const [1, 0, 0, 0, 0],
     BigInt? walletMicros,
     BigInt? lifetimeMicros,
@@ -88,9 +91,13 @@
     validate();
   }
 
-  factory GameState.initial() => GameState();
+  factory GameState.initial({String rulesVersion = economyVersion}) =>
+      GameState(rulesVersion: rulesVersion);
 
   void validate() {
+    if (!RegExp(r'^tideglass-economy-\d+\.\d+\.\d+$').hasMatch(rulesVersion)) {
+      throw ArgumentError('Invalid economic rules identity');
+    }
     if (counts.length != 5 ||
         counts.any((count) => count < 0) ||
         counts[0] < 1) {
@@ -177,7 +184,8 @@
   }
 
   GameState copyWith(
-          {List<int>? counts,
+          {String? rulesVersion,
+          List<int>? counts,
           BigInt? walletMicros,
           BigInt? lifetimeMicros,
           BigInt? charts,
@@ -202,6 +210,7 @@
           List<AutomationPlan>? automationPlans,
           String? selectedAutomationPlanId}) =>
       GameState(
+          rulesVersion: rulesVersion ?? this.rulesVersion,
           counts: counts ?? this.counts,
           walletMicros: walletMicros ?? this.walletMicros,
           lifetimeMicros: lifetimeMicros ?? this.lifetimeMicros,
@@ -235,7 +244,7 @@
 
   Map<String, dynamic> toJson() => {
         'schema_version': stateSchemaVersion,
-        'economic_version': economyVersion,
+        'economic_version': rulesVersion,
         'event_order_version': eventOrderVersion,
         'counts': counts,
         'wallet_micros': walletMicros.toString(),
@@ -264,7 +273,10 @@
         'selected_automation_plan_id': selectedAutomationPlanId,
       };
 
-  factory GameState.fromJson(Map<String, dynamic> json) {
+  /// The caller must resolve this exact version from its compiled registry
+  /// before decoding. The default continues to reject every non-v1 economy.
+  factory GameState.fromJson(Map<String, dynamic> json,
+      {String expectedEconomicVersion = economyVersion}) {
     final legacy = json['schema_version'] == 1;
     final preSupport = legacy || json['schema_version'] == 2;
     final preReceipts = preSupport || json['schema_version'] == 3;
@@ -304,7 +316,7 @@
       throw FormatException('Unexpected or missing state fields');
     }
     if ((!preReceipts && json['schema_version'] != stateSchemaVersion) ||
-        json['economic_version'] != economyVersion ||
+        json['economic_version'] != expectedEconomicVersion ||
         json['event_order_version'] !=
             (legacy
                 ? 1
@@ -330,6 +342,7 @@
       throw FormatException('Invalid state primitive field type');
     }
     return GameState(
+        rulesVersion: expectedEconomicVersion,
         counts: List<int>.from(json['counts'] as List),
         walletMicros: integer('wallet_micros'),
         lifetimeMicros: integer('lifetime_micros'),
