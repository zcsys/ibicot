import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:crypto/crypto.dart';
import 'tideglass_platform.dart';

/// Streams only the fixed authenticated asset from the configured service.
/// Tokens never appear in URLs, filenames, returned metadata or error text.
class SoundtrackDelivery {
  SoundtrackDelivery(
    this.client, {
    this.jsonDeadline = const Duration(seconds: 30),
  }) {
    if (jsonDeadline <= Duration.zero ||
        jsonDeadline > const Duration(seconds: 30)) {
      throw ArgumentError(
        'The JSON deadline must be positive and at most30seconds.',
      );
    }
  }
  final TideglassServiceClient client;
  final Duration jsonDeadline;
  static const maximumBytes = 64 * 1024 * 1024;
  static const filename = 'tideglass-original-soundtrack.zip';
  bool _busy = false;

  void _check(ServiceSession expected, int generation) {
    if (!identical(client.session, expected) ||
        client.sessionGeneration != generation ||
        !expected.expiresAt.isAfter(DateTime.now().toUtc())) {
      throw const ServiceException('session_changed');
    }
  }

  Future<HttpClientResponse> _get(
    HttpClient http,
    String path,
    ServiceSession session,
    int generation,
  ) async {
    _check(session, generation);
    final request = await http
        .getUrl(client.endpoint.resolve(path))
        .timeout(const Duration(seconds: 30));
    _check(session, generation);
    request.followRedirects = false;
    request.headers.set(
      HttpHeaders.authorizationHeader,
      'Bearer ${session.token}',
    );
    final response = await request.close().timeout(const Duration(seconds: 30));
    _check(session, generation);
    if (response.statusCode != HttpStatus.ok) {
      throw ServiceException(
        response.statusCode == 403
            ? 'soundtrack_ownership_required'
            : 'soundtrack_delivery_unavailable',
        status: response.statusCode,
      );
    }
    return response;
  }

  Future<Map<String, dynamic>> _json(
    HttpClient http,
    String path,
    ServiceSession session,
    int generation,
  ) => _readJson(http, path, session, generation).timeout(jsonDeadline);

  Future<Map<String, dynamic>> _readJson(
    HttpClient http,
    String path,
    ServiceSession session,
    int generation,
  ) async {
    final response = await _get(http, path, session, generation);
    final bytes = <int>[];
    await for (final part in response.timeout(const Duration(seconds: 30))) {
      _check(session, generation);
      if (bytes.length + part.length > 16384) {
        throw const ServiceException('invalid_soundtrack_manifest');
      }
      bytes.addAll(part);
    }
    _check(session, generation);
    final value = jsonDecode(utf8.decode(bytes));
    if (value is! Map<String, dynamic>) {
      throw const ServiceException('invalid_soundtrack_manifest');
    }
    return value;
  }

  Future<bool> ready() async {
    final session = client.session;
    if (session == null) return false;
    final generation = client.sessionGeneration;
    final http = HttpClient()..connectionTimeout = const Duration(seconds: 20);
    try {
      final result = await _json(
        http,
        '/v1/commerce/capabilities',
        session,
        generation,
      );
      return result['soundtrack_delivery_ready'] == true;
    } on ServiceException {
      rethrow;
    } catch (_) {
      throw const ServiceException('soundtrack_delivery_unavailable');
    } finally {
      http.close(force: true);
    }
  }

  /// The caller opens a native save/share sheet only after this future returns.
  /// Each export has a private temporary directory and is published by rename
  /// only after exact size and SHA-256 verification. Failed transfers are erased.
  Future<File> download(Directory destination) async {
    if (_busy) throw const ServiceException('soundtrack_download_in_progress');
    final session = client.session;
    if (session == null) throw const ServiceException('sign_in_required');
    final generation = client.sessionGeneration;
    final http = HttpClient()..connectionTimeout = const Duration(seconds: 20);
    Directory? staging;
    RandomAccessFile? output;
    var complete = false;
    _busy = true;
    try {
      final manifest = await _json(
        http,
        '/v1/soundtrack/manifest',
        session,
        generation,
      );
      final size = manifest['bytes'], hash = manifest['sha256'];
      if (manifest['asset_id'] != 'soundtrack.01' ||
          manifest['filename'] != filename ||
          manifest['content_type'] != 'application/zip' ||
          manifest['download_path'] != '/v1/soundtrack/download' ||
          size is! int ||
          size <= 0 ||
          size > maximumBytes ||
          hash is! String ||
          !RegExp(r'^[0-9a-f]{64}$').hasMatch(hash)) {
        throw const ServiceException('invalid_soundtrack_manifest');
      }
      _check(session, generation);
      await destination.create(recursive: true);
      staging = await destination.createTemp('soundtrack-');
      final part = File('${staging.path}/download.part');
      output = await part.open(mode: FileMode.write);
      final response = await _get(
        http,
        '/v1/soundtrack/download',
        session,
        generation,
      );
      if (response.contentLength != size ||
          response.headers.contentType?.mimeType != 'application/zip' ||
          response.headers.value('X-Content-SHA256') != hash) {
        throw const ServiceException('invalid_soundtrack_response');
      }
      final digest = _DigestSink();
      final hasher = sha256.startChunkedConversion(digest);
      var received = 0;
      final watch = Stopwatch()..start();
      await for (final bytes in response.timeout(const Duration(seconds: 30))) {
        _check(session, generation);
        received += bytes.length;
        if (received > size || watch.elapsed > const Duration(minutes: 5)) {
          throw const ServiceException('invalid_soundtrack_response');
        }
        hasher.add(bytes);
        await output.writeFrom(bytes);
      }
      hasher.close();
      if (received != size || digest.value?.toString() != hash) {
        throw const ServiceException('soundtrack_integrity_failed');
      }
      await output.flush();
      await output.close();
      output = null;
      _check(session, generation);
      final published = await part.rename('${staging.path}/$filename');
      _check(session, generation);
      complete = true;
      return published;
    } on ServiceException {
      rethrow;
    } catch (_) {
      throw const ServiceException('soundtrack_delivery_unavailable');
    } finally {
      http.close(force: true);
      var cleanupFailed = false;
      try {
        try {
          await output?.close();
        } catch (_) {
          cleanupFailed = true;
        }
        try {
          if (!complete && staging != null && await staging.exists()) {
            await staging.delete(recursive: true);
          }
        } catch (_) {
          cleanupFailed = true;
        }
      } finally {
        _busy = false;
      }
      if (cleanupFailed) {
        throw const ServiceException('soundtrack_cleanup_failed');
      }
    }
  }
}

class _DigestSink implements Sink<Digest> {
  Digest? value;
  @override
  void add(Digest data) => value = data;
  @override
  void close() {}
}
