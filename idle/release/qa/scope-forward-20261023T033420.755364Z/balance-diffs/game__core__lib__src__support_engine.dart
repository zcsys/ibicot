--- historical/game/core/lib/src/support_engine.dart
+++ current/game/core/lib/src/support_engine.dart
@@ -16,6 +16,7 @@
   /// The caller supplies its independently persisted envelope cursor.
   TransitionResult initializeReceiptCursor(
       GameState state, DateTime persistedCursorUtc) {
+    _requireRules(state);
     if (!state.support.receiptCursorMigrationRequired ||
         state.support.activeSettlementId != null)
       return _reject(state, 'receipt_cursor_migration_not_available');
@@ -38,6 +39,7 @@
     required String sourceId,
     String route = 'briefing',
   }) {
+    _requireRules(state);
     if (!state.daily.initialized || accountDay != state.daily.dayHighWater)
       return _reject(state, 'support_account_day_mismatch');
     if (slot < 0 ||
@@ -87,6 +89,7 @@
   }
 
   TransitionResult useSupportBoost(GameState state, String tokenId) {
+    _requireRules(state);
     final token = _availableToken(state, tokenId);
     if (token == null) return _reject(state, 'support_token_unavailable');
     final after = state.copyWith(
@@ -117,6 +120,7 @@
   /// one immutable transition. Persist the complete result as one commit.
   TransitionResult claimSalvageCache(
       GameState state, String tokenId, String cacheId) {
+    _requireRules(state);
     if (_availableToken(state, tokenId) == null)
       return _reject(state, 'support_token_unavailable');
     final matches = state.support.caches.where((c) => c.id == cacheId);
