--- historical/game/core/lib/src/engine.dart
+++ current/game/core/lib/src/engine.dart
@@ -19,6 +19,39 @@
 /// network, wall-clock or store operations occur in this package.
 class TideglassEngine {
   const TideglassEngine();
+
+  /// A compiled implementation identity. Remote values cannot select code.
+  String get rulesVersion => economyVersion;
+
+  void _requireRules(GameState state) {
+    if (state.rulesVersion != rulesVersion) {
+      throw StateError('State and selected economic rules differ');
+    }
+  }
+
+  /// A compiled compatibility edge may adopt an already settled state without
+  /// changing its currency basis, numeric residue or frozen daily objectives.
+  /// Persistence must first settle the old rules through its authorized UTC
+  /// boundary and atomically commit this state with that cursor and new pin.
+  /// This method alone is not a durable economic transition.
+  TransitionResult adoptCompatibleState(GameState state,
+      {required String sourceRulesVersion}) {
+    if (state.rulesVersion != sourceRulesVersion ||
+        sourceRulesVersion == rulesVersion) {
+      return _reject(state, 'economic_transition_source_mismatch');
+    }
+    if (state.support.activeSettlementId != null) {
+      return _reject(state, 'economic_transition_requires_closed_settlement');
+    }
+    final after = state.copyWith(
+        rulesVersion: rulesVersion, revision: state.revision + 1);
+    return TransitionResult(after, events: [
+      _event(after, 'economic_rules_adopted', details: {
+        'from': sourceRulesVersion,
+        'to': rulesVersion,
+      })
+    ]);
+  }
 
   static const producerNames = [
     'Spark Skiff',
@@ -90,6 +123,7 @@
   }
 
   bool isUnlocked(GameState state, int tierIndex) {
+    _requireRules(state);
     _tier(tierIndex);
     return tierIndex == 0 || state.counts[tierIndex - 1] >= 10;
   }
@@ -109,6 +143,7 @@
   }
 
   Fixed synergyMultiplier(GameState state, int tierIndex) {
+    _requireRules(state);
     _tier(tierIndex);
     if (state.charts < BigInt.from(25) || tierIndex < 3) return Fixed.one;
     final x1 = _synergyCountLog(state.counts[0]);
@@ -126,6 +161,7 @@
   /// Unboosted producer rate. Focus is applied by the timeline, not hidden in
   /// this value; forecasts explicitly state whether bonuses are ignored.
   Fixed producerOutputPerSecond(GameState state, int tierIndex) {
+    _requireRules(state);
     _tier(tierIndex);
     final direct = BigInt.from(state.counts[tierIndex]) *
         BigInt.from(20).pow(tierIndex) *
@@ -135,6 +171,7 @@
   }
 
   Fixed outputPerSecond(GameState state) {
+    _requireRules(state);
     // Scenario subclasses override producer rules and may read other state.
     // Only this exact baseline type has the complete key declared below.
     if (runtimeType == TideglassEngine && state.charts.bitLength <= 4096) {
@@ -180,12 +217,14 @@
   }
 
   BigInt prestigeAward(GameState state) {
+    _requireRules(state);
     if (state.lifetimeMicros < firstPrestigeMicros) return BigInt.zero;
     final difference = prestigeEntitlement(state.lifetimeMicros) - state.charts;
     return difference > BigInt.zero ? difference : BigInt.zero;
   }
 
   BigInt nextChartLifetimeMicros(GameState state) {
+    _requireRules(state);
     return lifetimeForCharts(state.charts + BigInt.one);
   }
 
@@ -199,11 +238,13 @@
   }
 
   int nextMilestoneQuantity(GameState state, int tierIndex) {
+    _requireRules(state);
     _tier(tierIndex);
     return 25 - state.counts[tierIndex] % 25;
   }
 
   int maximumAffordable(GameState state, int tierIndex) {
+    _requireRules(state);
     _tier(tierIndex);
     if (!isUnlocked(state, tierIndex) ||
         priceMicros(tierIndex, state.counts[tierIndex]) > state.walletMicros)
@@ -246,12 +287,13 @@
   CoreEvent _event(GameState after, String kind,
           {int index = 0, Map<String, dynamic> details = const {}}) =>
       CoreEvent(
-          id: '$economyVersion:${after.revision}:$index:$kind',
+          id: '$rulesVersion:${after.revision}:$index:$kind',
           kind: kind,
           elapsedMicros: after.elapsedMicros,
           details: details);
 
   TransitionResult buy(GameState state, int tierIndex, int quantity) {
+    _requireRules(state);
     _tier(tierIndex);
     if (quantity <= 0) return _reject(state, 'quantity_must_be_positive');
     if (!isUnlocked(state, tierIndex)) return _reject(state, 'producer_locked');
@@ -279,6 +321,7 @@
   }
 
   TransitionResult buyMax(GameState state, int tierIndex) {
+    _requireRules(state);
     final amount = maximumAffordable(state, tierIndex);
     return amount == 0
         ? _reject(state, 'no_affordable_unlocked_purchase')
@@ -286,6 +329,7 @@
   }
 
   TransitionResult rechart(GameState state) {
+    _requireRules(state);
     final award = prestigeAward(state);
     if (award == BigInt.zero) return _reject(state, 'no_new_eligible_charts');
     final after = state.copyWith(
@@ -301,6 +345,7 @@
   }
 
   TransitionResult setAutoBuy(GameState state, bool enabled) {
+    _requireRules(state);
     if (enabled && state.charts < BigInt.from(10))
       return _reject(state, 'autobuy_requires_10_charts');
     if (state.autoBuyEnabled == enabled)
@@ -313,6 +358,7 @@
   }
 
   TransitionResult activateFocus(GameState state, {int charges = 1}) {
+    _requireRules(state);
     if (charges <= 0 || charges > state.focusCharges)
       return _reject(state, 'insufficient_focus');
     final after = state.copyWith(
@@ -326,6 +372,7 @@
   }
 
   TransitionResult collectSurveys(GameState state) {
+    _requireRules(state);
     if (state.completedSurveys == 0)
       return _reject(state, 'no_completed_surveys');
     final gained = BigInt.from(state.completedSurveys * 10);
@@ -377,6 +424,7 @@
     String? offlineSettlementId,
     bool finalizeOfflineSettlement = true,
   }) {
+    _requireRules(initial);
     if (offlineSettlementId != null)
       return _reject(
           initial,
@@ -422,6 +470,7 @@
     BigInt? legacyThroughUtc,
     bool finalizeOfflineSettlement = true,
   }) {
+    _requireRules(initial);
     if (duration.isNegative || offlineElapsedBefore.isNegative)
       return _reject(initial, 'negative_elapsed_time');
     if (maximumEvents <= 0)
