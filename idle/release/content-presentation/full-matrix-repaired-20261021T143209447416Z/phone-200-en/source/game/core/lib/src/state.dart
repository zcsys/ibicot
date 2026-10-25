import 'fixed.dart';
import 'daily.dart';
import 'support.dart';

const economyVersion = 'tideglass-economy-1.0.0';
const stateSchemaVersion = 4;
const eventOrderVersion = 4;

/// Immutable production state. Wallet/lifetime/Charts are never doubles.
/// Native persistence wraps this payload in the separate save envelope.
class GameState {
  /// Selected by a compiled, trusted rules registry, never inferred from a save.
  final String rulesVersion;
  final List<int> counts;
  final BigInt walletMicros;
  final BigInt lifetimeMicros;
  final BigInt charts;
  final BigInt elapsedMicros;
  final BigInt earningRemainder;
  final int revision;
  final bool autoBuyEnabled;
  final int focusCharges;
  final BigInt focusPhaseMicros;
  final BigInt focusRemainingMicros;
  final int completedSurveys;
  final BigInt surveyPhaseMicros;
  final BigInt surveyNotes;
  final DailyState daily;
  final SupportState support;
  BigInt get supportRemainingMicros => support.remainingMicros;
  BigInt get nextDiscoverySequence => daily.nextDiscoverySequence;
  BigInt get nextSettlementSequence => support.nextSettlementSequence;
  final BigInt lifetimePurchasedCount;
  final int rechartCount;
  final BigInt lastRechartElapsedMicros;
  final BigInt surveysCollectedTotal;
  final Set<String> completedCalibrationIds;
  final int extraPlanSlots;
  final List<AutomationPlan> automationPlans;
  final String selectedAutomationPlanId;

  List<DailyContract> get dailyContracts => daily.contracts;
  BigInt get passXp => daily.passXp;
  AutomationPlan get selectedAutomationPlan =>
      automationPlans.firstWhere((plan) => plan.id == selectedAutomationPlanId);

  GameState({
    this.rulesVersion = economyVersion,
    List<int> counts = const [1, 0, 0, 0, 0],
    BigInt? walletMicros,
    BigInt? lifetimeMicros,
    BigInt? charts,
    BigInt? elapsedMicros,
    BigInt? earningRemainder,
    this.revision = 0,
    this.autoBuyEnabled = false,
    this.focusCharges = 0,
    BigInt? focusPhaseMicros,
    BigInt? focusRemainingMicros,
    this.completedSurveys = 0,
    BigInt? surveyPhaseMicros,
    BigInt? surveyNotes,
    DailyState? daily,
    SupportState? support,
    BigInt? lifetimePurchasedCount,
    this.rechartCount = 0,
    BigInt? lastRechartElapsedMicros,
    BigInt? surveysCollectedTotal,
    Set<String> completedCalibrationIds = const {},
    this.extraPlanSlots = 0,
    List<AutomationPlan>? automationPlans,
    this.selectedAutomationPlanId = 'plan.base',
  })  : counts = List.unmodifiable(counts),
        walletMicros = walletMicros ?? BigInt.zero,
        lifetimeMicros = lifetimeMicros ?? BigInt.zero,
        charts = charts ?? BigInt.zero,
        elapsedMicros = elapsedMicros ?? BigInt.zero,
        earningRemainder = earningRemainder ?? BigInt.zero,
        focusPhaseMicros = focusPhaseMicros ?? BigInt.zero,
        focusRemainingMicros = focusRemainingMicros ?? BigInt.zero,
        surveyPhaseMicros = surveyPhaseMicros ?? BigInt.zero,
        surveyNotes = surveyNotes ?? BigInt.zero,
        daily = daily ?? DailyState(),
        support = support ?? SupportState(),
        lifetimePurchasedCount = lifetimePurchasedCount ?? BigInt.zero,
        lastRechartElapsedMicros = lastRechartElapsedMicros ?? BigInt.zero,
        surveysCollectedTotal = surveysCollectedTotal ?? BigInt.zero,
        completedCalibrationIds = Set.unmodifiable(completedCalibrationIds),
        automationPlans =
            List.unmodifiable(automationPlans ?? [AutomationPlan.base()]) {
    validate();
  }

  factory GameState.initial({String rulesVersion = economyVersion}) =>
      GameState(rulesVersion: rulesVersion);

