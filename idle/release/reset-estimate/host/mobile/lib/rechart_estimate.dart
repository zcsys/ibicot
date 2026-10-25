import 'package:flutter/material.dart';
import 'package:tideglass_core/tideglass_core.dart';
import 'package:tideglass_core/rechart_forecast.dart';

import 'number_format.dart';
import 'presentation.dart';
import 'rechart_copy.dart';
import 'rechart_forecast_task.dart';

/// Wraps naturally in the existing ReadingDialog, including its large-text
/// fullscreen scroll path. No table, fixed height, truncation or small type.
class RechartEstimatePanel extends StatefulWidget {
  const RechartEstimatePanel({super.key, required this.snapshot});
  final GameState snapshot;
  @override
  State<RechartEstimatePanel> createState() => _RechartEstimatePanelState();
}

class _RechartEstimatePanelState extends State<RechartEstimatePanel> {
  late RechartForecastTask task;
  @override
  void initState() {
    super.initState();
    task = RechartForecastTask(widget.snapshot);
  }

  @override
  void didUpdateWidget(RechartEstimatePanel oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (!identical(oldWidget.snapshot, widget.snapshot)) {
      task.cancel();
      task = RechartForecastTask(widget.snapshot);
    }
  }

  @override
  void dispose() {
    task.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<RechartForecast?>(
    future: task.result,
    builder: (context, value) => RechartEstimateContent(
      forecast: value.data,
      loading: value.connectionState != ConnectionState.done,
    ),
  );
}

/// Separate immutable presentation enables status/layout tests without timing
/// a worker. The real preview above always runs the actual forecast task.
class RechartEstimateContent extends StatelessWidget {
  const RechartEstimateContent({
    super.key,
    this.forecast,
    this.loading = false,
  });
  final RechartForecast? forecast;
  final bool loading;
  String feature(int threshold) => switch (threshold) {
    10 => RechartCopy.autoBuy,
    25 => RechartCopy.synergy,
    100 => RechartCopy.resetPlans,
    _ => throw ArgumentError('Unknown atlas unlock'),
  };

  @override
  Widget build(BuildContext context) {
    final result = forecast;
    final valid = !loading && result?.status == RechartForecastStatus.estimated;
    final paragraphs = <String>[];
    if (loading) {
      paragraphs.add(RechartCopy.calculating);
    } else if (!valid) {
      paragraphs.add(
        result?.status == RechartForecastStatus.notEligible
            ? RechartCopy.notEligible
            : RechartCopy.unavailable,
      );
    } else {
      final value = result!;
      paragraphs.add(
        value.breakEvenSeconds == null
            ? RechartCopy.noCatchUp
            : RechartCopy.breakEven(
                durationLabel(Duration(seconds: value.breakEvenSeconds!)),
              ),
      );
      if (value.breakEvenSeconds != null)
        paragraphs.add(RechartCopy.definition);
      paragraphs.add(
        value.rebuildSeconds == null
            ? RechartCopy.rebuildBeyond
            : value.rebuildSeconds == 0
            ? RechartCopy.rebuildNow
            : RechartCopy.rebuild(
                durationLabel(Duration(seconds: value.rebuildSeconds!)),
              ),
      );
      for (final threshold in value.unlockedChartThresholds) {
        paragraphs.add(RechartCopy.unlocked(feature(threshold)));
      }
      final target = value.nextChartTarget!;
      paragraphs.add(
        [10, 25, 100].map(BigInt.from).contains(target)
            ? RechartCopy.nextUnlock(target, feature(target.toInt()))
            : RechartCopy.nextChart(target),
      );
      paragraphs.addAll([
        RechartCopy.assumptionsTitle,
        RechartCopy.purchases,
        RechartCopy.continuation,
        RechartCopy.objective,
        RechartCopy.snapshot,
      ]);
    }
    return Semantics(
      container: true,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Semantics(
            header: true,
            child: LocalizedText(
              RechartCopy.title,
              style: Theme.of(context).textTheme.titleMedium,
            ),
          ),
          for (final paragraph in paragraphs) ...[
            const SizedBox(height: 12),
            LocalizedText(paragraph),
          ],
        ],
      ),
    );
  }
}
