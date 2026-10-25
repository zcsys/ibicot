import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tideglass/app.dart';
import 'package:tideglass/bootstrap.dart';
import 'bootstrap_test.dart' show settleIo;

/// Repeated under real compile-time deployment definitions by the author gate.
/// No signing private key, account, remote endpoint, or store SDK is needed.
void main() {
  testWidgets(
    'production bootstrap pins commercial verification and keeps guest play',
    (tester) async {
      final directory = Directory.systemTemp.createTempSync(
        'tideglass-config-',
      );
      addTearDown(() => directory.deleteSync(recursive: true));
      await tester.pumpWidget(
        TideglassBootstrap(directory: directory, enableAudio: false),
      );
      await settleIo(
        tester,
        until: () => find.byType(TideglassApp).evaluate().isNotEmpty,
      );
      final app = tester.widget<TideglassApp>(find.byType(TideglassApp));
      final services = app.services!;
      expect(services.configuration.signedOwnershipRequired, isTrue);
      expect(
        services.ownershipCache != null,
        const bool.fromEnvironment('TIDEGLASS_TEST_EXPECT_SIGNED_CACHE'),
      );
      expect(services.session, isNull);
      expect(services.ownedEntitlementIds, isEmpty);
      expect(services.commerceAvailable, isFalse);
      expect(app.controller.state.counts, [1, 0, 0, 0, 0]);
      await tester.runAsync(() => app.controller.save());
      await tester.pumpWidget(const SizedBox());
      expect(tester.takeException(), isNull);
    },
  );
}
