/// English launch strings are centralized so translation never touches rules.
abstract final class Copy {
  static const title = 'Tideglass';
  static const subtitle = 'A harbor for returning stars';
  static const harbor = 'Harbor';
  static const atlas = 'Atlas';
  static const journal = 'Logbook';
  static const radiance = 'RADIANCE';
  static const rate = 'RADIANCE / SECOND';
  static const fleet = 'Your lightkeepers';
  static const fleetHint = 'Build a fleet. Bring the constellations home.';
  static const introduction = 'A small light, a beginning.';
  static const introductionBody =
      'Your first Spark Skiff is already gathering Radiance. Build another to brighten the harbor. Your fleet keeps working while you are away.';
  static const introductionDismiss = 'Let’s begin';
  static const rechart = 'Rechart the ocean';
  static const rechartBody = 'A stronger atlas. A new beginning.';
  static const rechartHint =
      'Charts are permanent. They strengthen every lightkeeper in every fleet you build.';
  static const rechartLost =
      'Rebuild: current Radiance and all purchased lightkeepers.';
  static const rechartKept =
      'Keep: lifetime Radiance, Charts, Survey Notes, stored Focus and its remaining effect, completed Surveys, discoveries and automation settings. Your free starting Skiff returns.';
  static const noPerfectReset =
      'There is no single perfect reset. A larger claim increases permanent power, while waiting lets your current fleet keep earning.';
  static const firstRechartHint =
      'Your first Rechart becomes available at 1 billion lifetime Radiance.';
  static const returnTitle = 'The harbor kept its light.';
  static const returnBody =
      'Your saved fleet continued its work while you were away.';
  static const returnAcknowledge = 'Welcome the light';
  static const settings = 'Settings';
  static const reducedMotion = 'Reduce motion';
  static const reducedMotionHint = 'Still waves and quiet celebrations';
  static const largerText = 'Larger text';
  static const largerTextHint = 'Increase text above your device setting';
  static const scientific = 'Scientific numbers';
  static const scientificHint = 'Use powers of ten for large values';
  static const help = 'How your harbor works';
  static const offlineHelp =
      'Your first 24 hours away earn at full rate. The next 48 hours earn at one quarter rate. Production stops after 72 hours away. Timers use real elapsed time.';
  static const milestoneHelp =
      'At 25, 50, 75 and 100 lightkeepers of one kind, that entire tier doubles its output. Early tiers also strengthen late tiers after 25 Charts.';
  static const saveFailed =
      'Progress could not be saved. Keep the game open and retry.';
}

