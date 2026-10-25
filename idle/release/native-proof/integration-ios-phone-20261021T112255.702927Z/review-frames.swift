import Foundation
import AVFoundation
import ImageIO
import UniformTypeIdentifiers
let file = URL(fileURLWithPath: CommandLine.arguments[1])
let output = URL(fileURLWithPath: CommandLine.arguments[2])
try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
let asset = AVURLAsset(url: file)
let generator = AVAssetImageGenerator(asset: asset)
generator.appliesPreferredTrackTransform = true
for second in [1, 6, 11, 17, 23] {
  var actual = CMTime.zero
  let frame = try generator.copyCGImage(at: CMTime(seconds: Double(second), preferredTimescale: 600), actualTime: &actual)
  let target = output.appendingPathComponent("frame-\(second)s.png")
  let dest = CGImageDestinationCreateWithURL(target as CFURL, UTType.png.identifier as CFString, 1, nil)!
  CGImageDestinationAddImage(dest, frame, nil)
  guard CGImageDestinationFinalize(dest) else { fatalError("Cannot write frame") }
  print("\(second): actual \(actual.seconds) seconds, \(frame.width)x\(frame.height)")
}
