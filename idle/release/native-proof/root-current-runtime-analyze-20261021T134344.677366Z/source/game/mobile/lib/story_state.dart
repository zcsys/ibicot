import 'dart:convert';
import 'bundled_content.dart';
import 'content_compatibility.dart';
import 'cosmetics.dart';
import 'package:flutter/services.dart';
import 'package:tideglass_events/tideglass_events.dart';
import 'package:tideglass_progression/tideglass_progression.dart';

class StoryCatalogue {
  StoryCatalogue(
    this.campaign,
    this.dossiers,
    this.archive,
    this.seasonDefinition,
    this.seasonSchedule,
    this.seasonRolloutMode,
  );
  final String seasonRolloutMode;
  final SeasonDefinition seasonDefinition;
  final SeasonSchedule seasonSchedule;
  final Campaign campaign;
  final List<ChallengeDefinition> dossiers;
  final List<Map<String, dynamic>> archive;
  ChallengeDefinition dossier(String id) =>
      dossiers.firstWhere((d) => d.id == id);
  static StoryCatalogue? _bundled;
  static StoryCatalogue? get loaded => _bundled;
  static Future<StoryCatalogue> load() async {
    // Cache the immutable value, never a Future tied to a caller's zone.
    final cached = _bundled;
    if (cached != null) return cached;
    await verifyBundledContent();
    Future<Map<String, dynamic>> read(String path) async =>
        Map<String, dynamic>.from(
          jsonDecode(await rootBundle.loadString(path)),
        );
    final dossiers = <ChallengeDefinition>[];
    for (var i = 1; i <= 12; i++) {
      dossiers.add(
        ChallengeDefinition.fromJson(
          await read(
            'assets/challenges/challenge.${i.toString().padLeft(2, '0')}.json',
          ),
        ),
      );
    }
    final campaign = Campaign(
      await read('assets/progression/campaign.json'),
      dossiers,
    );
    final entries =
        (await read('assets/progression/archive.en.json'))['entries'] as List;
    if (entries.length != 18) {
      throw const FormatException('All eighteen archive entries are required.');
    }
    final season = SeasonDefinition.fromJson(
      await read('assets/events/season.01.json'),
    );
    final schedule = await read('assets/events/schedule.json');
    if (schedule['schema_version'] != 1 ||
        schedule['season_id'] != season.id ||
        schedule['duration_days'] != 28) {
      throw const FormatException('Unsupported seasonal rollout.');
    }
    return _bundled = StoryCatalogue(
      campaign,
      List.unmodifiable(dossiers),
      List.unmodifiable(
        entries.map((v) => Map<String, dynamic>.unmodifiable(v)),
      ),
      season,
      SeasonSchedule(DateTime.parse(schedule['starts_at'] as String)),
      schedule['environment'] as String,
    );
  }
}

/// Main-world narrative and earned decoration state. Paid ownership belongs
/// to the verified platform ledger, never this locally imported object.
class StoryProgress {
  StoryProgress({
    CampaignProgress? campaign,
    DossierCollection? dossiers,
    Set<String> decorations = const {},
    this.equippedDecoration,
    this.season,
    this.pass,
    this.contentDigest,
    this.equippedAppearance,
  }) : campaign = campaign ?? CampaignProgress(),
       dossiers = dossiers ?? DossierCollection(),
       decorations = Set.unmodifiable(decorations) {
    if ((season == null) != (pass == null)) {
      throw const FormatException('Season and pass must be saved together.');
    }
    if (equippedAppearance != null &&
        !cosmeticCatalogue.any(
          (item) =>
              item.id == equippedAppearance &&
              item.source != CosmeticSource.decoration,
        )) {
      throw const FormatException('Unknown harbor appearance.');
    }
    if (decorations.any(
          (id) => !RegExp(r'^cosmetic\.core\.decoration\.0[1-6]$').hasMatch(id),
        ) ||
        (equippedDecoration != null &&
            !decorations.contains(equippedDecoration))) {
      throw const FormatException('Unknown or unowned core decoration.');
    }
  }
  final CampaignProgress campaign;
  final DossierCollection dossiers;
  final Set<String> decorations;
  final String? equippedDecoration;
  final SeasonState? season;
  final PassState? pass;
  final String? contentDigest;

  /// Selection is a preference, never proof of paid ownership. Renderers must
  /// project it through current earned or independently verified ownership.
  final String? equippedAppearance;
  StoryProgress copyWith({
    CampaignProgress? campaign,
    DossierCollection? dossiers,
    Set<String>? decorations,
    String? equippedDecoration,
    bool clearDecoration = false,
    SeasonState? season,
    PassState? pass,
    String? contentDigest,
    String? equippedAppearance,
    bool clearAppearance = false,
  }) => StoryProgress(
    equippedAppearance: clearAppearance
        ? null
        : equippedAppearance ?? this.equippedAppearance,
    contentDigest: contentDigest ?? this.contentDigest,
    season: season ?? this.season,
    pass: pass ?? this.pass,
    campaign: campaign ?? this.campaign,
    dossiers: dossiers ?? this.dossiers,
    decorations: decorations ?? this.decorations,
    equippedDecoration: clearDecoration
        ? null
        : equippedDecoration ?? this.equippedDecoration,
  );
  Map<String, dynamic> toJson() => {
    'schema_version': 4,
    'campaign': campaign.toJson(),
    'dossiers': dossiers.toJson(),
    'decorations': decorations.toList()..sort(),
    'equipped_decoration': equippedDecoration,
    'season': season?.toJson(),
    'pass': pass?.toJson(),
    'content_digest': contentDigest,
    'equipped_appearance': equippedAppearance,
  };
  factory StoryProgress.fromJson(
    Map<String, dynamic> json, {
    SeasonDefinition? seasonDefinition,
  }) {
    seasonDefinition ??= StoryCatalogue.loaded?.seasonDefinition;
    final version = json['schema_version'];
    if ((version != 1 && version != 2 && version != 3 && version != 4) ||
        json.length !=
            (version == 1
                ? 5
                : version == 2
                ? 7
                : version == 3
                ? 8
                : 9)) {
      throw const FormatException('Unsupported story progress.');
    }
    if (version >= 3 && !acceptsStoryContentDigest(json['content_digest'])) {
      throw const FormatException(
        'This story needs its original pinned content.',
      );
    }
    final decorations = List<String>.from(json['decorations']);
    if (decorations.toSet().length != decorations.length) {
      throw const FormatException('Duplicate decoration ownership.');
    }
    if (version >= 2 &&
        (json['season'] != null || json['pass'] != null) &&
        seasonDefinition == null) {
      throw const FormatException('Pinned seasonal content is required.');
    }
    return StoryProgress(
      equippedAppearance: version >= 4
          ? json['equipped_appearance'] as String?
          : null,
      contentDigest: migratedStoryContentDigest(
        json['content_digest'] as String?,
      ),
      season: json['season'] == null
          ? null
          : SeasonState.fromJson(
              Map<String, dynamic>.from(json['season']),
              seasonDefinition!,
            ),
      pass: json['pass'] == null
          ? null
          : PassState.fromJson(Map<String, dynamic>.from(json['pass']), [
              seasonDefinition!,
            ]),
      campaign: CampaignProgress.fromJson(
        Map<String, dynamic>.from(json['campaign']),
      ),
      dossiers: DossierCollection.fromJson(
        Map<String, dynamic>.from(json['dossiers']),
      ),
      decorations: decorations.toSet(),
      equippedDecoration: json['equipped_decoration'] as String?,
    );
  }
}
