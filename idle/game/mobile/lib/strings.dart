import 'presentation.dart';

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

/// English UI catalogue. Templates preserve inserted values in pseudo builds.
abstract final class UiEnglish {
  static String cosmeticStoreOffer(Object? title, Object? price) =>
      Presentation.template('{title} · {price}', {
        'title': title,
        'price': price,
      });
  static const serviceThisActionCouldNotBeConfirmedYour =
      "This action could not be confirmed. Your local harbor remains available. Review the service connection and try again.";
  static const serviceTheServiceCouldNotConfirmThisRequest =
      "The service could not confirm this request. Your local harbor remains available. Refresh or recover before retrying an account change.";
  static const serviceTheServiceDidNotAuthorizeThisAction =
      "The service did not authorize this action. Check your account recovery details. Your local harbor is kept.";
  static const serviceTheAccountSessionNeedsRecoveryYourLocal =
      "The account session needs recovery. Your local harbor is kept.";
  static const serviceCloudDataChangedOnAnotherDeviceRefresh =
      "Cloud data changed on another device. Refresh branches and review before retrying. Your local harbor was not merged.";
  static const serviceChooseThisBranch = "Choose this branch";
  static String serviceSettledThroughSnapshotSettledThroughToUtcToIsoString(
    Object? value0,
  ) => Presentation.template("Settled through {value0}", {'value0': value0});
  static String serviceRevisionSnapshotRevision(Object? value0) =>
      Presentation.template("Revision {value0}", {'value0': value0});
  static String serviceSaveSnapshotSaveId(Object? value0) =>
      Presentation.template("Save {value0}", {'value0': value0});
  static String serviceBranchSnapshotBranchId(Object? value0) =>
      Presentation.template("Branch {value0}", {'value0': value0});
  static const serviceEarlierSave = "Earlier save";
  static const serviceBranchTip = "Branch tip";
  static const serviceSelectedCloudSave = "Selected cloud save";
  static const serviceRemoteReportPreferencesRequireAnAccountConnection =
      "Remote report preferences require an account connection. Guest play does not send account usage reports.";
  static const serviceStopReportsAndDeleteRemoteEvents =
      "Stop reports and delete remote events";
  static const serviceAllowUsageReports2 = "Allow usage reports";
  static const serviceRetryReportDeletion = "Retry report deletion";
  static const serviceLocalCollectionIsStoppedRemoteDeletionIs =
      "Local collection is stopped. Remote deletion is still pending; an offline request is not a confirmed deletion.";
  static const serviceThisConsentIsSeparateFromCloudStorage =
      "This consent is separate from cloud storage. Reports are not required to play or recover a harbor.";
  static const serviceCollectionIsOff = "Collection is off.";
  static const serviceCollectionIsOn = "Collection is on.";
  static const serviceOptionalUsageReports = "Optional usage reports";
  static const serviceDeleteCloudAccount2 = "Delete cloud account";
  static const serviceForgetDeviceSignInWithoutNetwork =
      "Forget device sign-in without network";
  static const serviceSignOutOfThisDevice2 = "Sign out of this device";
  static const serviceThisIsTheDataReturnedByYour =
      "This is the data returned by your account service. It may contain cloud saves and account records. Copy and retain it privately. Displaying this export does not save a file on your behalf.";
  static const serviceAccountDataExport = "Account data export";
  static const serviceExportAccountData = "Export account data";
  static const serviceReplaceRecoveryCode2 = "Replace recovery code";
  static const serviceRecoveryAndAccountData = "Recovery and account data";
  static const serviceUploadCurrentHarbor2 = "Upload current harbor";
  static const serviceNoCloudSavesHaveBeenUploaded =
      "No cloud saves have been uploaded.";
  static const serviceMoreThanOneBranchNeedsYourReview =
      "More than one branch needs your review. Choose the branch you want to continue.";
  static String serviceCloudRevisionCloudGeneration(Object? value0) =>
      Presentation.template("Cloud revision {value0}", {'value0': value0});
  static const serviceRefreshCloudBranches = "Refresh cloud branches";
  static const serviceRefreshToSeeActualSavedBranchesA =
      "Refresh to see actual saved branches. A branch is a complete harbor, with its own revision and settlement time. Balances are never combined.";
  static const serviceCloudBranches = "Cloud branches";
  static const serviceKeepRecoveryDetails = "Keep recovery details";
  static const serviceUploadsAreLockedUntilRecoveryDetailsAre =
      "Uploads are locked until recovery details are retained. If this screen no longer has your new code, recover the account using the details you kept.";
  static const serviceAccountID3 = "Account ID";
  static const serviceAccount = "Account";
  static const serviceRecoverAnExistingAccount = "Recover an existing account";
  static const serviceCreateACloudAccount = "Create a cloud account";
  static const serviceOptionalAccount = "Optional account";
  static const serviceThisIsACopyOfYourLocal =
      "This is a copy of your local harbor. It contains no account sign-in or recovery code. Copy it and retain it somewhere safe. Nothing has been uploaded.";
  static const serviceLocalHarborExport = "Local harbor export";
  static const serviceExportLocalHarbor = "Export local harbor";
  static const serviceLocalCopy = "Local copy";
  static const serviceWaitingForServiceResponse =
      "Waiting for service response";
  static const serviceTheServerSignOutOrDeletionCompleted =
      "The server sign-out or deletion completed, but this device could not clear its stored sign-in. The old credential may still be present on this device; it no longer confirms access.";
  static const serviceReportPreferencesCouldNotBeReadSecurely =
      "Report preferences could not be read securely. Collection is off until you make a new choice.";
  static const serviceDeviceSignInCouldNotBeSaved =
      "Device sign-in could not be saved securely. Keep your account ID and recovery code; this device may ask you to recover the account next time.";
  static const serviceOnlineServicesAreNotConfiguredInThis =
      "Online services are not configured in this build. Account creation, cloud saves and remote usage reports are unavailable. Your local harbor is unaffected.";
  static const serviceGuestPlayAndLocalSavesWorkWithout =
      "Guest play and local saves work without an account. Cloud storage and usage reports are separate, optional choices. Nothing here uploads or replaces a harbor automatically.";
  static const serviceYourHarborYourChoice = "Your harbor, your choice";
  static const serviceServices = "Services";
  static const serviceUsageCollectionStoppedAndRemoteDeletionConfirmed =
      "Usage collection stopped and remote deletion confirmed.";
  static const serviceUsageReportsEnabledByYourChoice =
      "Usage reports enabled by your choice.";
  static const serviceAllowUsageReports = "Allow usage reports";
  static const serviceReportsHelpUnderstandSessionsAndGameFlows =
      "Reports help understand sessions and game flows. They use a defined set of event names and fields; recovery codes, save contents and free-form text are not included. This choice does not affect your harbor or cloud storage. You can stop collection and request deletion here.";
  static const serviceShareOptionalUsageReports =
      "Share optional usage reports?";
  static const serviceCloudAccountDeletedYourLocalHarborIs =
      "Cloud account deleted. Your local harbor is kept.";
  static const serviceCancel4 = "Cancel";
  static const serviceDeleteCloudAccount = "Delete cloud account";
  static const serviceIUnderstandThatThisCloudAccountAnd =
      "I understand that this cloud account and its data will be deleted";
  static const serviceCurrentRecoveryCode2 = "Current recovery code";
  static const serviceThisPermanentlyDeletesThisServiceAccountAnd =
      "This permanently deletes this service account and its stored account data, including cloud saves. Your local harbor is kept. This does not cancel or refund purchases managed by an app store. Export any account data you want to retain first.";
  static const serviceDeleteTheCloudAccount = "Delete the cloud account";
  static const serviceDeviceSessionRevokedAndSignInCleared =
      "Device session revoked and sign-in cleared. Local harbor kept.";
  static const serviceDeviceSignInForgottenServerRevocationWas =
      "Device sign-in forgotten. Server revocation was not confirmed. Local harbor kept.";
  static const serviceSignOut = "Sign out";
  static const serviceForgetSignInOnThisDevice =
      "Forget sign-in on this device";
  static const serviceThisAsksTheServiceToRevokeThis =
      "This asks the service to revoke this device’s session, then clears its stored sign-in. Your cloud account and local harbor are kept. Retain your account ID and recovery code. If the service is offline, sign-out will not be reported as complete.";
  static const serviceThisRemovesThisDeviceSStoredSign =
      "This removes this device’s stored sign-in without contacting the service. The server session may remain valid until it expires or is revoked. Your cloud account and local harbor are kept. Retain your account ID and recovery code.";
  static const serviceSignOutOfThisDevice = "Sign out of this device?";
  static const serviceForgetThisDeviceSignIn = "Forget this device sign-in?";
  static const serviceTheRecoveryCodeChangeWasNotConfirmed =
      "The recovery-code change was not confirmed. It may have completed if the reply was lost. Keep both codes and try the new code when recovering this account.";
  static const serviceRecoveryCodeReplacedUseTheNewCode =
      "Recovery code replaced. Use the new code you retained.";
  static const serviceCancel3 = "Cancel";
  static const serviceReplaceRecoveryCode = "Replace recovery code";
  static const serviceIHaveSafelyKeptTheNewCode =
      "I have safely kept the new code before this request";
  static const serviceCurrentRecoveryCode = "Current recovery code";
  static const serviceCopyNewRecoveryDetails = "Copy new recovery details";
  static const serviceCopiedToClipboard3 = "Copied to clipboard";
  static String serviceTideglassAccountAccountIdNRecoveryCodeNext(
    Object? value0,
    Object? value1,
  ) => Presentation.template(
    "Tideglass account: {value0}\nRecovery code: {value1}",
    {'value0': value0, 'value1': value1},
  );
  static const serviceNewRecoveryCode = "New recovery code";
  static String serviceAccountIDAccountId(Object? value0) =>
      Presentation.template("Account ID: {value0}", {'value0': value0});
  static const serviceKeepThisNewCodeBeforeSendingThe =
      "Keep this new code before sending the replacement request. If the reply is lost, the change may still have succeeded: try the new code to recover the account. Keep the current code until you have confirmed access.";
  static const serviceReplaceYourRecoveryCode = "Replace your recovery code";
  static const serviceTheCloudBranchWasSelectedButLocal =
      "The cloud branch was selected, but local import did not confirm completion. Your local recovery flow remains available. Refresh branches and review before retrying.";
  static const serviceCloudBranchSelectedAndImportedThePrevious =
      "Cloud branch selected and imported. The previous local save is preserved.";
  static const serviceChooseBranchAndImport = "Choose branch and import";
  static String serviceBranchSnapshotBranchIdNRevisionSnapshotRevisionN(
    Object? value0,
    Object? value1,
    Object? value2,
  ) => Presentation.template(
    "Branch {value0}\nRevision {value1}\nSettled through {value2}\n\nThis replaces the active local harbor with this complete save. Your current local save is preserved by the import process as a separate backup. No balances are combined. Other cloud branches are kept. A changed cloud selection stops this request for review.",
    {'value0': value0, 'value1': value1, 'value2': value2},
  );
  static const serviceUseThisCloudBranch = "Use this cloud branch?";
  static const serviceHarborUploadedCloudBranchesRemainSeparate =
      "Harbor uploaded. Cloud branches remain separate.";
  static const serviceUploadCurrentHarbor = "Upload current harbor";
  static const serviceACompleteCopyOfYourCurrentLocal =
      "A complete copy of your current local harbor will be sent to this account. Existing branches remain separate. Nothing is combined. If the cloud changed since you refreshed, this upload will stop so you can review it.";
  static const serviceUploadThisHarbor = "Upload this harbor?";
  static const serviceSignedInYourLocalHarborIsUnchanged =
      "Signed in. Your local harbor is unchanged.";
  static const serviceCancel2 = "Cancel";
  static const serviceSignInWithoutChangingHarbor =
      "Sign in without changing harbor";
  static const serviceRecoveryCode2 = "Recovery code";
  static const serviceAccountID2 = "Account ID";
  static const serviceSigningInDoesNotReplaceOrUpload =
      "Signing in does not replace or upload your local harbor. You will choose a cloud branch separately. Your recovery code is sent only to the configured account service.";
  static const serviceRecoverAnAccount = "Recover an account";
  static const serviceRecoveryDetailsConfirmedUploadsRemainYourChoice =
      "Recovery details confirmed. Uploads remain your choice.";
  static const serviceKeepUploadsLockedForNow = "Keep uploads locked for now";
  static const serviceContinue = "Continue";
  static const serviceIHaveSafelyKeptTheAccountID =
      "I have safely kept the account ID and recovery code";
  static const serviceCopyingUsesYourDeviceClipboardKeepThe =
      "Copying uses your device clipboard. Keep the details private.";
  static const serviceCopyRecoveryDetails = "Copy recovery details";
  static const serviceCopiedToClipboard2 = "Copied to clipboard";
  static String serviceTideglassAccountAccountIdNRecoveryCodeCode(
    Object? value0,
    Object? value1,
  ) => Presentation.template(
    "Tideglass account: {value0}\nRecovery code: {value1}",
    {'value0': value0, 'value1': value1},
  );
  static const serviceRecoveryCode = "Recovery code";
  static const serviceAccountID = "Account ID";
  static const serviceSaveBothDetailsSomewherePrivateBeforeUploading =
      "Save both details somewhere private before uploading a harbor. The recovery code gives access to this account. It is not included in a harbor save and cannot be shown again after this session.";
  static const serviceKeepYourRecoveryDetails = "Keep your recovery details";
  static const serviceKeepPlayingAsGuest = "Keep playing as guest";
  static const serviceCreateAccount = "Create account";
  static const serviceIChooseOptionalCloudStorage =
      "I choose optional cloud storage";
  static const serviceAnAccountLetsYouUploadAndChoose =
      "An account lets you upload and choose complete harbor saves. Cloud storage is optional. Your current harbor stays on this device. No save is uploaded during account creation. Usage reports are a separate choice and start off.";
  static const serviceChooseCloudStorage = "Choose cloud storage";
  static const serviceDone = "Done";
  static const serviceCopyText = "Copy text";
  static const serviceCopiedToClipboard = "Copied to clipboard";
  static const servicePreviewShortenedForReadabilityCopyTextIncludes =
      "Preview shortened for readability. Copy text includes the complete export.";
  static const serviceCancel = "Cancel";
  static const serviceThisRequestCouldNotBeConfirmedCheck =
      "This request could not be confirmed. Check store and account availability, then refresh or retry delivery. No purchase request grants an appearance by itself.";
  static const serviceLinkThisHarborToYourAccountFirst =
      "Link this harbor to your account first: upload its save in Account & cloud saves, then refresh ownership. Your collection has not changed.";
  static const serviceWaitingForAConfirmedStoreStatus =
      "Waiting for a confirmed store status.";
  static const servicePurchaseResponseVerifiedAppearancesAreShownOnly =
      "Purchase response verified. Appearances are shown only while ownership remains current and any required pass level is earned.";
  static const serviceCurrentStoreVerificationNoLongerGrantsThis =
      "Current store verification no longer grants this purchase.";
  static const serviceDeliveryNeedsARetryAvoidBuyingThe =
      "Delivery needs a retry. Avoid buying the same item again.";
  static const serviceVerificationIsPendingNoAppearanceHasBeen =
      "Verification is pending. No appearance has been delivered yet.";
  static const serviceCheckingThePurchaseWithTheAccountService =
      "Checking the purchase with the account service.";
  static const serviceRecoverTheAccountToContinueDeliveryAvoid =
      "Recover the account to continue delivery. Avoid buying again.";
  static const serviceTheStoreReportedAFailureNothingWas =
      "The store reported a failure. Nothing was added.";
  static const serviceCancelledNothingWasAdded =
      "Cancelled. Nothing was added.";
  static const serviceWaitingForApprovalOrPaymentNothingHas =
      "Waiting for approval or payment. Nothing has been delivered yet.";
  static const serviceTheStoreRequestDidNotStartNothing =
      "The store request did not start. Nothing was added.";
  static const serviceWaitingForTheAppStore = "Waiting for the app store.";
  static const serviceStoreRequest = "Store request";
  static const serviceSupporterBundle = "Supporter bundle";
  static const serviceReturningStarsPremiumAppearances =
      "Returning stars premium appearances";
  static const servicePremiumAppearancesAlsoRequireTheirEarnedPass =
      "Premium appearances also require their earned pass levels. The pass has no paid XP, power, storage or production bonus.";
  static const serviceTheSupporterBundleReusesTheFourShop =
      "The supporter bundle reuses the four shop appearances. Its purchase is unavailable until authenticated soundtrack delivery is ready. No soundtrack download is offered in this build.";
  static const serviceRetryPurchaseDelivery = "Retry purchase delivery";
  static const serviceDeliveryRetryRequestedReviewThePurchaseStatus =
      "Delivery retry requested. Review the purchase status below before buying again.";
  static const serviceCheckExistingOwnership = "Check existing ownership";
  static const serviceCurrentOwnershipCheckedWithTheAccountService =
      "Current ownership checked with the account service.";
  static const serviceRefreshStoreAndOwnership = "Refresh store and ownership";
  static const serviceChecking = "Checking…";
  static const serviceAvailableStorefrontOffersAndCurrentVerifiedOwnership =
      "Available storefront offers and current verified ownership refreshed.";
  static const serviceStoreAndDelivery = "Store and delivery";
  static const serviceOnlyAvailableStorefrontOffersAreShownPurchases =
      "Only available storefront offers are shown. Purchases change appearances, never production, storage, Charts or XP.";
  static const serviceRefreshTheStoreToCheckAvailabilityAnd =
      "Refresh the store to check availability and actual localized offers. No price is estimated.";
  static const serviceOwnershipCouldNotBeVerifiedRefreshWhen =
      "Ownership could not be verified. Refresh when the account service is available. No purchase request will replace missing verification.";
  static const serviceKeepAndConfirmYourAccountRecoveryDetails =
      "Keep and confirm your account recovery details in Account & cloud saves before purchasing.";
  static const serviceStorePurchasesAndRestorationAreNotEnabled =
      "Store purchases and restoration are not enabled for this build. No price or purchase is being offered.";
  static const serviceRecoverOrCreateAnOptionalAccountIn =
      "Recover or create an optional account in Account & cloud saves before using the store. Your local collection is unchanged.";
  static const serviceOnlineServicesAreNotConfiguredInThis2 =
      "Online services are not configured in this build. Purchases and restoration are unavailable. Earned appearances and local play remain available.";
  static const serviceRestorationRequestedTheAppStoreMayRespond =
      "Restoration requested. The app store may respond later; delivery still requires verification.";
  static const serviceTokensUseTheSameSixSlotsWhichever =
      "Tokens use the same six slots whichever route you choose. Account sync does not upload or combine your harbor saves.";
  static const serviceCheckAccountTokenDelivery =
      "Check account token delivery";
  static const serviceOptionalAdsAreUnavailableEveryUnusedSlot =
      "Optional ads are unavailable. Every unused slot has the same free briefing reward.";
  static const cosmeticsRestorationCouldNotBeCheckedPleaseTry =
      "Restoration could not be checked. Please try again when the store is available.";
  static const cosmeticsRestorationRequestedTheStoreMayRespondLater =
      "Restoration requested. The store may respond later; your collection changes only after verification.";
  static const cosmeticsTheStoreCouldNotCompleteThisRequest =
      "The store could not complete this request. Your collection is unchanged.";
  static const cosmeticsStoreRequestSentDeliveryMayStillBe =
      "Store request sent. Delivery may still be pending; appearances enter your collection only after verification.";
  static const cosmeticsBackToCollection = "Back to collection";
  static String cosmeticsVerifiedPassOwnershipAndLevelItemOrdinal(
    Object? value0,
  ) => Presentation.template(
    "Verified pass ownership and level {value0} are required to equip this appearance.",
    {'value0': value0},
  );
  static const cosmeticsKeepDecorationNotes = "Keep decoration · 50 Notes";
  static const cosmeticsEquip = "Equip";
  static const cosmeticsKeptInYourCollection = "Kept in your collection";
  static const cosmeticsEquipped = "Equipped";
  static String cosmeticsEnlargeItemTitlePreview(Object? value0) =>
      Presentation.template("Enlarge {value0} preview", {'value0': value0});
  static const cosmeticsRestorePurchases = "Restore purchases";
  static const cosmeticsContactingTheStore = "Contacting the store…";
  static const cosmeticsYourKeepsakesWillAppearHereAsThe =
      "Your keepsakes will appear here as the harbor grows.";
  static const cosmeticsShop = "Shop";
  static const cosmeticsPremium = "Premium";
  static const cosmeticsFreePass = "Free pass";
  static const cosmeticsCore = "Core";
  static const cosmeticsOwned = "Owned";
  static const cosmeticsAll = "All 36";
  static const cosmeticsRemoveEarnedDecoration = "Remove earned decoration";
  static const cosmeticsRemoveHarborAppearance = "Remove harbor appearance";
  static const cosmeticsOneHarborAppearanceAndOneEarnedDecoration =
      "One harbor appearance and one earned decoration can share your view. These choices change the scenery; production, storage and Charts stay the same.";
  static String cosmeticsWidgetOwnedIdsLengthOfAppearancesKept(
    Object? value0,
  ) => Presentation.template("{value0} of 36 appearances kept", {
    'value0': value0,
  });
  static const cosmeticsHarborCollection = "Harbor collection";
  static const cosmeticsOnlyOwnedAppearancesMayBeEquipped =
      "Only owned appearances may be equipped.";
  static const cosmeticsPurchasesAndRestorationAreNotAvailableIn =
      "Purchases and restoration are not available in this build.";
  static const seasonThisActionIsNotAvailableYet =
      "This action is not available yet.";
  static const seasonYourProgressIsSaved = "Your progress is saved.";
  static const seasonDec = "Dec";
  static const seasonNov = "Nov";
  static const seasonOct = "Oct";
  static const seasonSep = "Sep";
  static const seasonAug = "Aug";
  static const seasonJul = "Jul";
  static const seasonJun = "Jun";
  static const seasonMay = "May";
  static const seasonApr = "Apr";
  static const seasonMar = "Mar";
  static const seasonFeb = "Feb";
  static const seasonJan = "Jan";
  static const seasonArchivedFleetPaused = "Archived fleet · paused";
  static const seasonArchivedFleetContinuing = "Archived fleet · continuing";
  static String seasonLiveWindowTimeUntilSeasonEndsAtMicrosRemaining(
    Object? value0,
  ) => Presentation.template("Live window · {value0} remaining", {
    'value0': value0,
  });
  static String seasonBeginsInTimeUntilSeasonStartsAtMicros(Object? value0) =>
      Presentation.template("Begins in {value0}", {'value0': value0});
  static const seasonClaimThisSharedSlot = "Claim this shared slot";
  static String
  seasonSeasonalRouteCompactMicrosProgressCompactMicrosBindingTargetMicr(
    Object? value0,
    Object? value1,
  ) => Presentation.template("Seasonal route: {value0} / {value1} new R", {
    'value0': value0,
    'value1': value1,
  });
  static const seasonAddSeasonalRoute = "Add seasonal route";
  static const seasonR = " R";
  static String seasonHarborRouteContractKindRestoreCompactMicrosMainProgress(
    Object? value0,
    Object? value1,
    Object? value2,
  ) => Presentation.template("Harbor route: {value0} / {value1}{value2}", {
    'value0': value0,
    'value1': value1,
    'value2': value2,
  });
  static const seasonNotesXPToTheSelectedPass =
      "10 Notes + 250 XP to the selected pass";
  static const seasonThisSharedSlotIsComplete = "This shared slot is complete.";
  static const seasonReadAnArchiveAccount = "Read an archive account";
  static const seasonChartAPassage = "Chart a passage";
  static const seasonStudyAConstellation = "Study a constellation";
  static const seasonBuildYourHarbor = "Build your harbor";
  static const seasonRestoreRadiance = "Restore Radiance";
  static String seasonAgeDaysAgo(Object? value0) =>
      Presentation.template("{value0} days ago", {'value0': value0});
  static const seasonYesterday = "Yesterday";
  static const seasonToday = "Today";
  static const seasonNewSeasonalProductionCountsOnlyAfterAssignment =
      "New seasonal production counts only after assignment. The original harbor objective stays available; claiming either route completes this same slot once.";
  static const seasonPremiumOwnershipIsNotCurrentlyVerifiedReview =
      "Premium ownership is not currently verified. Review collection and store status for available offers or restoration. This preview grants no ownership or game power.";
  static String seasonPremiumOwnershipIsVerifiedEarnLevelValue(
    Object? value0,
  ) => Presentation.template(
    "Premium ownership is verified. Earn level {value0} to add this appearance to your collection.",
    {'value0': value0},
  );
  static const seasonAvailableInYourHarborCollectionThisLevel =
      "Available in your harbor collection: this level is earned and premium ownership is verified.";
  static const seasonPurchasingAndPremiumDeliveryAreUnavailableIn =
      "Purchasing and premium delivery are unavailable in this build. This preview grants no ownership or game power.";
  static const seasonPREMIUMAPPEARANCEPREVIEW = "PREMIUM APPEARANCE · PREVIEW";
  static const seasonPREMIUMAPPEARANCEAVAILABLE =
      "PREMIUM APPEARANCE · AVAILABLE";
  static String seasonKeepFreeFreeKindCosmeticAppearanceAccount(
    Object? value0,
  ) => Presentation.template("Keep free {value0}", {'value0': value0});
  static const seasonCollectedFree = "Collected · free";
  static String seasonCollectThisAccountAtLevelValueTo(
    Object? value0,
  ) => Presentation.template(
    "Collect this account at level {value0} to read the next part of the watchkeeper’s record.",
    {'value0': value0},
  );
  static String seasonValueXP(Object? value0) =>
      Presentation.template("{value0} XP", {'value0': value0});
  static const seasonReadyToCollect = "Ready to collect";
  static const seasonKeptInYourCollection = "Kept in your collection";
  static String seasonLevelValueFreeTitle(Object? value0, Object? value1) =>
      Presentation.template("Level {value0} · {value1}", {
        'value0': value0,
        'value1': value1,
      });
  static const seasonCollectionAndStoreStatus = "Collection and store status";
  static const seasonTenFreeAppearancesAndTwentyReadableAccounts =
      "Ten free appearances and twenty readable accounts. Ten premium appearances are previewed at every third level.";
  static const seasonFREETRACKLEVELS = "FREE TRACK · 30 LEVELS";
  static const seasonMainAndSeasonalObjectivesShareTheSame =
      "Main and seasonal objectives share the same daily slots: 250 XP and 10 Notes once per completed slot. This pass stays available after the season ends.";
  static const seasonSelectThisPass = "Select this pass";
  static const seasonSelectedForFutureContractXP =
      "Selected for future contract XP";
  static String seasonXpXPXPPerLevel(Object? value0) => Presentation.template(
    "{value0} XP · 500 XP per level",
    {'value0': value0},
  );
  static String seasonLevelLevel(Object? value0) =>
      Presentation.template("Level {value0} / 30", {'value0': value0});
  static const seasonAPersonalKeepsakeNoEconomicReward =
      "A personal keepsake. No economic reward.";
  static const seasonKeepPersonalBadge = "Keep personal badge";
  static const seasonBadgeKept = "Badge kept";
  static String
  seasonCompactMicrosSeasonFleetLifetimeMicrosCompactMicrosValueLifetime(
    Object? value0,
    Object? value1,
  ) => Presentation.template("{value0} / {value1} lifetime seasonal R", {
    'value0': value0,
    'value1': value1,
  });
  static String seasonBuildMaxMax(Object? value0) =>
      Presentation.template("Build max · {value0}", {'value0': value0});
  static String seasonBuildCompactMicrosPriceR(Object? value0) =>
      Presentation.template("Build 1 · {value0} R", {'value0': value0});
  static String seasonNeedsTideglassEngineProducerNamesTier(Object? value0) =>
      Presentation.template("Needs 10 {value0}", {'value0': value0});
  static String seasonTideglassEngineProducerNamesTierNSeasonFleetCounts(
    Object? value0,
    Object? value1,
  ) => Presentation.template("{value0}\n{value1} at work", {
    'value0': value0,
    'value1': value1,
  });
  static const seasonPersonalBearings = "Personal bearings";
  static String seasonCurrentLoomLinkGameSeasonEngineSynergyMultiplierSeason(
    Object? value0,
    Object? value1,
  ) => Presentation.template(
    "Current Loom link: {value0}×\nCurrent Dawn link: {value1}×",
    {'value0': value0, 'value1': value1},
  );
  static const seasonNurseries = "Nurseries";
  static const seasonSkiffs = "Skiffs";
  static const seasonDawn = "Dawn";
  static const seasonLoom = "Loom";
  static const seasonSource = "Source";
  static const seasonConnectionsWorkFromTheFirstSkiffEach =
      "Connections work from the first Skiff. Each column adds both source effects: coefficient × log₂(1 + source count / 25).";
  static const seasonTheReturningStarNetwork = "The returning-star network";
  static String seasonMoveTideglassEngineProducerNamesSeasonPriorityILater(
    Object? value0,
  ) => Presentation.template("Move {value0} later", {'value0': value0});
  static String seasonMoveTideglassEngineProducerNamesSeasonPriorityIEarlier(
    Object? value0,
  ) => Presentation.template("Move {value0} earlier", {'value0': value0});
  static const seasonBestPaybackWaitsForTheMostEfficient =
      "Best payback waits for the most efficient purchase. Tier priority waits for the first unlocked tier in your order.";
  static const seasonTierPriority = "Tier priority";
  static const seasonBestPayback = "Best payback";
  static const seasonPurchaseApproach = "Purchase approach";
  static const seasonFreeAutomationForThisSeparateFleet =
      "Free automation for this separate fleet.";
  static const seasonLetTheCrewBuild = "Let the crew build";
  static const seasonThisFleetKeepsItsOwnRadianceAnd =
      "This fleet keeps its own Radiance and production. Your main harbor continues independently. No Charts, Focus, Support or purchases increase its power.";
  static const seasonPausedPotential = "Paused · potential ";
  static String seasonSeasonCanPlayPausedPotentialCompactFixedGameSeasonEngine(
    Object? value0,
    Object? value1,
  ) => Presentation.template("{value0}{value1} R/s", {
    'value0': value0,
    'value1': value1,
  });
  static String seasonCompactMicrosSeasonFleetWalletMicrosR(Object? value0) =>
      Presentation.template("{value0} R", {'value0': value0});
  static const seasonSEASONALRADIANCE = "SEASONAL RADIANCE";
  static const seasonResumeArchivedFleetFree = "Resume archived fleet · free";
  static const seasonPauseArchivedFleet = "Pause archived fleet";
  static const seasonLocalPreviewSchedule = " · local preview schedule";
  static String seasonUtcDateSeasonStartsAtMicrosUtcDateSeasonEndsAtMicrosUTC(
    Object? value0,
    Object? value1,
    Object? value2,
  ) => Presentation.template("{value0} — {value1} UTC\n28 days{value2}", {
    'value0': value0,
    'value1': value1,
    'value2': value2,
  });
  static const seasonContracts = "Contracts";
  static const seasonPass = "Pass";
  static const seasonFleet = "Fleet";
  static const seasonThisSeasonalCatalogueIsNotAvailable =
      "This seasonal catalogue is not available.";
  static const seasonReturningStars = "Returning stars";
  static const storyKeepCurrentProgress = "Keep current progress";
  static const storyThisActionIsNotAvailableYet =
      "This action is not available yet.";
  static const storyYourHarborHasBeenUpdated = "Your harbor has been updated.";
  static const storyKeepDecorationNotes = "Keep decoration · 50 Notes";
  static const storyEquipDecoration = "Equip decoration";
  static const storyEquipped = "Equipped";
  static const storyReturningComets = "Returning comets";
  static const storyShoreGarden = "Shore garden";
  static const storyTideRings = "Tide rings";
  static const storyAuroraKite = "Aurora kite";
  static const storyGlassBuoys = "Glass buoys";
  static const storyBeaconPennants = "Beacon pennants";
  static const storyShowTheUndecoratedHarbor = "Show the undecorated harbor";
  static const storySixOptionalDecorationsSurveyNotesEachPurely =
      "Six optional decorations, 50 Survey Notes each. Purely visual: they never change production, prestige or storage.";
  static const storyMakeTheHarborYours = "Make the harbor yours";
  static const storyClosePassage = "Close passage";
  static const storyTheCurrentPassageFleetAndUnfinishedProgress =
      "The current passage fleet and unfinished progress will be discarded. Dossier ownership and recorded completion remain. You can use Back to visit your harbor while keeping this passage active.";
  static const storyCloseThisPassage2 = "Close this passage?";
  static const storyRestartFleet = "Restart fleet";
  static const storyTheCurrentPassageRadianceAndFleetWill =
      "The current passage Radiance and fleet will be rebuilt. Ownership, recorded completion and your main harbor remain. Replaying costs no Notes.";
  static const storyRestartThisPassageFleet = "Restart this passage fleet?";
  static const storyBuild = "Build 1";
  static const storyCrewPurchase = "Crew purchase";
  static String
  storyEconomyDefinitionAutomaticOnlyCrewPurchaseBuildCompactMicros(
    Object? value0,
    Object? value1,
  ) => Presentation.template("{value0} · {value1} R", {
    'value0': value0,
    'value1': value1,
  });
  static String storyNeedsTideglassEngineProducerNamesTier(Object? value0) =>
      Presentation.template("Needs 10 {value0}", {'value0': value0});
  static const storyBerthLimitReached = "Berth limit reached";
  static String storyTideglassEngineProducerNamesTierNRunFleetCounts(
    Object? value0,
    Object? value1,
    Object? value2,
  ) => Presentation.template("{value0}\n{value1}{value2} at work", {
    'value0': value0,
    'value1': value1,
    'value2': value2,
  });
  static const storyCloseThisPassage = "Close this passage";
  static const storyRestartFleetFree = "Restart fleet · free";
  static const storyNurseries = "Nurseries";
  static const storySkiffs = "Skiffs";
  static const storyDawn = "Dawn";
  static const storyLoom = "Loom";
  static const storySource = "Source";
  static const storyThisPassageHasNoCrossTierMultipliers =
      "This passage has no cross-tier multipliers. Its berth limits shape the fleet.";
  static const storyTheseCrossTierLinksApplyFromThe =
      "These cross-tier links apply from the start. Each coefficient multiplies log₂(1 + source count / 25).";
  static const storyPassageNetworkRules = "Passage network rules";
  static String storyMoveTideglassEngineProducerNamesRunPriorityILater(
    Object? value0,
  ) => Presentation.template("Move {value0} later", {'value0': value0});
  static String storyMoveTideglassEngineProducerNamesRunPriorityIEarlier(
    Object? value0,
  ) => Presentation.template("Move {value0} earlier", {'value0': value0});
  static const storyBestPaybackWaitsForTheMostEfficient =
      "Best payback waits for the most efficient purchase. Tier priority waits for the first unlocked tier in your order.";
  static const storyTierPriority = "Tier priority";
  static const storyBestPayback = "Best payback";
  static const storyPurchaseApproach = "Purchase approach";
  static const storyPauseThePlanToMakePurchasesYourself =
      "Pause the plan to make purchases yourself.";
  static const storyLetThePassageCrewBuild = "Let the passage crew build";
  static const storyChooseThePlanTheyFollowBelow =
      "Choose the plan they follow below.";
  static const storyThePassageCrewBuildsAutomatically =
      "The passage crew builds automatically";
  static const storyYouCanReturnToTheHarborWithout =
      "You can return to the harbor without closing this passage. Both fleets continue working.";
  static const storyPassageChartedItsDiscoveryIsKeptIn =
      "Passage charted. Its discovery is kept in your restoration.";
  static String
  storyCompactMicrosRunFleetLifetimeMicrosCompactMicrosDefinitionGoalMic(
    Object? value0,
    Object? value1,
  ) => Presentation.template("{value0} / {value1} lifetime Radiance", {
    'value0': value0,
    'value1': value1,
  });
  static String storyCompactFixedEconomyOutputPerSecondRunFleetRS(
    Object? value0,
  ) => Presentation.template("+{value0} R/s", {'value0': value0});
  static String storyCompactMicrosRunFleetWalletMicrosR(Object? value0) =>
      Presentation.template("{value0} R", {'value0': value0});
  static const storyPASSAGEFLEET = "PASSAGE FLEET";
  static const storyOpenDossier = "Open dossier";
  static const storyReplaceAndOpen = "Replace and open";
  static const storySpendSurveyNotesToKeepThisDossier =
      "Spend 100 Survey Notes to keep this dossier permanently. Replays are free.";
  static const storyThisDossierIsAlreadyYoursOpeningIt =
      "This dossier is already yours. Opening it is free.";
  static const storyYourCurrentPassageFleetAndItsUnfinished =
      " Your current passage fleet and its unfinished progress will be replaced; its ownership and recorded completion remain.";
  static String storyOwnedThisDossierIsAlreadyYoursOpening(
    Object? value0,
    Object? value1,
  ) => Presentation.template(
    "{value0}{value1} Your main harbor is unchanged.",
    {'value0': value0, 'value1': value1},
  );
  static String storyOpenDefinitionTitle(Object? value0) =>
      Presentation.template("Open {value0}?", {'value0': value0});
  static const storyReplaceTheActivePassage = "Replace the active passage?";
  static const storyChartedReplayWheneverYouLike =
      "Charted · replay whenever you like";
  static const storyOpenDossierNotes = "Open dossier · 100 Notes";
  static const storyOpenOwnedDossierFree = "Open owned dossier · free";
  static const storyYourActivePassage = "Your active passage";
  static String
  storyGoalCompactMicrosDefinitionGoalMicrosLifetimePassageRadiance(
    Object? value0,
  ) => Presentation.template("Goal: {value0} lifetime passage Radiance", {
    'value0': value0,
  });
  static const storyFinishTheQuietWatchChapterToOpen =
      "Finish The Quiet Watch, chapter 3, to open passages. Each dossier then costs 100 Survey Notes once. Replays are free.";
  static const storyEachDossierOpensASeparateFleetYour =
      "Each dossier opens a separate fleet. Your main harbor keeps earning. Main Radiance, Charts and boosts stay at home; passage progress returns as discoveries, never money.";
  static String storyGameStateSurveyNotesSurveyNotesCollectionCompleted(
    Object? value0,
    Object? value1,
  ) => Presentation.template("{value0} Survey Notes · {value1} / 12 charted", {
    'value0': value0,
    'value1': value1,
  });
  static const storyPassagesBeyondTheHarbor = "Passages beyond the harbor";
  static String storyRestoresWithChapterIntParseEntryChapter(Object? value0) =>
      Presentation.template("Restores with chapter {value0}", {
        'value0': value0,
      });
  static const storyReflectOnThisAccount = "Reflect on this account";
  static String storyGameStoryCampaignArchiveIdsLengthOfAccounts(
    Object? value0,
  ) => Presentation.template("{value0} of 18 accounts recovered", {
    'value0': value0,
  });
  static const storyTheKeeperSArchive = "The keeper’s archive";
  static String storyLabelTargetAchieved(Object? value0, Object? value1) =>
      Presentation.template("{value0} · {value1} · achieved", {
        'value0': value0,
        'value1': value1,
      });
  static const storyDistinctCalibrationPatterns =
      "Distinct calibration patterns";
  static const storySurveysCollected = "Surveys collected";
  static const storyPermanentCharts = "Permanent Charts";
  static const storyRechartsCompleted = "Recharts completed";
  static String storyPassagesFamilyLabelsGoalFamily(Object? value0) =>
      Presentation.template("Passages: {value0}", {'value0': value0});
  static String storyTideglassEngineProducerNamesTierInYourCurrentFleet(
    Object? value0,
  ) => Presentation.template("{value0} in your current fleet", {
    'value0': value0,
  });
  static const storyKeepsakeARestoredSkyThreeArchiveEntries =
      "Keepsake: a restored sky, three archive entries and a permanent chapter badge. No production boost.";
  static String storyCompleteChapterIndexFirst(Object? value0) =>
      Presentation.template("Complete chapter {value0} first", {
        'value0': value0,
      });
  static const storyYourCurrentChapter = "Your current chapter";
  static const storyRestored = "Restored";
  static const storyKeepCharting = "Keep charting";
  static const storyTheHarborRemembers = "The Harbor Remembers";
  static const storyAPermanentRecordOfWhatYouDiscover =
      "A permanent record of what you discover. Recharting never darkens a restored constellation.";
  static String storyCampaignRestoredHarborOfConstellationsRestored(
    Object? value0,
  ) => Presentation.template("{value0} of 6 constellations restored", {
    'value0': value0,
  });
  static const storyTheRestorationCatalogueCouldNotBeLoaded =
      "The restoration catalogue could not be loaded.";
  static const storyDecorations = "Decorations";
  static const storyArchive = "Archive";
  static const storyPassages = "Passages";
  static const storyChapters = "Chapters";
  static const storyTheRestoration = "The restoration";
  static const storyPlansForTheTide = "Plans for the tide";
  static const storyDifferentConnections = "Different connections";
  static const storyASmallerFleet = "A smaller fleet";
  static const supportSupportChangesMainHarborProductionOnlyChallenges =
      "Support changes main-harbor production only. Challenges and seasonal fleets keep their own rules.";
  static const supportUseTokenMatchThisSlice = "Use 1 token · match this slice";
  static String supportSliceICompactMicrosGameEngineSalvageBonusMicrosCaches(
    Object? value0,
    Object? value1,
  ) => Presentation.template("Slice {value0} · {value1} R", {
    'value0': value0,
    'value1': value1,
  });
  static const supportNoUnclaimedSliceIsAvailableReturnAfter =
      "No unclaimed slice is available. Return after at least five minutes away to form a cache.";
  static const supportYourSixLatestCompleteFiveMinuteSlices =
      "Your six latest complete five-minute slices of credited time away are retained. A token matches a slice’s unboosted earnings, capped at five minutes of the unboosted rate when that return was settled. Later building cannot enlarge the reward. Partial slices are not kept.";
  static const supportSalvageCache = "Salvage cache";
  static const supportUseTokenForMinutes = "Use 1 token · +25% for 20 minutes";
  static String supportSupportRemainingMicrosBigIntFromToStringSecondsOf(
    Object? value0,
  ) => Presentation.template("{value0} seconds of Support remaining", {
    'value0': value0,
  });
  static const supportProductionForMinutesPerTokenRepeatingQueues =
      "+25% production for 20 minutes per token. Repeating queues time. With Focus, the combined bonus is +45%.";
  static const supportSteadyTheLight = "Steady the light";
  static const supportUnusedTokensExpireAtYourFixedAccount =
      "Unused tokens expire at your fixed account-day boundary. A boost already queued keeps its remaining real time, including through Rechart.";
  static const supportOptionalAdTheSameToken = "Optional ad · the same 1 token";
  static const supportReadACrewBriefing = "Read a crew briefing";
  static const supportAllSixSlotsUsedToday = "All six slots used today";
  static String supportSlotsLengthOfSlotsUsedAvailableTokenNull(
    Object? value0,
    Object? value1,
  ) => Presentation.template(
    "{value0} of 6 slots used · {value1} unspent tokens",
    {'value0': value0, 'value1': value1},
  );
  static const supportSixSharedSlotsEachAccountDayA =
      "Six shared slots each account day. A crew briefing grants one token. Spend it on a short boost or a genuine salvage slice. Neither is needed to finish the restoration.";
  static const supportALittleHelpFreelyAvailable =
      "A little help, freely available";
  static const supportCrewSupport = "Crew Support";
  static const supportCompleteBriefing = "Complete briefing";
  static const supportLater = "Later";
  static String supportCopyNNCompletingThisBriefingUsesOne(
    Object? value0,
  ) => Presentation.template(
    "{value0}\n\nCompleting this briefing uses one of today’s six shared Support slots. The token expires at your account-day boundary.",
    {'value0': value0},
  );
  static const supportSupportIsOptionalItsAllowanceHasNo =
      "Support is optional. Its allowance has no streak, paid refill or catch-up penalty. Focus and Support add together: +20% and +25% give +45%.";
  static const supportKeepTheWatchGentle = "Keep the watch gentle";
  static const supportChallengeDossiersUseTheirOwnFleetsYour =
      "Challenge dossiers use their own fleets. Your main harbor keeps working. Notes open a dossier once; replaying it is free.";
  static const supportADifferentPassage = "A different passage";
  static const supportTheCrewCanBuyForTheBest =
      "The crew can buy for the best payback or follow your tier priorities. A saved plan does no work until you choose it and enable automatic building.";
  static const supportAPlanYouCanChange = "A plan you can change";
  static const supportRechartRebuildsYourFleetAndKeepsLifetime =
      "Rechart rebuilds your fleet and keeps lifetime earnings, Charts, Notes and your discoveries. Preview the gain before choosing to start again.";
  static const supportAChartRemembers = "A chart remembers";
  static const supportAtChartsSkiffsAndNurseriesStrengthenYour =
      "At 25 Charts, Skiffs and Nurseries strengthen your Looms and Observatories. The smallest craft can still be worth building.";
  static const supportTheOldCraftMatter = "The old craft matter";
  static const supportYourFleetWorksWhileYouAreAway =
      "Your fleet works while you are away. The first 24 hours keep full production, followed by 48 hours at one quarter. A longer break does not erase your harbor.";
  static const supportAPatientHarbor = "A patient harbor";
  static String audioValueRoundPercent2(Object? value0) =>
      Presentation.template("{value0} percent", {'value0': value0});
  static const audioSoundEffectsVolume = "Sound effects volume";
  static const audioActionsAndDiscoveries = "Actions and discoveries";
  static const audioSoundEffects = "Sound effects";
  static String audioValueRoundPercent(Object? value0) =>
      Presentation.template("{value0} percent", {'value0': value0});
  static const audioMusicVolume = "Music volume";
  static const audioQuietHarborThemes = "Quiet harbor themes";
  static const audioMusic = "Music";
  static const audioMuteAllSound = "Mute all sound";
  static const calibrationFINISH = "FINISH";
  static const calibrationSTART = "START";
  static String calibrationWidgetFocusChargesFocusChargesAvailableNoTimer(
    Object? value0,
  ) => Presentation.template(
    "{value0} Focus charges available. No timer. No penalty for trying.",
    {'value0': value0},
  );
  static const calibrationLetTheCrewHelp = "Let the crew help";
  static const calibrationCollectPatternFocus = "Collect pattern · 1 Focus";
  static const calibrationConstellationCollected = "Constellation collected";
  static const calibrationRestart = "Restart";
  static const calibrationUndo = "Undo";
  static const calibrationChooseTheNextConnectedStar =
      "Choose the next connected star:";
  static const calibrationThisRouteHasNoNextStarUndo =
      "This route has no next star. Undo a step or begin again.";
  static const calibrationTheConstellationIsAligned =
      "The constellation is aligned.";
  static String calibrationPatternTitleRouteVisitedLengthOfPattern(
    Object? value0,
    Object? value1,
    Object? value2,
    Object? value3,
  ) => Presentation.template(
    "{value0}. {value1} of {value2} stars connected. Current star: {value3}.",
    {'value0': value0, 'value1': value1, 'value2': value2, 'value3': value3},
  );
  static const calibrationAQuieterWayToBrightenTheSky =
      "A quieter way to brighten the sky.";
  static const calibrationConstellationCalibration =
      "Constellation calibration";
  static const calibrationNoFocusChargeIsAvailableYetYour =
      "No Focus charge is available yet. Your route is saved on this screen.";
  static const calibrationPatternCollectedTenMinutesOfFocusAdded =
      "Pattern collected. Ten minutes of Focus added.";
  static const dailyCreateAPlanInAnEmptySlot = "Create a plan in an empty slot";
  static const dailyNewPlan = "New plan";
  static String dailyBuyAPlanSlotNotesGameState(Object? value0) =>
      Presentation.template("Buy a plan slot · 50 Notes ({value0}/6 owned)", {
        'value0': value0,
      });
  static const dailyANewPlanSlotIsAvailable = "A new plan slot is available.";
  static const dailySaveAndSelectPlan = "Save and select plan";
  static const dailyTheseAreYourChosenConditionsNotA =
      "These are your chosen conditions, not a prediction of the best possible reset time.";
  static const dailyMinimumRunLengthInSeconds = "Minimum run length in seconds";
  static const dailyMinimumNewChartsPerRechart =
      "Minimum new Charts per Rechart";
  static const dailyRebuildOnlyWhenBothLimitsBelowAre =
      "Rebuild only when both limits below are met. Existing fleet and wallet are spent at every reset.";
  static const dailyUnlocksAtCharts = "Unlocks at 100 Charts.";
  static const dailyAutomaticallyRechart = "Automatically Rechart";
  static const dailyMoveLater = "Move later";
  static const dailyMoveEarlier = "Move earlier";
  static const dailyBestPaybackWaitsForTheMostEfficient =
      "Best payback waits for the most efficient next purchase. Tier priority waits for the first unlocked tier in your list; it can favor a longer-term route.";
  static const dailyTierPriority = "Tier priority";
  static const dailyBestMarginalPayback = "Best marginal payback";
  static const dailyBuyingPolicy = "Buying policy";
  static const dailyPlanName = "Plan name";
  static const dailySavedPlan = "Saved plan";
  static const dailyOneFreePlanExtraSavedPlansCost =
      "One free plan. Extra saved plans cost 50 Notes each, up to five. Plans work while you are away.";
  static const dailyTheCrewSPlan = "The crew’s plan";
  static const dailyThisPlanCouldNotBeSavedCheck =
      "This plan could not be saved. Check the Chart unlock and available plan slots.";
  static const dailyPlanSavedAndSelectedAutomaticRebuildingRemains =
      "Plan saved and selected. Automatic rebuilding remains your separate choice in the harbor.";
  static const dailyChooseANameAtLeastOneNew =
      "Choose a name, at least one new Chart, and a run of at least one second.";
  static const dailyRerollOnce = "Reroll once";
  static const dailyClaimNotesXP = "Claim 10 Notes + 250 XP";
  static String dailyAgeDInTheBacklog(Object? value0) =>
      Presentation.template("{value0}d in the backlog", {'value0': value0});
  static const dailyToday = "Today";
  static String dailyCompactMicrosProgressCompactMicrosContractTargetR(
    Object? value0,
    Object? value1,
  ) => Presentation.template("{value0} / {value1} R", {
    'value0': value0,
    'value1': value1,
  });
  static const dailyArchiveEntry = "archive entry";
  static String
  dailyExploreOneSwitchContractDiscoveryKindCalibrationConstellation(
    Object? value0,
  ) => Presentation.template("Explore one {value0}", {'value0': value0});
  static String dailyBuildContractTargetLightkeepers(Object? value0) =>
      Presentation.template("Build {value0} lightkeepers", {'value0': value0});
  static String dailyGatherCompactMicrosContractTargetRadiance(
    Object? value0,
  ) => Presentation.template("Gather {value0} Radiance", {'value0': value0});
  static String dailyAccountDayUsesAFixedUTCGame(
    Object? value0,
    Object? value1,
  ) => Presentation.template(
    "Account day uses a fixed UTC{value0}{value1} offset. Traveling will not reset the allowance.",
    {'value0': value0, 'value1': value1},
  );
  static const dailyAllRetainedContractsAreCompleteTheHarbor =
      "All retained contracts are complete. The harbor has no streak to protect.";
  static String dailyGameStateDailyContractsWhereCCClaimed(
    Object? value0,
    Object? value1,
  ) => Presentation.template(
    "{value0} claimed · {value1} XP toward the selected pass",
    {'value0': value0, 'value1': value1},
  );
  static const dailyThreeEachAccountDayKeptForSeven =
      "Three each account day, kept for seven days. Targets stay fixed. Each completed contract grants 10 Notes and 250 pass XP.";
  static const dailyCrewContracts = "Crew contracts";
  static const dailyTheConstellationChartsCouldNotBeOpened =
      "The constellation charts could not be opened. Your Focus has been kept.";
  static const appRetry = "Retry";
  static String appNumberReportEarnedMicrosR(Object? value0) =>
      Presentation.template("+{value0} R", {'value0': value0});
  static String appCollectGameStateCompletedSurveysNotes(Object? value0) =>
      Presentation.template("Collect {value0} Notes", {'value0': value0});
  static String appFocusedForDurationLabelDurationMicrosecondsGameState(
    Object? value0,
  ) => Presentation.template("Focused for {value0}", {'value0': value0});
  static const appReflectOnThisEntry = "Reflect on this entry";
  static const appAnArchiveInteractionRecordedForYourCrew =
      "An archive interaction recorded for your crew contracts.";
  static const appEditTheCrewSAutomationPlan =
      "Edit the crew’s automation plan";
  static const appAccountCloudSaves = "Account & cloud saves";
  static const appHarborAppearances = "Harbor appearances";
  static const appCrewSupport = "Crew support";
  static String appRestorationGameStoryCampaignRestoredHarbor(Object? value0) =>
      Presentation.template("Restoration · {value0} / 6", {'value0': value0});
  static String appPermanentPowerGameEnginePrestigeMultiplierGameState(
    Object? value0,
    Object? value1,
  ) => Presentation.template("Permanent power: {value0}× → {value1}×", {
    'value0': value0,
    'value1': value1,
  });
  static String appClaimClaimNewCharts(Object? value0) =>
      Presentation.template("Claim {value0} new Charts", {'value0': value0});
  static String appPreviewRechartClaimCharts(Object? value0) =>
      Presentation.template("Preview Rechart · +{value0} Charts", {
        'value0': value0,
      });
  static String appNumberGameStateLifetimeMicrosR(Object? value0) =>
      Presentation.template("{value0} R", {'value0': value0});
  static String appGameStateChartsCharts(Object? value0) =>
      Presentation.template("{value0} Charts", {'value0': value0});
  static String appNeedsTideglassEngineProducerNamesTier(Object? value0) =>
      Presentation.template("Needs 10 {value0}", {'value0': value0});
  static String appBuildQuantity(Object? value0) =>
      Presentation.template("Build {value0}", {'value0': value0});
  static String appReadyInDurationLabelForecast(Object? value0) =>
      Presentation.template("Ready in {value0}", {'value0': value0});
  static String appRateGameEngineMarginalOutputPerSecondSTierQuantity(
    Object? value0,
  ) => Presentation.template("+{value0} network R/s", {'value0': value0});
  static String appNumberGamePriceForTierR(Object? value0) =>
      Presentation.template("{value0} R", {'value0': value0});
  static String appNextMilestoneLightkeepersDoubleThisTier(Object? value0) =>
      Presentation.template("{value0} lightkeepers → double this tier", {
        'value0': value0,
      });
  static String appSCountsTierAtWorkRateGame(Object? value0, Object? value1) =>
      Presentation.template("{value0} at work · {value1} R/s", {
        'value0': value0,
        'value1': value1,
      });
  static const appMilestone = "Milestone";
  static const appTryAgain = "Try again";
  static const appGatheringYourTimeAway = "Gathering your time away…";
  static const bootstrapUseThisRecoveryCopy = "Use this recovery copy";
  static const bootstrapRecovering = "Recovering…";
  static const bootstrapRecoverySelectsTheExportedProgressExistingReadable =
      "Recovery selects the exported progress. Existing readable progress is archived; damaged files are retained for recovery. Purchases require separate verified restoration.";
  static const bootstrapPasteYourCompleteRecoveryCopyHere =
      "Paste your complete recovery copy here";
  static const bootstrapPreviouslyExportedHarbor = "Previously exported harbor";
  static const bootstrapTryOpeningAgain = "Try opening again";
  static const bootstrapKeepYourHarborSafe = "Keep your harbor safe";
  static String bootstrapThisRecoveryCopyCouldNotBeUsed(
    Object? value0,
  ) => Presentation.template(
    "This recovery copy could not be used ({value0}). Your current files have been kept.",
    {'value0': value0},
  );
  static const bootstrapYourPreviousSaveStaysSafeUntilAll =
      "Your previous save stays safe until all progress is ready.";
  static String bootstrapGatheringYourTimeAwayReplayProgressFractionFloor(
    Object? value0,
  ) => Presentation.template("Gathering your time away… {value0}%", {
    'value0': value0,
  });
  static const bootstrapOpeningYourHarbor = "Opening your harbor…";
  static const bootstrapTideglass = "Tideglass";
  static String bootstrapYourHarborCouldNotBeOpenedError(
    Object? value0,
  ) => Presentation.template(
    "Your harbor could not be opened ({value0}). Its saved files have been preserved.",
    {'value0': value0},
  );
  static const bootstrapNeitherSavedCopyCouldBeOpenedYour =
      "Neither saved copy could be opened. Your files have been preserved. You can recover from a previously exported copy.";
  static const bootstrapTwoDifferentSavedHarborsNeedToBe =
      "Two different saved harbors need to be reconciled. Both copies have been preserved.";
  static const bootstrapThisHarborNeedsACompatibleGameVersion =
      "This harbor needs a compatible game version. Its saved files have been preserved.";
  static const bootstrapTheLatestCopyCouldNotBeRead =
      "The latest copy could not be read. Your previous saved harbor was recovered; its time away has been settled.";
  static String bootstrapDirectoryPathAudioPreferencesJson(Object? value0) =>
      Presentation.template("{value0}/audio-preferences.json", {
        'value0': value0,
      });
  static String bootstrapAwaitGetApplicationSupportDirectoryPathTideglass(
    Object? value0,
  ) => Presentation.template("{value0}/tideglass", {'value0': value0});
  static const bootstrapTIDEGLASSREWARDEDADS = "TIDEGLASS_REWARDED_ADS";
  static const bootstrapTIDEGLASSCOMMERCE = "TIDEGLASS_COMMERCE";
  static const bootstrapTIDEGLASSREWARDEDADUNIT = "TIDEGLASS_REWARDED_AD_UNIT";
  static const bootstrapTIDEGLASSLOCALSERVICE = "TIDEGLASS_LOCAL_SERVICE";
  static const bootstrapTIDEGLASSSERVICEURL = "TIDEGLASS_SERVICE_URL";
  static String gameYourHarborIsStillOpenButIts(
    Object? value0,
  ) => Presentation.template(
    "Your harbor is still open, but its latest progress could not be written. {value0}",
    {'value0': value0},
  );
  static const gameTheOriginalHarborAppearanceIsRestored =
      "The original harbor appearance is restored.";
  static const gameHarborDecorationChanged = "Harbor decoration changed.";
  static const gameANewDecorationForYourHarborProduction =
      "A new decoration for your harbor. Production is unchanged.";
  static const gameCosmeticCoreDecoration =
      "^cosmetic\\.core\\.decoration\\.0[1-6]\$";
  static const gameChallengePlanUpdated = "Challenge plan updated.";
  static const gameAVesselJoinsTheChallengeFleet =
      "A vessel joins the challenge fleet.";
  static const gameAFreshChallengeFleetReplaysCostNo =
      "A fresh challenge fleet. Replays cost no Notes.";
  static const gameReturnedToTheHarborDossierOwnershipAnd =
      "Returned to the harbor. Dossier ownership and completion are kept.";
  static const gameASeparateFleetIsReadyYourHarbor =
      "A separate fleet is ready. Your harbor continues its work.";
  static const gameAnEarnedPassRewardIsAddedTo =
      "An earned pass reward is added to your collection.";
  static const gameTheSharedContractGrantsNotesAndXP =
      "The shared contract grants 10 Notes and 250 XP once.";
  static const gameThisContractCanAlsoBeCompletedWith =
      "This contract can also be completed with new seasonal production.";
  static const gameFutureContractXPGoesToThisSelected =
      "Future contract XP goes to this selected pass.";
  static const gameASeasonalBadgeHasBeenRecorded =
      "A seasonal badge has been recorded.";
  static const gameArchivedFleetPaused = "Archived fleet paused.";
  static const gameTheArchivedFleetContinuesAtItsOwn =
      "The archived fleet continues at its own pace.";
  static const gameSeasonalPlanUpdated = "Seasonal plan updated.";
  static const gameTheSeasonalFleetGrows = "The seasonal fleet grows.";
  static const gameAGenuineFiveMinuteSalvageSliceHas =
      "A genuine five-minute salvage slice has been matched.";
  static const gameTwentyMinutesOfSupportQueuedAt =
      "Twenty minutes of Support queued at +25%.";
  static const gameOneVerifiedSupportTokenIsReadyFor =
      "One verified Support token is ready for this account day.";
  static const gameOneSupportTokenIsReadyForThis =
      "One Support token is ready for this account day.";
  static const gameAnAdditionalPlanSlotIsReady =
      "An additional plan slot is ready.";
  static const gameTheCrewWillFollowTheSelectedPlan =
      "The crew will follow the selected plan.";
  static const gameYourCrewSPlanIsSaved = "Your crew’s plan is saved.";
  static const gameTheKeeperSAccountIsRecordedIn =
      "The keeper’s account is recorded in your logbook.";
  static const gameANewObjectiveWithTheOriginalDifficulty =
      "A new objective, with the original difficulty snapshot.";
  static const gameContractCompleteNotesAndPassXP2 =
      "Contract complete: 10 Notes and 250 pass XP.";
  static const gameContractCompleteNotesAndPassXP =
      "Contract complete: 10 Notes and 250 pass XP.";
  static const gameAConstellationRecordedTenMinutesOfFocus =
      "A constellation recorded. Ten minutes of Focus queued.";
  static const gameSurveyNotesAddedToYourArchive =
      "Survey Notes added to your archive.";
  static const gameYourConstellationIsFocusedForTenMore =
      "Your constellation is focused for ten more minutes.";
  static const gameAutomaticBuildingPaused = "Automatic building paused.";
  static const gameYourFleetIsBuildingAutomatically =
      "Your fleet is building automatically.";
  static const gameANewChartABrighterBeginning =
      "A new chart. A brighter beginning.";
  static String gameANewTideglassEngineProducerNamesTierJoinsYour(
    Object? value0,
  ) => Presentation.template("A new {value0} joins your harbor.", {
    'value0': value0,
  });
  static const gameYourTimeAwayCouldNotBeGathered =
      "Your time away could not be gathered. Your prior progress is safe; try again.";
  static String gameSeasonSettlementRejectedSeasonalReason(Object? value0) =>
      Presentation.template("Season settlement rejected: {value0}", {
        'value0': value0,
      });
  static String gameChallengeDiscoveryRejectedDiscoveryReason(Object? value0) =>
      Presentation.template("Challenge discovery rejected: {value0}", {
        'value0': value0,
      });
  static String gameTimeSettlementRejectedAdvancedReason(Object? value0) =>
      Presentation.template("Time settlement rejected: {value0}", {
        'value0': value0,
      });
  static const gameYourHarborAppearanceIsSavedProductionIs =
      "Your harbor appearance is saved. Production is unchanged.";
}
