import AppKit
import AVFoundation
import Foundation

Task {
    do {
        let args = CommandLine.arguments
        guard args.count == 4 else { throw NSError(domain: "mode source output required", code: 1) }
        let mode = args[1], sourceURL = URL(fileURLWithPath: args[2]), out = URL(fileURLWithPath: args[3])
        guard !FileManager.default.fileExists(atPath: out.path) else { throw NSError(domain: "existing output", code: 1) }
        let asset = AVURLAsset(url: sourceURL)
        let video = try await asset.loadTracks(withMediaType: .video)
        guard video.count == 1 else { throw NSError(domain: "one video required", code: 1) }
        let duration = try await asset.load(.duration)
        let size = try await video[0].load(.naturalSize)
        let transform = try await video[0].load(.preferredTransform)
        if mode == "probe" {
            try FileManager.default.createDirectory(at: out, withIntermediateDirectories: false)
            let gen = AVAssetImageGenerator(asset: asset)
            gen.appliesPreferredTrackTransform = true
            gen.requestedTimeToleranceBefore = .zero
            gen.requestedTimeToleranceAfter = .zero
            var entries: [[String: Any]] = []
            for (i, seconds) in [2.0, 7.0, 12.0, 17.0, 21.966666666666665].enumerated() {
                let image = try await gen.image(at: CMTime(seconds: seconds, preferredTimescale: 600))
                let bitmap = NSBitmapImageRep(cgImage: image.image)
                guard let png = bitmap.representation(using: .png, properties: [:]) else { throw NSError(domain: "PNG", code: 1) }
                let filename = "source-\(i).png"
                try png.write(to: out.appendingPathComponent(filename), options: .withoutOverwriting)
                entries.append(["file":filename,"requested":seconds,"actual":image.actualTime.seconds,
                                "width":image.image.width,"height":image.image.height])
            }
            let metadata: [String: Any] = ["duration":duration.seconds,"natural_width":size.width,"natural_height":size.height,
                "transform":[transform.a,transform.b,transform.c,transform.d,transform.tx,transform.ty],"samples":entries]
            let json = try JSONSerialization.data(withJSONObject: metadata, options:[.sortedKeys,.prettyPrinted])
            try json.write(to: out.appendingPathComponent("metadata.json"), options:.withoutOverwriting)
        } else {
            let composition = AVMutableComposition()
            guard let track = composition.addMutableTrack(withMediaType:.video,preferredTrackID:kCMPersistentTrackID_Invalid) else { throw NSError(domain:"track",code:1) }
            try track.insertTimeRange(CMTimeRange(start:.zero,duration:duration),of:video[0],at:.zero)
            if mode == "rotate" {
                track.preferredTransform = CGAffineTransform(a:0,b:1,c:-1,d:0,tx:size.height,ty:0)
            } else if mode == "audio" {
                track.preferredTransform = transform
                let audioAsset = AVURLAsset(url:URL(fileURLWithPath:"game/mobile/assets/audio/harbor.m4a"))
                let audio = try await audioAsset.loadTracks(withMediaType:.audio)
                guard audio.count == 1, let target = composition.addMutableTrack(withMediaType:.audio,preferredTrackID:kCMPersistentTrackID_Invalid) else { throw NSError(domain:"audio",code:1) }
                try target.insertTimeRange(CMTimeRange(start:.zero,duration:duration),of:audio[0],at:.zero)
            } else { throw NSError(domain:"unknown mode",code:1) }
            guard let exporter = AVAssetExportSession(asset:composition,presetName:AVAssetExportPresetPassthrough) else { throw NSError(domain:"exporter",code:1) }
            try await exporter.export(to:out,as:.mp4)
        }
        exit(0)
    } catch {
        fputs("Review fixture/probe failed: \(error)\n", stderr)
        exit(1)
    }
}
dispatchMain()
