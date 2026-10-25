import 'dart:convert';
import 'dart:io';
import 'file:///Users/csys/Desktop/ibicot/idle/game/mobile/lib/help_content.dart';
void main(List<String> args) {
  final topics = {
      'asset.support.help': [HelpTopic.play, HelpTopic.rechart, HelpTopic.away, HelpTopic.notes],
      'asset.support.recovery_guide': [HelpTopic.recovery],
      'asset.support.release_notes': [HelpTopic.releaseNotes],
      'asset.support.credits': [HelpTopic.credits],
    };
    final values = <String, Object?>{};
    for (final entry in topics.entries) {
      values[entry.key] = {
        'schema_version': 1,
        'asset_id': entry.key,
        'locale': 'en-US',
        'runtime_source': 'game/mobile/lib/help_content.dart',
        'runtime_selector': entry.value.map((t) => 'HelpTopic.${t.name}').toList(),
        'handbook_title': HelpCopy.title,
        'handbook_intro': HelpCopy.intro,
        'development_notice': HelpCopy.developmentNotice,
        'articles': [
          for (final topic in entry.value)
            {
              'topic': topic.name,
              'title': HelpContent.article(topic).title,
              'summary': HelpContent.article(topic).summary,
              'sections': [
                for (final section in HelpContent.article(topic).sections)
                  {'id': section.id, 'title': section.title, 'paragraphs': section.paragraphs},
              ],
              'actions': [
                for (final action in HelpContent.article(topic).actions)
                  {'id': action.name, 'label': HelpCopy.action(action)},
              ],
            },
        ],
      };
    }
    final out = File(args.single);
    out.parent.createSync(recursive: true);
    out.writeAsStringSync('${const JsonEncoder.withIndent('  ').convert(values)}\n');
}
