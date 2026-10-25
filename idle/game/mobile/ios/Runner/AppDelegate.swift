import Darwin
import Flutter
import UIKit
import UserNotifications

@main
@objc class AppDelegate: FlutterAppDelegate, FlutterImplicitEngineDelegate {
  private var studyProcess: FlutterMethodChannel?
  private var ownershipClock: FlutterMethodChannel?
  private var clockObservers: [NSObjectProtocol] = []

  override func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
  ) -> Bool {
    UNUserNotificationCenter.current().delegate = self
    return super.application(application, didFinishLaunchingWithOptions: launchOptions)
  }

  func didInitializeImplicitFlutterEngine(_ engineBridge: FlutterImplicitEngineBridge) {
    GeneratedPluginRegistrant.register(with: engineBridge.pluginRegistry)
    if let studyRegistrar = engineBridge.pluginRegistry.registrar(forPlugin: "TideglassStudyProcess") {
      let channel = FlutterMethodChannel(name: "dev.tideglass/study_process", binaryMessenger: studyRegistrar.messenger())
      studyProcess = channel
      channel.setMethodCallHandler { call, result in
        guard call.method == "observe" else { result(FlutterMethodNotImplemented); return }
        let bundle = Bundle.main
        guard let identifier = bundle.bundleIdentifier,
              let version = bundle.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String,
              let build = bundle.object(forInfoDictionaryKey: "CFBundleVersion") as? String else {
          result(FlutterError(code: "study_context_unavailable", message: "Process metadata unavailable", details: nil)); return
        }
        // Observation time is not a claim of kernel process launch time.
        result(["version": 1, "status": "available", "source": "native_process_observation_v1",
                "native_pid": Int(getpid()), "platform": "ios", "application_id": identifier,
                "application_version": version, "application_build": build,
                "observed_start_utc_ms": Int64(Date().timeIntervalSince1970 * 1000)])
      }
    }
    guard let registrar = engineBridge.pluginRegistry.registrar(forPlugin: "TideglassOwnershipClock") else { return }
    let channel = FlutterMethodChannel(name: "dev.tideglass/ownership_clock", binaryMessenger: registrar.messenger())
    ownershipClock = channel
    channel.setMethodCallHandler { call, result in
      guard call.method == "sample" else { result(FlutterMethodNotImplemented); return }
      guard let sample = TideglassOwnershipClock.sample() else {
        result(FlutterError(code: "ownership_clock_unavailable", message: "Clock evidence unavailable", details: nil))
        return
      }
      result(sample)
    }
    let names: [Notification.Name] = [UIApplication.willResignActiveNotification,
      UIApplication.didEnterBackgroundNotification, UIApplication.willEnterForegroundNotification,
      UIScene.willDeactivateNotification, UIScene.didActivateNotification]
    for name in names {
      clockObservers.append(NotificationCenter.default.addObserver(forName: name, object: nil, queue: .main) { [weak self] _ in
        self?.ownershipClock?.invokeMethod("invalidate", arguments: nil)
      })
    }
  }
}

// Sleep-inclusive elapsed clock. The epoch is deliberately process-only: iOS 18
// makes kern.bootsessionuuid unavailable to apps. Never guess a boot identity.
private enum TideglassOwnershipClock {
  static let epoch = "apple.process." + UUID().uuidString
  static func sample() -> [String: Any]? {
    var scale = mach_timebase_info_data_t()
    guard mach_timebase_info(&scale) == KERN_SUCCESS, scale.denom > 0 else { return nil }
    let ticks = mach_continuous_time()
    let denominator = UInt64(scale.denom), numerator = UInt64(scale.numer)
    let (whole, overflow) = (ticks / denominator).multipliedReportingOverflow(by: numerator)
    let remainder = ((ticks % denominator) * numerator) / denominator
    let (nanoseconds, sumOverflow) = whole.addingReportingOverflow(remainder)
    guard !overflow, !sumOverflow, nanoseconds / 1000 <= UInt64(Int64.max) else { return nil }
    return ["version": 1, "elapsed_us": Int64(nanoseconds / 1000),
            "epoch_id": epoch, "continuity_scope": "process"]
  }
}
