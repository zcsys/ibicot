import AppKit
import AVFoundation
import Foundation

func fourCC(_ value: FourCharCode) -> String {
    String(bytes: [24, 16, 8, 0].map { UInt8((value >> $0) & 255) }, encoding: .ascii) ?? "unknown"
}

Task {
    do {
        guard CommandLine.arguments.count == 3 else {
            throw NSError(domain: "Expected video and new evidence directory", code: 1)
        }
        let url = URL(fileURLWithPath: CommandLine.arguments[1])
        let out = URL(fileURLWithPath: CommandLine.arguments[2])
        guard !FileManager.default.fileExists(atPath: out.path) else {
            throw NSError(domain: "Refusing to replace evidence", code: 1)
        }
        let asset = AVURLAsset(url: url)
        let duration = try await asset.load(.duration).seconds
        let tracks = try await asset.loadTracks(withMediaType: .video)
        let audio = try await asset.loadTracks(withMediaType: .audio)
        guard tracks.count == 1 else { throw NSError(domain: "Expected one video track", code: 1) }
        let track = tracks[0]
        let size = try await track.load(.naturalSize)
        let transform = try await track.load(.preferredTransform)
        let formats = try await track.load(.formatDescriptions)
        let frameRate = try await track.load(.nominalFrameRate)
        let dataRate = try await track.load(.estimatedDataRate)
        let display = CGRect(origin: .zero, size: size).applying(transform)
        let reader = try AVAssetReader(asset: asset)
        let read = AVAssetReaderTrackOutput(track: track, outputSettings: nil)
        reader.add(read)
        guard reader.startReading() else { throw NSError(domain: "Cannot read samples", code: 1) }
        var timestamps: [Double] = []
        while let sample = read.copyNextSampleBuffer() {
            timestamps.append(CMSampleBufferGetPresentationTimeStamp(sample).seconds)
        }
        guard reader.status == .completed else { throw NSError(domain: "Incomplete sample read", code: 1) }
        timestamps.sort() // H.264 decoding order can differ from presentation order.
        let gaps = zip(timestamps.dropFirst(), timestamps).map { $0 - $1 }
        try FileManager.default.createDirectory(at: out, withIntermediateDirectories: false)
        let generator = AVAssetImageGenerator(asset: asset)
        generator.appliesPreferredTrackTransform = true
        generator.requestedTimeToleranceBefore = .zero
        generator.requestedTimeToleranceAfter = CMTime(value: 1, timescale: 30)
        var frames: [[String: Any]] = []
        for (index, seconds) in [0.0, duration * 0.25, duration * 0.5,
                                 duration * 0.75, max(0, duration - 1.0 / 30)].enumerated() {
            let frame = try await generator.image(at: CMTime(seconds: seconds, preferredTimescale: 600))
            let bitmap = NSBitmapImageRep(cgImage: frame.image)
            guard let bytes = bitmap.representation(using: .png, properties: [:]) else {
                throw NSError(domain: "Cannot encode evidence frame", code: 1)
            }
            let name = "frame-\(index).png"
            try bytes.write(to: out.appendingPathComponent(name), options: .withoutOverwriting)
            frames.append(["file": name, "requested_seconds": seconds,
                           "actual_seconds": frame.actualTime.seconds])
        }
        let info: [String: Any] = [
            "source": url.path, "duration_seconds": duration,
            "display_width": display.width, "display_height": display.height,
            "codec_fourcc": formats.map { fourCC(CMFormatDescriptionGetMediaSubType($0)) },
            "nominal_frames_per_second": frameRate, "estimated_bits_per_second": dataRate,
            "audio_track_count": audio.count, "compressed_video_samples": timestamps.count,
            "first_frame_seconds": timestamps.first ?? -1,
            "last_frame_seconds": timestamps.last ?? -1,
            "min_frame_gap_seconds": gaps.min() ?? -1,
            "max_frame_gap_seconds": gaps.max() ?? -1,
            "sample_read_complete": true, "frames": frames,
        ]
        let data = try JSONSerialization.data(withJSONObject: info, options: [.sortedKeys, .prettyPrinted])
        try data.write(to: out.appendingPathComponent("metadata.json"), options: .withoutOverwriting)
        print(String(decoding: data, as: UTF8.self))
        exit(0)
    } catch {
        fputs("Preview inspection failed: \(error)\n", stderr)
        exit(1)
    }
}
dispatchMain()
