import AVFoundation
import Foundation

// Full-frame, real-time edit of an existing silent native recording. No synthetic
// frames, speed changes or UI crop. Source and output must be different files.
func require(_ condition: Bool, _ message: String) throws {
    if !condition { throw NSError(domain: message, code: 1) }
}

Task {
    do {
        guard #available(macOS 26.0, *) else {
            throw NSError(domain: "Preview tool requires macOS26 or later", code: 1)
        }
        let args = CommandLine.arguments
        try require(args.count == 7, "Expected input output start duration width height")
        guard let start = Double(args[3]), let duration = Double(args[4]),
              let width = Int(args[5]), let height = Int(args[6]) else {
            throw NSError(domain: "Invalid numeric argument", code: 1)
        }
        try require(start.isFinite && start >= 0 && duration.isFinite &&
                    duration >= 15 && duration <= 30, "Invalid clip interval")
        try require(width >= 320 && height >= 320 && width <= 1920 &&
                    height <= 1920 && width % 2 == 0 && height % 2 == 0,
                    "Invalid even output dimensions")
        let input = URL(fileURLWithPath: args[1]).standardizedFileURL
        let output = URL(fileURLWithPath: args[2]).standardizedFileURL
        try require(input.resolvingSymlinksInPath() != output.resolvingSymlinksInPath(),
                    "Source must be preserved")
        try require(!FileManager.default.fileExists(atPath: output.path),
                    "Refusing to replace existing output")
        let source = AVURLAsset(url: input)
        let sourceDuration = try await source.load(.duration)
        let videos = try await source.loadTracks(withMediaType: .video)
        let audio = try await source.loadTracks(withMediaType: .audio)
        try require(videos.count == 1 && audio.isEmpty,
                    "Expected one silent video; refusing to discard source audio")
        try require(start + duration <= sourceDuration.seconds, "Clip exceeds source")
        let track = videos[0]
        let size = try await track.load(.naturalSize)
        let originalTransform = try await track.load(.preferredTransform)
        let originalRect = CGRect(origin: .zero, size: size).applying(originalTransform)
        try require(originalRect.width > 0 && originalRect.height > 0,
                    "Invalid source frame")
        let canvas = CGSize(width: width, height: height)
        let scale = min(canvas.width / originalRect.width, canvas.height / originalRect.height)
        let padding = CGPoint(x: (canvas.width - originalRect.width * scale) / 2,
                              y: (canvas.height - originalRect.height * scale) / 2)
        let transform = originalTransform
            .concatenating(CGAffineTransform(translationX: -originalRect.minX, y: -originalRect.minY))
            .concatenating(CGAffineTransform(scaleX: scale, y: scale))
            .concatenating(CGAffineTransform(translationX: padding.x, y: padding.y))
        let range = CMTimeRange(start: CMTime(seconds: start, preferredTimescale: 600),
                                duration: CMTime(seconds: duration, preferredTimescale: 600))
        let composition = AVMutableComposition()
        guard let clip = composition.addMutableTrack(withMediaType: .video,
                                                     preferredTrackID: kCMPersistentTrackID_Invalid) else {
            throw NSError(domain: "Cannot create video track", code: 1)
        }
        try clip.insertTimeRange(range, of: track, at: .zero)
        var layerConfig = AVVideoCompositionLayerInstruction.Configuration(assetTrack: clip)
        layerConfig.setTransform(transform, at: .zero)
        let layer = AVVideoCompositionLayerInstruction(configuration: layerConfig)
        let instruction = AVVideoCompositionInstruction(configuration: .init(
            backgroundColor: CGColor(red: 0.02, green: 0.06, blue: 0.10, alpha: 1),
            layerInstructions: [layer],
            timeRange: CMTimeRange(start: .zero, duration: range.duration)))
        let video = AVVideoComposition(configuration: .init(
            frameDuration: CMTime(value: 1, timescale: 30),
            instructions: [instruction], renderSize: canvas))
        let reader = try AVAssetReader(asset: composition)
        let read = AVAssetReaderVideoCompositionOutput(videoTracks: [clip],
            videoSettings: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA])
        read.videoComposition = video
        try require(reader.canAdd(read), "Cannot attach video reader")
        reader.add(read)
        let writer = try AVAssetWriter(outputURL: output, fileType: .mp4)
        let write = AVAssetWriterInput(mediaType: .video, outputSettings: [
            AVVideoCodecKey: AVVideoCodecType.h264,
            AVVideoWidthKey: width, AVVideoHeightKey: height,
            AVVideoCompressionPropertiesKey: [
                AVVideoAverageBitRateKey: 11_000_000,
                AVVideoExpectedSourceFrameRateKey: 30,
                AVVideoMaxKeyFrameIntervalKey: 30,
                AVVideoProfileLevelKey: AVVideoProfileLevelH264High40,
            ],
        ])
        write.expectsMediaDataInRealTime = false
        try require(writer.canAdd(write), "Cannot attach video writer")
        writer.add(write)
        try require(writer.startWriting(), "Cannot start video writer")
        writer.startSession(atSourceTime: .zero)
        try require(reader.startReading(), "Cannot start video reader")
        var count = 0
        while let sample = read.copyNextSampleBuffer() {
            while !write.isReadyForMoreMediaData {
                try require(writer.status == .writing, "Video writer failed")
                try await Task.sleep(for: .milliseconds(2))
            }
            try require(write.append(sample), "Cannot append decoded frame")
            count += 1
        }
        try require(reader.status == .completed, "Video reader did not complete")
        write.markAsFinished()
        await writer.finishWriting()
        try require(writer.status == .completed && count > 0, "Video export did not complete")
        let result: [String: Any] = [
            "source": input.path, "output": output.path, "source_start_seconds": start,
            "requested_duration_seconds": duration, "frames_encoded": count,
            "output_width": width, "output_height": height, "frame_rate": 30,
            "target_video_bits_per_second": 11_000_000,
            "full_frame_preserved": true, "speed_multiplier": 1,
            "audio_tracks": 0, "synthetic_frames_added": false,
            "padding_x": padding.x, "padding_y": padding.y,
            "store_submission_qualified": false,
        ]
        let data = try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys])
        print(String(decoding: data, as: UTF8.self))
        exit(0)
    } catch {
        fputs("Preview export failed: \(error)\n", stderr)
        exit(1)
    }
}
dispatchMain()
