import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'package:tideglass_core/tideglass_core.dart';

String canonicalDigest(Object? value) =>
    sha256.convert(utf8.encode(jsonEncode(_canonical(value)))).toString();
Object? _canonical(Object? value) {
  if (value is Map) {
    final keys = value.keys.cast<String>().toList()..sort();
    return {for (final key in keys) key: _canonical(value[key])};
  }
  if (value is List) return value.map(_canonical).toList();
  return value;
}

void exactKeys(Map<String, dynamic> value, Set<String> keys) {
  if (value.length != keys.length || !value.keys.every(keys.contains))
    throw const FormatException('Unknown or missing season/pass fields.');
}

Set<String> stringSet(Object? value) {
  final list = List<String>.from(value as List);
  if (list.toSet().length != list.length || list.any((v) => v.isEmpty))
    throw const FormatException('Duplicate or empty receipt identity.');
  return list.toSet();
}

class PassReward {
  final String id, track, kind, contentId, title, body;
  final int level;
  PassReward._(this.id, this.track, this.kind, this.contentId, this.title,
      this.body, this.level);
  factory PassReward.fromJson(Map<String, dynamic> json) {
    exactKeys(json, {
      'id',
      'level',
      'track',
      'kind',
      'content_id',
      'title',
      'body',
      'economic_effects'
    });
    final track = json['track'] as String, kind = json['kind'] as String;
    final level = json['level'] as int;
    if (!{'free', 'premium'}.contains(track) ||
        !{'cosmetic', 'archive_fragment'}.contains(kind) ||
        (track == 'premium' && kind != 'cosmetic') ||
        level < 1 ||
        level > 30 ||
        (json['economic_effects'] as List).isNotEmpty ||
        (json['title'] as String).trim().isEmpty ||
        (json['body'] as String).trim().isEmpty)
      throw const FormatException('Unsafe or incomplete pass reward.');
    return PassReward._(
        json['id'] as String,
        track,
        kind,
        json['content_id'] as String,
        json['title'] as String,
        json['body'] as String,
        level);
  }
}

class SeasonMilestone {
  final String id, badgeId, title, body;
  final BigInt lifetimeMicros;
  SeasonMilestone._(
      this.id, this.badgeId, this.title, this.body, this.lifetimeMicros);
  factory SeasonMilestone.fromJson(Map<String, dynamic> json) {
    exactKeys(json, {'id', 'lifetime_r', 'badge_id', 'title', 'body'});
    final target =
        parseNonnegativeInteger(json['lifetime_r']) * BigInt.from(1000000);
    if (target <= BigInt.zero ||
        !(json['badge_id'] as String).startsWith('badge.'))
      throw const FormatException('Invalid personal milestone.');
    return SeasonMilestone._(json['id'] as String, json['badge_id'] as String,
        json['title'] as String, json['body'] as String, target);
  }
}

