import AVFoundation
import Foundation

// Read-only metadata for raw simulator recordings; no transcoding or edits.
guard CommandLine.arguments.count == 2 else {
    fputs("Expected one local video path\n", stderr)
    exit(2)
}
let url = URL(fileURLWithPath: CommandLine.arguments[1])
Task {
    do {
        let asset = AVURLAsset(url: url)
        let duration = try await asset.load(.duration)
        let tracks = try await asset.loadTracks(withMediaType: .video)
        let audio = try await asset.loadTracks(withMediaType: .audio)
        guard let track = tracks.first else { throw NSError(domain: "MissingVideoTrack", code: 1) }
        let naturalSize = try await track.load(.naturalSize)
        let transform = try await track.load(.preferredTransform)
        let size = naturalSize.applying(transform)
        let result: [String: Any] = [
            "duration_seconds": CMTimeGetSeconds(duration),
            "width": abs(size.width),
            "height": abs(size.height),
            "video_track_count": tracks.count,
            "audio_track_count": audio.count,
        ]
        let data = try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys])
        print(String(decoding: data, as: UTF8.self))
        exit(0)
    } catch {
        fputs("Video metadata failed: \(error)\n", stderr)
        exit(1)
    }
}
dispatchMain()
