import 'dart:convert';
import 'package:flutter/services.dart';

class CalibrationStar {
  const CalibrationStar(this.key, this.label, this.x, this.y);
  final int key;
  final String label;
  final double x, y;
}

class CalibrationPattern {
  CalibrationPattern._(
    this.id,
    this.title,
    this.intro,
    this.instructions,
    this.accessibleLabel,
    this.accessibleDescription,
    this.stars,
    this.edges,
    this.start,
    this.end,
  );
  final String id,
      title,
      intro,
      instructions,
      accessibleLabel,
      accessibleDescription;
  final List<CalibrationStar> stars;
  final List<(int, int)> edges;
  final int start, end;
  factory CalibrationPattern.fromJson(Map<String, dynamic> json) {
    if (json['schema_version'] != 1 ||
        json['focus_cost'] != 1 ||
        json['reward_profile_id'] != 'calibration.standard' ||
        json['time_limit_seconds'] != null) {
      throw const FormatException('Unsupported calibration rules');
    }
    final stars = (json['nodes'] as List)
        .map((value) {
          final node = value as Map;
          final x = (node['x'] as num).toDouble(),
              y = (node['y'] as num).toDouble();
          if (x < 0 || x > 1 || y < 0 || y > 1 || !x.isFinite || !y.isFinite) {
            throw const FormatException('Star position is outside the sky');
          }
          return CalibrationStar(
            node['key'] as int,
            node['label'] as String,
            x,
            y,
          );
        })
        .toList(growable: false);
    final keys = stars.map((star) => star.key).toSet();
    if (stars.length < 2 ||
        keys.length != stars.length ||
        !keys.contains(json['start']) ||
        !keys.contains(json['end']) ||
        json['start'] == json['end']) {
      throw const FormatException('Invalid calibration stars');
    }
    final edges = (json['edges'] as List)
        .map((edge) {
          final pair = edge as List;
          if (pair.length != 2 ||
              !keys.contains(pair[0]) ||
              !keys.contains(pair[1]) ||
              pair[0] == pair[1]) {
            throw const FormatException('Invalid calibration link');
          }
          return (pair[0] as int, pair[1] as int);
        })
        .toList(growable: false);
    return CalibrationPattern._(
      json['id'] as String,
      json['title'] as String,
      json['intro'] as String,
      json['instructions'] as String,
      json['accessible_label'] as String,
      json['accessible_description'] as String,
      stars,
      edges,
      json['start'] as int,
      json['end'] as int,
    );
  }
  bool linked(int a, int b) => edges.any(
    (edge) => (edge.$1 == a && edge.$2 == b) || (edge.$1 == b && edge.$2 == a),
  );
  CalibrationStar star(int key) => stars.firstWhere((star) => star.key == key);
}

/// A route is UI state only. Completing it never grants currency directly.
class CalibrationRoute {
  CalibrationRoute(this.pattern) : _visited = [pattern.start];
  final CalibrationPattern pattern;
  final List<int> _visited;
  List<int> get visited => List.unmodifiable(_visited);
  bool get solved =>
      _visited.length == pattern.stars.length && _visited.last == pattern.end;
  bool canVisit(int key) =>
      !solved &&
      !_visited.contains(key) &&
      pattern.linked(_visited.last, key) &&
      (key != pattern.end || _visited.length == pattern.stars.length - 1);
  bool visit(int key) {
    if (!canVisit(key)) return false;
    _visited.add(key);
    return true;
  }

  void undo() {
    if (_visited.length > 1) _visited.removeLast();
  }

  void restart() {
    _visited
      ..clear()
      ..add(pattern.start);
  }

  List<CalibrationStar> get nextStars =>
      pattern.stars.where((star) => canVisit(star.key)).toList(growable: false);
}

Future<List<CalibrationPattern>> loadCalibrationPatterns({
  AssetBundle? bundle,
}) async {
  final source = bundle ?? rootBundle;
  final patterns = <CalibrationPattern>[];
  for (var i = 1; i <= 12; i++) {
    final text = await source.loadString(
      'assets/calibrations/calibration.${i.toString().padLeft(2, '0')}.pattern.json',
    );
    patterns.add(
      CalibrationPattern.fromJson(jsonDecode(text) as Map<String, dynamic>),
    );
  }
  return List.unmodifiable(patterns);
}