/// Literal labels and help copy for the native presentation layer.
abstract final class UiCopy {
  static String lightkeeperCount(int count) =>
      '$count ${count == 1 ? 'lightkeeper' : 'lightkeepers'}';
  static const theFirstLight = '✦  THE FIRST LIGHT';
  static const aWiderSky = '✦  A WIDER SKY';
  static const letTheFleetBuild = 'Let the fleet build';
  static const bestPaybackIncludingWhileYouAre =
      'Best payback, including while you are away.';
  static const buy = 'Buy 1';
  static const buyMax = 'Buy max';
  static const forecastsAssumeAFixedFleetAnd =
      'Forecasts assume a fixed fleet and ignore temporary bonuses. New purchases change your forecast.';
  static const undiscoveredLightkeeper = 'Undiscovered lightkeeper';
  static const allFourMilestonesIlluminated = 'All four milestones illuminated';
  static const aDistantHorizon = 'A distant horizon';
  static const gathering = 'Gathering';
  static const yourPermanentAtlas = 'YOUR PERMANENT ATLAS';
  static const permanentPower = 'Permanent power';
  static const lifetimeRadiance = 'Lifetime Radiance';
  static const newChartsAvailable = 'New Charts available';
  static const notYet = 'Not yet';
  static const gatherTheFirstBillion = 'Gather the first billion';
  static const anAtlasThatGrowsWithYou = 'An atlas that grows with you';
  static const charts = '10 Charts';
  static const aSelfBuildingFleet = 'A self-building fleet';
  static const freeAutomaticBuyingForEveryProducer =
      'Free automatic buying for every producer.';
  static const chartsText = '25 Charts';
  static const aConnectedOcean = 'A connected ocean';
  static const skiffsAndNurseriesStrengthenLoomsAnd =
      'Skiffs and Nurseries strengthen Looms and Observatories.';
  static const chartABrighterOcean = 'Chart a brighter ocean?';
  static const yourCurrentFleetStopsEarningAs =
      'Your current fleet stops earning as soon as you confirm.';
  static const keepBuilding = 'Keep building';
  static const rechart = 'Rechart';
  static const theKeeperSLogbook = 'The keeper’s logbook';
  static const smallDiscoveriesKeptForTheNext =
      'Small discoveries, kept for the next voyage.';
  static const aLightLeftOn = '01  /  A LIGHT LEFT ON';
  static const theOceanDidNotForgetIts =
      'The ocean did not forget its stars. It scattered them into the water, waiting for someone to gather them again.';
  static const oneSkiffOneLanternEnoughTo =
      'One skiff. One lantern. Enough to begin.';
  static const whileYouAreAway = 'While you are away';
  static const aGrowingFleet = 'A growing fleet';
  static const aPermanentAtlas = 'A permanent atlas';
  static const yourHarborIsSavedOnThis = 'Your harbor is saved on this device.';
  static const sessionPreviewLocalSavingIsNot =
      'Session preview · local saving is not connected.';
  static const exportMyHarbor = 'Export my harbor';
  static const importASavedHarbor = 'Import a saved harbor';
  static const openSourceLicenses = 'Open-source licenses';
  static const theHarborSRhythm = 'The harbor’s rhythm';
  static const focusStored = 'Focus stored';
  static const oneChargeEveryTwoHoursEach =
      'One charge every two hours. Each gives +20% production for ten minutes; queued time adds together.';
  static const focusTheConstellation = 'Focus the constellation';
  static const surveysComplete = 'Surveys complete';
  static const oneSurveyEveryEightHoursUp =
      'One survey every eight hours, up to three stored. Each completed survey yields 10 Notes.';
  static const surveyNotes = 'Survey Notes';
  static const timeAway = 'Time away';
  static const atFullRate = 'At full rate';
  static const atQuarterRate = 'At quarter rate';
  static const beyondStorage = 'Beyond storage';
  static const yourSavedAutomaticBuyingPolicyWas =
      'Your saved automatic-buying policy was active. Radiance shown includes earnings invested in lightkeepers.';
  static const yourFleetCompositionRemainedUnchanged =
      'Your fleet composition remained unchanged.';
  static const alreadyAddedToYourHarbor = 'Already added to your harbor.';
  static const yourDeviceSReducedMotionAnd =
      'Your device’s reduced-motion and text-size preferences are respected.';
  static const returnToTheHarbor = 'Return to the harbor';
  static const chooseASavedHarbor = 'Choose a saved harbor';
  static const importReplacesThisDeviceSCurrent =
      'Import replaces this device’s current branch. Wallets, Charts and offline time are never added together. A recovery copy of the current harbor is retained.';
  static const pasteYourExportedHarbor = 'Paste your exported harbor';
  static const keepThisHarbor = 'Keep this harbor';
  static const replaceLocalHarbor = 'Replace local harbor';
  static const thisHarborCouldNotBeImported =
      'This harbor could not be imported. Check that the complete backup is valid for this version.';
  static const yourHarborBackup = 'Your harbor backup';
  static const done = 'Done';
  static const theBackupCouldNotBeExported =
      'The backup could not be exported. Your current harbor is unchanged.';
  static const dismissRecoveryNotice = 'Dismiss recovery notice';
}
