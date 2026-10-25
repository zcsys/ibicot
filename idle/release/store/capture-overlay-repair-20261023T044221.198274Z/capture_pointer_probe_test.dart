import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../../../game/mobile/integration_test/platform_smoke_test.dart';

void main() {
  final binding = CaptureGalleryBinding();
  // Host-only routing probe; this policy does not change the capture harness.
  binding.framePolicy = LiveTestWidgetsFlutterBindingFramePolicy.onlyPumps;
  WidgetController.hitTestWarningShouldBeFatal = true;

  testWidgets('capture binding preserves real hit-tested pointer dispatch', (
    tester,
  ) async {
    var activations = 0;
    final positions = <Offset>[];
    final sources = <TestBindingEventSource>[];
    final eventTypes = <String>[];
    await tester.pumpWidget(
      Directionality(
        textDirection: TextDirection.ltr,
        child: Listener(
          behavior: HitTestBehavior.opaque,
          onPointerDown: (event) {
            positions.add(event.position);
            sources.add(binding.pointerEventSource);
            eventTypes.add('down');
          },
          onPointerUp: (event) {
            positions.add(event.position);
            sources.add(binding.pointerEventSource);
            eventTypes.add('up');
          },
          child: Center(
            child: GestureDetector(
              key: const ValueKey('hit-target'),
              onTap: () => activations += 1,
              child: const SizedBox(
                width: 120,
                height: 90,
                child: ColoredBox(color: Colors.teal),
              ),
            ),
          ),
        ),
      ),
    );
    final center = tester.getCenter(find.byKey(const ValueKey('hit-target')));
    const outside = Offset(5, 5);
    await tester.tapAt(center);
    expect(activations, 1);
    await tester.tapAt(outside);
    expect(
      activations,
      1,
      reason: 'A miss must not invoke the target callback',
    );
    expect(positions, [center, center, outside, outside]);
    expect(eventTypes, ['down', 'up', 'down', 'up']);
    expect(sources, everyElement(TestBindingEventSource.device));
    expect(binding.routedTestPointerEvents, greaterThanOrEqualTo(4));
    expect(binding.shouldPropagateDevicePointerEvents, isTrue);
    expect(tester.takeException(), isNull);
    debugPrint(
      'CAPTURE_POINTER_PROBE ${jsonEncode({'host_routing_only': true, 'physical_input_or_native_capture_claim': false, 'activations_after_hit_and_miss': activations, 'unchanged_hit_and_miss_coordinates': true, 'event_order': eventTypes, 'dispatch_sources': sources.map((source) => source.name).toList(), 'routed_test_pointer_events': binding.routedTestPointerEvents})}',
    );
    await tester.pumpWidget(const SizedBox.shrink());
  });
}
