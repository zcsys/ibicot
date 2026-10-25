#!/usr/bin/env python3
"""Install pinned macOS ARM64 development tools inside .tooling only."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / '.tooling'
FLUTTER_REF = '3.47.7'
FLUTTER_COMMIT = 'abaf9c523780a608bd46686fd5e53740a07077f8'
JAVA_URL = 'https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.20.1%2B1/OpenJDK17U-jdk_aarch64_mac_hotspot_17.0.20.1_1.tar.gz'
JAVA_SHA256 = '196d13ba5f10414bef7f6a05a9b3f00edacb18ebacef2b99485db9e2ee18f0e8'


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--android-sdk-source', type=Path,
                        default=Path.home() / 'Library/Android/sdk')
    args = parser.parse_args()
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        raise SystemExit('This bootstrap is pinned for macOS ARM64; use a reviewed host-specific pin on other hosts.')
    TOOLS.mkdir(exist_ok=True)
    flutter = TOOLS / 'flutter'
    if not flutter.exists():
        run('git', 'clone', '--depth', '1', '--branch', FLUTTER_REF,
            'https://github.com/flutter/flutter.git', str(flutter))
    commit = subprocess.check_output(['git', '-C', str(flutter), 'rev-parse', 'HEAD'], text=True).strip()
    if commit != FLUTTER_COMMIT:
        raise SystemExit(f'Existing Flutter checkout differs from pin: {commit}')

    java = TOOLS / 'java'
    current = java / 'current'
    if not current.exists():
        archive = TOOLS / 'java.tar.gz'
        if not archive.exists() or hashlib.sha256(archive.read_bytes()).hexdigest() != JAVA_SHA256:
            partial = TOOLS / 'java.tar.gz.download'
            run('curl', '--fail', '--location', '--show-error', JAVA_URL, '-o', str(partial))
            if hashlib.sha256(partial.read_bytes()).hexdigest() != JAVA_SHA256:
                raise SystemExit('JDK archive checksum mismatch; no extraction performed.')
            partial.replace(archive)
        java.mkdir(exist_ok=True)
        with tarfile.open(archive) as bundle:
            bundle.extractall(java, filter='data')
        choices = list(java.glob('*/Contents/Home/bin/java'))
        if len(choices) != 1:
            raise SystemExit('Expected exactly one extracted Java runtime.')
        current.symlink_to(choices[0].parents[3].name, target_is_directory=True)

    sdk = TOOLS / 'android-sdk'
    source = args.android_sdk_source.resolve()
    if not (source / 'cmdline-tools/latest/bin/sdkmanager').is_file():
        raise SystemExit('Provide --android-sdk-source with official Android command-line tools. No global SDK is installed by this script.')
    sdk.mkdir(exist_ok=True)
    for name in ['platform-tools', 'cmdline-tools', 'emulator', 'system-images']:
        target = sdk / name
        if (source / name).exists() and not target.exists():
            target.symlink_to(source / name, target_is_directory=True)
    for category in ['platforms', 'build-tools']:
        (sdk / category).mkdir(exist_ok=True)
        for item in (source / category).glob('*'):
            target = sdk / category / item.name
            if not target.exists():
                target.symlink_to(item, target_is_directory=True)
    (sdk / 'licenses').mkdir(exist_ok=True)
    for license_file in (source / 'licenses').glob('*'):
        target = sdk / 'licenses' / license_file.name
        if not target.exists():
            shutil.copy2(license_file, target)
    print(json.dumps({'flutter': FLUTTER_REF, 'flutter_commit': commit,
                      'java_archive_sha256': JAVA_SHA256,
                      'android_sdk': str(sdk), 'existing_sdk_source': str(source)}, indent=2))
    run(str(ROOT / 'tool/flutter'), '--version')


if __name__ == '__main__':
    main()
