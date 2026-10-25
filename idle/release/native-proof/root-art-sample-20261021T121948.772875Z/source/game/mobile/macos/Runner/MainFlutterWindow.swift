import Cocoa
import Darwin
import FlutterMacOS

class MainFlutterWindow: NSWindow {
  private var ownershipClock: FlutterMethodChannel?
  private var clockObservers: [NSObjectProtocol] = []

  override func awakeFromNib() {
    let flutterViewController = FlutterViewController()
    let windowFrame = self.frame
    self.contentViewController = flutterViewController
    self.setFrame(windowFrame, display: true)

    RegisterGeneratedPlugins(registry: flutterViewController)
    let channel = FlutterMethodChannel(name: "dev.tideglass/ownership_clock",
      binaryMessenger: flutterViewController.engine.binaryMessenger)
    ownershipClock = channel
    channel.setMethodCallHandler { call, result in
      guard call.method == "sample" else { result(FlutterMethodNotImplemented); return }
      guard let sample = TideglassOwnershipClock.sample() else {
        result(FlutterError(code: "ownership_clock_unavailable", message: "Clock evidence unavailable", details: nil))
        return
      }
      result(sample)
    }
    for name in [NSWorkspace.willSleepNotification, NSWorkspace.didWakeNotification] {
      clockObservers.append(NSWorkspace.shared.notificationCenter.addObserver(forName: name,
        object: nil, queue: .main) { [weak self] _ in
          self?.ownershipClock?.invokeMethod("invalidate", arguments: nil)
        })
    }
    for name in [NSApplication.willResignActiveNotification, NSApplication.didBecomeActiveNotification] {
      clockObservers.append(NotificationCenter.default.addObserver(forName: name,
        object: nil, queue: .main) { [weak self] _ in
          self?.ownershipClock?.invokeMethod("invalidate", arguments: nil)
        })
    }

    super.awakeFromNib()
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