  void validate() {
    if (!RegExp(r'^tideglass-economy-\d+\.\d+\.\d+$').hasMatch(rulesVersion)) {
      throw ArgumentError('Invalid economic rules identity');
    }
    if (counts.length != 5 ||
        counts.any((count) => count < 0) ||
        counts[0] < 1) {
      throw ArgumentError(
          'Five nonnegative counts and the gifted first Skiff are required');
    }
    if ([
      walletMicros,
      lifetimeMicros,
      charts,
      elapsedMicros,
      earningRemainder,
      focusPhaseMicros,
      focusRemainingMicros,
      surveyPhaseMicros,
      surveyNotes,
      lifetimePurchasedCount,
      lastRechartElapsedMicros,
      surveysCollectedTotal
    ].any((value) => value.isNegative)) {
      throw ArgumentError('State quantities must be nonnegative');
    }
    if ((support.activeSettlementRequest != null &&
            support.activeSettlementId !=
                support.activeSettlementRequest!.identity(daily.accountSeed)) ||
        support.tokenDay > daily.dayHighWater ||
        support.caches.any((cache) => cache.endElapsedMicros > elapsedMicros) ||
        (support.activeSettlementId != null &&
            support.sourceStartElapsedMicros + support.nextOffsetMicros !=
                elapsedMicros) ||
        support.caches.any((cache) =>
            cache.settlementRateRaw == null &&
            cache.settlementId != support.activeSettlementId) ||
        support.tokens.any((token) =>
            token.id !=
            'support:${daily.accountSeed}:${token.accountDay}:${token.slot}')) {
      throw ArgumentError(
          'Support ledger conflicts with account or elapsed cursor');
    }
    if (walletMicros > lifetimeMicros)
      throw ArgumentError('Wallet cannot exceed lifetime income');
    if (charts > BigInt.zero) {
      final firstGate = BigInt.from(10).pow(15);
      if (charts < BigInt.from(10) ||
          lifetimeMicros < firstGate ||
          charts.pow(20) * firstGate.pow(13) >
              BigInt.from(10).pow(20) * lifetimeMicros.pow(13)) {
        throw ArgumentError('Awarded Charts exceed exact earned entitlement');
      }
    }
    if (revision < 0 ||
        focusCharges < 0 ||
        focusCharges > 12 ||
        completedSurveys < 0 ||
        completedSurveys > 3) {
      throw ArgumentError('Invalid revision or timer capacity');
    }
    if (earningRemainder >= Fixed.scale * BigInt.from(400))
      throw ArgumentError('Invalid earning remainder');
    if (focusPhaseMicros >= BigInt.from(7200) * BigInt.from(1000000) ||
        surveyPhaseMicros >= BigInt.from(28800) * BigInt.from(1000000)) {
      throw ArgumentError('Timer phase must be less than its cycle');
    }
    if ((focusCharges == 12 && focusPhaseMicros != BigInt.zero) ||
        (completedSurveys == 3 && surveyPhaseMicros != BigInt.zero)) {
      throw ArgumentError('Full queues cannot bank hidden cycle progress');
    }
    if (autoBuyEnabled && charts < BigInt.from(10))
      throw ArgumentError('Autobuy requires 10 Charts');
    if (rechartCount < 0 ||
        lastRechartElapsedMicros > elapsedMicros ||
        extraPlanSlots < 0 ||
        extraPlanSlots > 5 ||
        automationPlans.isEmpty ||
        automationPlans.length > 1 + extraPlanSlots ||
        automationPlans.map((p) => p.id).toSet().length !=
            automationPlans.length ||
        !automationPlans.any((p) => p.id == 'plan.base') ||
        !automationPlans.any((p) => p.id == selectedAutomationPlanId) ||
        (charts < BigInt.from(100) &&
            automationPlans.any((p) => p.autoResetEnabled))) {
      throw ArgumentError('Invalid statistics or automation plan state');
    }
  }

