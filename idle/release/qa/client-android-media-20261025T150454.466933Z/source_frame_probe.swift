import AppKit
import AVFoundation
import Foundation

Task {
    do {
        let args = CommandLine.arguments
        guard args.count == 3 else { throw NSError(domain: "source and new evidence directory required", code: 1) }
        let source = URL(fileURLWithPath: args[1])
        let output = URL(fileURLWithPath: args[2], isDirectory: true)
        guard !FileManager.default.fileExists(atPath: output.path) else { throw NSError(domain: "refuse existing output", code: 1) }
        let asset = AVURLAsset(url: source)
        let generator = AVAssetImageGenerator(asset: asset)
        generator.appliesPreferredTrackTransform = true
        generator.requestedTimeToleranceBefore = .zero
        generator.requestedTimeToleranceAfter = .zero
        try FileManager.default.createDirectory(at: output, withIntermediateDirectories: false)
        var frames: [[String: Any]] = []
        // Actual preview sample presentation times plus the declared source start of 0.5 seconds.
        for (index, seconds) in [0.5, 5.233333333333333, 10.033333333333333, 14.733333333333333, 19.433333333333334].enumerated() {
            let result = try await generator.image(at: CMTime(seconds: seconds, preferredTimescale: 600))
            let bitmap = NSBitmapImageRep(cgImage: result.image)
            guard let data = bitmap.representation(using: .png, properties: [:]) else { throw NSError(domain: "PNG encoding failed", code: 1) }
            let name = "source-frame-\(index).png"
            try data.write(to: output.appendingPathComponent(name), options: .withoutOverwriting)
            frames.append(["file":name,"requested_source_seconds":seconds,"actual_source_seconds":result.actualTime.seconds,"width":result.image.width,"height":result.image.height])
        }
        let metadata: [String: Any] = ["source":source.path,"operation":"Decode actual source frames at selected times; no pixel repair, crop, masking or resynthesis.","frames":frames]
        let data = try JSONSerialization.data(withJSONObject: metadata, options: [.sortedKeys,.prettyPrinted])
        try data.write(to: output.appendingPathComponent("metadata.json"), options: .withoutOverwriting)
        exit(0)
    } catch {
        fputs("Frame probe failed: \(error)\n", stderr)
        exit(1)
    }
}
dispatchMain()
