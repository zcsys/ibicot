"""Register the two actual local page drafts without granting publication approval."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
HERE = Path('release/public-pages')


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.links = []
        self.text = []
        self.resources = []
        self.forbidden = []
        self.heading_count = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            assert attrs['id'] not in self.ids, 'Duplicate page id'
            self.ids.add(attrs['id'])
        if tag == 'a':
            self.links.append(attrs['href'])
        if tag in ('script', 'form', 'iframe', 'input'):
            self.forbidden.append(tag)
        if tag == 'link':
            self.resources.append(attrs['href'])
        if tag == 'h1':
            self.heading_count += 1

    def handle_data(self, data):
        text = data.strip()
        if text:
            self.text.append(text)


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def write(path, value):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if isinstance(value, str) else json.dumps(value, indent=2) + '\n')


def main():
    mapping = {'support.support_page': 'index.html', 'support.privacy_page': 'privacy.html'}
    pages = {}
    for name in mapping.values():
        page = Page()
        page.feed((ROOT / HERE / 'dist' / name).read_text())
        assert not page.forbidden and page.heading_count == 1
        assert page.resources == ['site.css']
        pages[name] = page
    links = 0
    for name, page in pages.items():
        for link in page.links:
            target = urlsplit(link)
            assert not target.scheme and not target.netloc and not target.query
            destination = target.path or name
            assert destination in pages
            assert not target.fragment or target.fragment in pages[destination].ids
            links += 1
    contract = json.loads((ROOT / 'implementation/art/production_contract.json').read_text())
    contracts = {a['asset_id']: a for a in contract['assets']}
    records = []
    for entity, filename in mapping.items():
        asset = 'asset.' + entity
        c = contracts[asset]
        actual = str(HERE / 'dist' / filename)
        source = c['source_descriptor_path']
        export = c['export_descriptor_path']
        content = {
            'schema_version': 1, 'locale': 'en-US', 'content_id': entity,
            'publication_status': 'local_draft_not_published',
            'actual_page': actual, 'actual_page_sha256': sha(actual),
            'visible_text_segments': pages[filename].text,
            'links': pages[filename].links,
            'descriptor_loaded_by_client': False,
            'native_public_url': None,
        }
        write(source, '# ' + entity + '\n\nLocal draft; not a published policy or support service.\n\n'
              + 'Actual HTML: `' + actual + '`. The following text segments are extracted from that file.\n\n'
              + '\n\n'.join(pages[filename].text) + '\n')
        write(export, content)
        inputs = [source, actual, str(HERE / 'dist/site.css'), str(HERE / 'publication.json'),
                  'game/mobile/lib/help_content.dart', 'services/docs/PRIVACY.md',
                  'game/platform/lib/soundtrack_cache.dart', 'game/platform/lib/study_recorder.dart',
                  'game/mobile/lib/study_gate.dart']
        provenance = {
            'asset_id': asset, 'author_or_tool': '/root; original Tideglass development prose and HTML/CSS',
            'creation_date': '2026-10-21', 'source_kind': 'original_project_authored_text',
            'source_media_paths': inputs, 'source_media_sha256': {p: sha(p) for p in inputs},
            'license_or_authorship_basis': 'Original project-authored text, system fonts and CSS; no quoted external prose or imported artwork. This is authorship traceability, not legal or publication approval.',
            'license_evidence_paths': [source, actual, str(HERE / 'dist/site.css')],
            'allowed_uses': ['local_project_development_and_review'],
            'distribution_terms_approval': {'status': 'not_recorded', 'owner': None, 'evidence': None},
            'attribution_text': 'Original Tideglass project prose and code.',
            'reference_asset_permissions': [],
            'export_tool_and_version': 'register_pages.py v1; Python HTMLParser text extraction',
            'exported_paths': [export, actual], 'exported_sha256': {p: sha(p) for p in [export, actual]},
            'reviewer': None, 'review_evidence': None, 'author_report': str(HERE / 'AUTHOR_REPORT.md'),
            'status': 'in_production', 'production_acceptance': False,
            'original_required_variants': c['required_variants'],
            'variant_acceptance': {v: 'open_independent_complete_variant_acceptance' for v in c['required_variants']},
            'publication_status': 'local_only_operator_contacts_policy_and_live_links_pending',
            'original_delivery_channel': c['delivery_channel'],
            'actual_current_delivery': 'Local HTML preview only; no live URL or native link configured',
        }
        write(c['provenance_path'], provenance)
        records.append({'asset_id': asset, 'source': source, 'actual_page': actual, 'export': export,
                        'provenance': c['provenance_path'], 'publication_accepted': False})
    write(HERE / 'evidence/registration.json', {'assets': records, 'internal_links_checked': links,
          'all_link_targets_exist': True, 'forms_scripts_external_resources': False,
          'page_hashes': {name: sha(str(HERE / 'dist' / name)) for name in pages},
          'stylesheet_sha256': sha(str(HERE / 'dist/site.css'))})
    print(f'Registered {len(records)} local drafts; {links} valid internal links. No publication or asset acceptance.')


if __name__ == '__main__':
    main()