  GameState copyWith(
          {String? rulesVersion,
          List<int>? counts,
          BigInt? walletMicros,
          BigInt? lifetimeMicros,
          BigInt? charts,
          BigInt? elapsedMicros,
          BigInt? earningRemainder,
          int? revision,
          bool? autoBuyEnabled,
          int? focusCharges,
          BigInt? focusPhaseMicros,
          BigInt? focusRemainingMicros,
          int? completedSurveys,
          BigInt? surveyPhaseMicros,
          BigInt? surveyNotes,
          DailyState? daily,
          SupportState? support,
          BigInt? lifetimePurchasedCount,
          int? rechartCount,
          BigInt? lastRechartElapsedMicros,
          BigInt? surveysCollectedTotal,
          Set<String>? completedCalibrationIds,
          int? extraPlanSlots,
          List<AutomationPlan>? automationPlans,
          String? selectedAutomationPlanId}) =>
      GameState(
          rulesVersion: rulesVersion ?? this.rulesVersion,
          counts: counts ?? this.counts,
          walletMicros: walletMicros ?? this.walletMicros,
          lifetimeMicros: lifetimeMicros ?? this.lifetimeMicros,
          charts: charts ?? this.charts,
          elapsedMicros: elapsedMicros ?? this.elapsedMicros,
          earningRemainder: earningRemainder ?? this.earningRemainder,
          revision: revision ?? this.revision,
          autoBuyEnabled: autoBuyEnabled ?? this.autoBuyEnabled,
          focusCharges: focusCharges ?? this.focusCharges,
          focusPhaseMicros: focusPhaseMicros ?? this.focusPhaseMicros,
          focusRemainingMicros:
              focusRemainingMicros ?? this.focusRemainingMicros,
          completedSurveys: completedSurveys ?? this.completedSurveys,
          surveyPhaseMicros: surveyPhaseMicros ?? this.surveyPhaseMicros,
          surveyNotes: surveyNotes ?? this.surveyNotes,
          daily: daily ?? this.daily,
          support: support ?? this.support,
          lifetimePurchasedCount:
              lifetimePurchasedCount ?? this.lifetimePurchasedCount,
          rechartCount: rechartCount ?? this.rechartCount,
          lastRechartElapsedMicros:
              lastRechartElapsedMicros ?? this.lastRechartElapsedMicros,
          surveysCollectedTotal:
              surveysCollectedTotal ?? this.surveysCollectedTotal,
          completedCalibrationIds:
              completedCalibrationIds ?? this.completedCalibrationIds,
          extraPlanSlots: extraPlanSlots ?? this.extraPlanSlots,
          automationPlans: automationPlans ?? this.automationPlans,
          selectedAutomationPlanId:
              selectedAutomationPlanId ?? this.selectedAutomationPlanId);

  Map<String, dynamic> toJson() => {
        'schema_version': stateSchemaVersion,
        'economic_version': rulesVersion,
        'event_order_version': eventOrderVersion,
        'counts': counts,
        'wallet_micros': walletMicros.toString(),
        'lifetime_micros': lifetimeMicros.toString(),
        'charts': charts.toString(),
        'elapsed_micros': elapsedMicros.toString(),
        'earning_remainder': earningRemainder.toString(),
        'revision': revision,
        'auto_buy_enabled': autoBuyEnabled,
        'focus_charges': focusCharges,
        'focus_phase_micros': focusPhaseMicros.toString(),
        'focus_remaining_micros': focusRemainingMicros.toString(),
        'completed_surveys': completedSurveys,
        'survey_phase_micros': surveyPhaseMicros.toString(),
        'survey_notes': surveyNotes.toString(),
        'daily': daily.toJson(),
        'support': support.toJson(),
        'lifetime_purchased_count': lifetimePurchasedCount.toString(),
        'rechart_count': rechartCount,
        'last_rechart_elapsed_micros': lastRechartElapsedMicros.toString(),
        'surveys_collected_total': surveysCollectedTotal.toString(),
        'completed_calibration_ids': completedCalibrationIds.toList()..sort(),
        'extra_plan_slots': extraPlanSlots,
        'automation_plans':
            automationPlans.map((plan) => plan.toJson()).toList(),
        'selected_automation_plan_id': selectedAutomationPlanId,
      };

