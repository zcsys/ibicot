"""Read-only independent local-page checks; writes only its own JSON evidence."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "release/public-pages"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class InspectPage(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.links, self.tags, self.references, self.text = [], [], [], [], []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        self.tags.append(tag)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a":
            self.links.append(attrs.get("href", ""))
        for key in ("src", "href"):
            if key in attrs:
                self.references.append(attrs[key])

    def handle_data(self, data):
        if data.strip():
            self.text.append(data.strip())


def differences(before, after, path=""):
    if type(before) is not type(after):
        return [{"path": path, "before": before, "after": after}]
    if isinstance(before, dict):
        result = []
        for key in sorted(before.keys() | after.keys()):
            if key not in before or key not in after:
                result.append({"path": f"{path}/{key}", "before": before.get(key), "after": after.get(key)})
            else:
                result += differences(before[key], after[key], f"{path}/{key}")
        return result
    if isinstance(before, list):
        assert len(before) == len(after), f"List size changed: {path}"
        return [d for i, (a, b) in enumerate(zip(before, after)) for d in differences(a, b, f"{path}/{i}")]
    return [] if before == after else [{"path": path, "before": before, "after": after}]


def main():
    author_pins = json.loads((HERE / "evidence/author-source-pin.json").read_text())
    mismatches = [p for p, digest in author_pins.items() if sha(ROOT / p) != digest]
    assert not mismatches, mismatches
    pages = {}
    for name in ("index.html", "privacy.html"):
        page = InspectPage()
        page.feed((HERE / "dist" / name).read_text())
        assert len(page.ids) == len(set(page.ids))
        assert Counter(page.tags)["h1"] == 1
        assert not set(page.tags) & {"script", "form", "iframe", "input"}
        assert "#main" in page.links
        assert not any(urlsplit(ref).scheme or urlsplit(ref).netloc for ref in page.references)
        pages[name] = page
    links = []
    for name, page in pages.items():
        for href in page.links:
            target = urlsplit(href)
            path = target.path or name
            assert path in pages and not target.query
            assert not target.fragment or target.fragment in pages[path].ids
            links.append({"page": name, "href": href, "resolved_page": path, "fragment_exists": True})
    http = []
    for name in ("index.html", "privacy.html", "site.css"):
        with urlopen(f"http://127.0.0.1:8779/{name}", timeout=5) as response:
            body = response.read()
            assert response.status == 200
            assert body == (HERE / "dist" / name).read_bytes()
            assert response.headers.get("Set-Cookie") is None
            http.append({"path": name, "status": response.status,
                         "sha256": hashlib.sha256(body).hexdigest(), "set_cookie": False})
    before = json.loads((HERE / "evidence/launch-manifest-before.json").read_text())
    after = json.loads((ROOT / "implementation/content/launch_manifest.json").read_text())
    delta = differences(before, after)
    allowed = set()
    for i, record in enumerate(after["assets"]):
        if record["id"] in {"asset.support.privacy_page", "asset.support.support_page"}:
            allowed |= {f"/assets/{i}/{key}" for key in ("delivery_status", "source_path", "production_evidence")}
            assert record["verification_evidence"] is None and record["license_evidence"] is None
    for i, record in enumerate(after["support_content"]):
        if record["id"] in {"support.privacy_page", "support.support_page"}:
            allowed.add(f"/support_content/{i}/production_status")
            assert record["verification_evidence"] is None
    assert {d["path"] for d in delta} == allowed
    assert len(after["assets"]) == len(before["assets"]) == 164
    publication = json.loads((HERE / "publication.json").read_text())
    assert publication["status"] == "local_draft_not_published"
    assert publication["public_release_authorized"] is False
    for key in ("operator", "support_contact", "privacy_contact", "support_url", "privacy_url",
                "web_deletion_request_url", "approved_backup_retention", "native_sdk_data_audit"):
        assert publication[key] is None
    provenance_checks = []
    for kind, filename in (("privacy_page", "privacy.html"), ("support_page", "index.html")):
        p = ROOT / f"source/provenance/asset.support.{kind}.json"
        record = json.loads(p.read_text())
        assert record["reviewer"] is None and record["review_evidence"] is None
        assert record["production_acceptance"] is False
        assert record["distribution_terms_approval"]["status"] == "not_recorded"
        for source, digest in (record["source_media_sha256"] | record["exported_sha256"]).items():
            assert sha(ROOT / source) == digest, source
        descriptor = json.loads((ROOT / f"game/content/locales/en-US/support.{kind}.json").read_text())
        assert descriptor["visible_text_segments"] == pages[filename].text
        assert descriptor["links"] == pages[filename].links
        assert descriptor["descriptor_loaded_by_client"] is False
        assert descriptor["native_public_url"] is None
        provenance_checks.append({"asset_id": record["asset_id"], "hashes_match": True,
                                  "unapproved_fields_preserved": True, "text_export_matches": True})
    pins = dict(author_pins)
    for path in [HERE / "AUTHOR_REPORT.md", HERE / "evidence/launch-manifest-before.json",
                 HERE / "evidence/registration.json", HERE / "evidence/browser-measures.json",
                 ROOT / "implementation/content/launch_manifest.json"] + list((HERE / "evidence").glob("*.png")):
        pins[str(path.relative_to(ROOT))] = sha(path)
    for record in provenance_checks:
        path = ROOT / "source/provenance" / f"{record['asset_id']}.json"
        pins[str(path.relative_to(ROOT))] = sha(path)
    result = {"scope": "Independent read-only local draft probes; not public policy/release acceptance",
              "reviewer": "/root/art_content_engineer", "source_pin_mismatches": mismatches,
              "internal_links": links, "internal_link_count": len(links), "http_checks": http,
              "exact_manifest_delta": delta, "asset_count": len(after["assets"]),
              "provenance_checks": provenance_checks, "input_sha256": pins,
              "runtime_sources_or_manifest_modified": False, "public_release_accepted": False}
    target = HERE / "independent-probes.json"
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Passed: {len(links)} internal links, three exact HTTP responses, eight allowed manifest fields, two provenance/export records. {len(pins)} inputs pinned.")


if __name__ == "__main__":
    main()