/// A fully authored, pinned season definition. Schedule dates are supplied by
/// an independently versioned rollout configuration, never invented here.
class SeasonDefinition {
  final String id, rulesVersion, digest, title, passId;
  final Map<String, String> copy;
  final List<PassReward> rewards;
  final List<SeasonMilestone> milestones;
  final List<List<int>> matrix;
  SeasonDefinition._(
      this.id,
      this.rulesVersion,
      this.digest,
      this.title,
      this.passId,
      Map<String, String> copy,
      List<PassReward> rewards,
      List<SeasonMilestone> milestones,
      List<List<int>> matrix)
      : copy = Map.unmodifiable(copy),
        rewards = List.unmodifiable(rewards),
        milestones = List.unmodifiable(milestones),
        matrix =
            List.unmodifiable(matrix.map((v) => List<int>.unmodifiable(v)));
  factory SeasonDefinition.fromJson(Map<String, dynamic> json) {
    exactKeys(json, {
      'schema_version',
      'id',
      'rules_version',
      'title',
      'pass_id',
      'duration_days',
      'base_economy_version',
      'synergy_percent_matrix',
      'synergies_immediate',
      'main_power_import',
      'paid_effects',
      'rechart_enabled',
      'economic_exports',
      'offline_envelope',
      'initial_counts',
      'levels',
      'xp_per_level',
      'copy',
      'milestones',
      'rewards'
    });
    if (json['schema_version'] != 1 ||
        json['duration_days'] != 28 ||
        json['base_economy_version'] != economyVersion ||
        json['synergies_immediate'] != true ||
        json['main_power_import'] != false ||
        json['paid_effects'] != false ||
        json['rechart_enabled'] != false ||
        (json['economic_exports'] as List).isNotEmpty ||
        json['offline_envelope'] != '24h_full_48h_quarter' ||
        jsonEncode(json['initial_counts']) != '[1,0,0,0,0]' ||
        json['levels'] != 30 ||
        json['xp_per_level'] != 500 ||
        jsonEncode(json['synergy_percent_matrix']) != '[[10,20],[25,10]]')
      throw const FormatException(
          'Unsupported or economically unsafe season rules.');
    final id = json['id'] as String, pass = json['pass_id'] as String;
    if (!RegExp(r'^season\.[0-9]{2}$').hasMatch(id) ||
        !RegExp(r'^pass\.[0-9]{2}$').hasMatch(pass) ||
        (json['rules_version'] as String).isEmpty ||
        (json['title'] as String).isEmpty)
      throw const FormatException('Invalid season identity.');
    final rewards = (json['rewards'] as List)
        .map((r) => PassReward.fromJson(Map<String, dynamic>.from(r)))
        .toList();
    final free = rewards.where((r) => r.track == 'free').toList();
    final premium = rewards.where((r) => r.track == 'premium').toList();
    if (free.length != 30 ||
        premium.length != 10 ||
        rewards.map((r) => r.id).toSet().length != 40 ||
        rewards.map((r) => r.contentId).toSet().length != 40 ||
        free.where((r) => r.kind == 'cosmetic').length != 10 ||
        free.where((r) => r.kind == 'archive_fragment').length != 20 ||
        !List.generate(30, (i) => i + 1)
            .every((level) => free.any((r) => r.level == level)) ||
        !List.generate(10, (i) => (i + 1) * 3)
            .every((level) => premium.any((r) => r.level == level)) ||
        rewards.any((r) =>
            r.id != '$pass.${r.track}.${r.level.toString().padLeft(2, '0')}'))
      throw const FormatException(
          'The complete 30-free/10-premium reward track is required.');
    final copy = Map<String, String>.from(json['copy']);
    if (!{
          'upcoming',
          'live',
          'ended',
          'archived',
          'pass',
          'premium',
          'alternative',
          'archive_resume'
        }.every(copy.containsKey) ||
        copy.values.any((v) => v.trim().isEmpty))
      throw const FormatException('Missing season copy.');
    final milestones = (json['milestones'] as List)
        .map((m) => SeasonMilestone.fromJson(Map<String, dynamic>.from(m)))
        .toList();
    if (milestones.isEmpty ||
        milestones.map((m) => m.id).toSet().length != milestones.length ||
        milestones.map((m) => m.badgeId).toSet().length != milestones.length)
      throw const FormatException('Missing or duplicate personal milestones.');
    return SeasonDefinition._(
        id,
        json['rules_version'] as String,
        canonicalDigest(json),
        json['title'] as String,
        pass,
        copy,
        rewards,
        milestones,
        (json['synergy_percent_matrix'] as List)
            .map((r) => List<int>.from(r))
            .toList());
  }
  PassReward reward(String id) => rewards.firstWhere((r) => r.id == id,
      orElse: () => throw const FormatException('Unknown pass reward.'));
}

class SeasonSchedule {
  final BigInt startsAtMicros, endsAtMicros;
  SeasonSchedule(DateTime startsAtUtc)
      : startsAtMicros =
            BigInt.from(startsAtUtc.toUtc().microsecondsSinceEpoch),
        endsAtMicros = BigInt.from(startsAtUtc.toUtc().microsecondsSinceEpoch) +
            BigInt.from(2419200000000) {
    if (startsAtMicros.isNegative)
      throw ArgumentError('Season start precedes supported epoch.');
  }
}
