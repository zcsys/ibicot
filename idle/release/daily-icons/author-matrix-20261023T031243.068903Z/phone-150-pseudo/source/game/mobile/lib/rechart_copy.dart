import 'presentation.dart';

/// Central launch-English copy; templates protect values in pseudo mode.
/// No translated text or formatted duration feeds back into the simulation.
abstract final class RechartCopy {
  static const title = 'Estimated break-even';
  static const calculating = 'Comparing rebuilding with keeping this fleet…';
  static const unavailable =
      'Estimate unavailable for this preview. You can still choose whether to Rechart.';
  static const notEligible =
      'Earn another eligible Chart before comparing a Rechart.';
  static const noCatchUp =
      'No lasting catch-up found within 24 hours under this policy.';
  static const definition =
      'At each one-minute check from this point through 24 hours, Rechart has earned at least as much new Radiance as keeping this fleet. The paths may cross between checks or after 24 hours.';
  static const assumptionsTitle = 'What this estimate assumes';
  static const purchases =
      'Buy at opening and every minute: choose the unit with the best added output per cost, repeat until that unit is unaffordable, then wait. This assumes active buying before automation unlocks and replaces your saved plan for this comparison only.';
  static const continuation =
      'No later Rechart or new bonus activation. Current Focus and Support boosts expire normally. Both paths earn at full rate for 24 hours.';
  static const objective =
      'Compare new Radiance earned, not wallet wealth. Keeping the fleet can invest its current wallet; Rechart loses that wallet and rebuilds from the free Skiff while earning throughout.';
  static const snapshot =
      'Uses the fleet when this preview opened. New purchases, bonuses or waiting can change the result. This is not a universally best reset time.';
  static const rebuildBeyond =
      'Rebuilding did not reach today’s unboosted output within 24 hours.';
  static const rebuildNow =
      'The free Skiff already reaches today’s unboosted output.';
  static const autoBuy = 'automatic buying';
  static const synergy = 'cross-tier synergies';
  static const resetPlans = 'conditional reset plans';
  static String breakEven(String time) => Presentation.template(
    'About {time}, on the one-minute grid.',
    {'time': time},
  );
  static String rebuild(String time) => Presentation.template(
    'Rebuilding reaches today’s unboosted output in about {time}.',
    {'time': time},
  );
  static String nextUnlock(BigInt target, String feature) =>
      Presentation.template(
        'Next atlas milestone: {target} total Charts unlock {feature}.',
        {'target': target, 'feature': Presentation.text(feature)},
      );
  static String nextChart(BigInt target) => Presentation.template(
    'Next atlas step: {target} total Charts. No further automation unlock is assumed.',
    {'target': target},
  );
  static String unlocked(String feature) => Presentation.template(
    'This claim unlocks {feature}.',
    {'feature': Presentation.text(feature)},
  );
}