  /// The caller must resolve this exact version from its compiled registry
  /// before decoding. The default continues to reject every non-v1 economy.
  factory GameState.fromJson(Map<String, dynamic> json,
      {String expectedEconomicVersion = economyVersion}) {
    final legacy = json['schema_version'] == 1;
    final preSupport = legacy || json['schema_version'] == 2;
    final preReceipts = preSupport || json['schema_version'] == 3;
    final keys = {
      'schema_version',
      'economic_version',
      'event_order_version',
      'counts',
      'wallet_micros',
      'lifetime_micros',
      'charts',
      'elapsed_micros',
      'earning_remainder',
      'revision',
      'auto_buy_enabled',
      'focus_charges',
      'focus_phase_micros',
      'focus_remaining_micros',
      'completed_surveys',
      'survey_phase_micros',
      'survey_notes'
    };
    if (!legacy)
      keys.addAll({
        'daily',
        'lifetime_purchased_count',
        'rechart_count',
        'last_rechart_elapsed_micros',
        'surveys_collected_total',
        'completed_calibration_ids',
        'extra_plan_slots',
        'automation_plans',
        'selected_automation_plan_id'
      });
    if (!preSupport) keys.add('support');
    if (json.length != keys.length || !json.keys.every(keys.contains)) {
      throw FormatException('Unexpected or missing state fields');
    }
    if ((!preReceipts && json['schema_version'] != stateSchemaVersion) ||
        json['economic_version'] != expectedEconomicVersion ||
        json['event_order_version'] !=
            (legacy
                ? 1
                : (preSupport ? 2 : (preReceipts ? 3 : eventOrderVersion)))) {
      throw FormatException(
          'Unsupported state, economy or event ordering version');
    }
    BigInt integer(String key) {
      final raw = json[key];
      if (raw is! String || !RegExp(r'^(0|[1-9][0-9]*)$').hasMatch(raw)) {
        throw FormatException(
            '$key must be a canonical nonnegative integer string');
      }
      return BigInt.parse(raw);
    }

    if (json['counts'] is! List ||
        (json['counts'] as List).any((v) => v is! int) ||
        json['revision'] is! int ||
        json['auto_buy_enabled'] is! bool ||
        json['focus_charges'] is! int ||
        json['completed_surveys'] is! int) {
      throw FormatException('Invalid state primitive field type');
    }
    return GameState(
        rulesVersion: expectedEconomicVersion,
        counts: List<int>.from(json['counts'] as List),
        walletMicros: integer('wallet_micros'),
        lifetimeMicros: integer('lifetime_micros'),
        charts: integer('charts'),
        elapsedMicros: integer('elapsed_micros'),
        earningRemainder: integer('earning_remainder'),
        revision: json['revision'] as int,
        autoBuyEnabled: json['auto_buy_enabled'] as bool,
        focusCharges: json['focus_charges'] as int,
        focusPhaseMicros: integer('focus_phase_micros'),
        focusRemainingMicros: integer('focus_remaining_micros'),
        completedSurveys: json['completed_surveys'] as int,
        surveyPhaseMicros: integer('survey_phase_micros'),
        surveyNotes: integer('survey_notes'),
        support: preSupport
            ? SupportState()
            : SupportState.fromJson(Map<String, dynamic>.from(json['support'] as Map),
                legacy: preReceipts,
                migrationUtcMicros: (json['daily'] as Map)['utc_anchor_micros'] == null
                    ? null
                    : BigInt.parse((json['daily'] as Map)['utc_anchor_micros'] as String) +
                        integer('elapsed_micros')),
        daily: legacy
            ? DailyState()
            : DailyState.fromJson(Map<String, dynamic>.from(json['daily'] as Map),
                legacy: preReceipts),
        lifetimePurchasedCount: legacy
            ? BigInt.from((json['counts'] as List).cast<int>().fold<int>(0, (sum, n) => sum + n) -
                1)
            : integer('lifetime_purchased_count'),
        rechartCount: legacy
            ? (integer('charts') > BigInt.zero ? 1 : 0)
            : json['rechart_count'] as int,
        lastRechartElapsedMicros: legacy
            ? integer('elapsed_micros')
            : integer('last_rechart_elapsed_micros'),
        surveysCollectedTotal: legacy
            ? integer('survey_notes') ~/ BigInt.from(10)
            : integer('surveys_collected_total'),
        completedCalibrationIds:
            legacy ? {} : Set<String>.from(json['completed_calibration_ids'] as List),
        extraPlanSlots: legacy ? 0 : json['extra_plan_slots'] as int,
        automationPlans: legacy ? [AutomationPlan.base()] : (json['automation_plans'] as List).map((p) => AutomationPlan.fromJson(Map<String, dynamic>.from(p as Map))).toList(),
        selectedAutomationPlanId: legacy ? 'plan.base' : json['selected_automation_plan_id'] as String);
  }
}

class CoreEvent {
  final String id;
  final String kind;
  final BigInt elapsedMicros;
  final Map<String, dynamic> details;
  CoreEvent(
      {required this.id,
      required this.kind,
      required this.elapsedMicros,
      Map<String, dynamic> details = const {}})
      : details = Map.unmodifiable(details);
  Map<String, dynamic> toJson() => {
        'id': id,
        'kind': kind,
        'elapsed_micros': elapsedMicros.toString(),
        'details': details
      };
}

class TransitionResult {
  final GameState state;
  final List<CoreEvent> events;
  final bool accepted;
  final String? reason;
  TransitionResult(this.state,
      {List<CoreEvent> events = const [], this.accepted = true, this.reason})
      : events = List.unmodifiable(events);
}
