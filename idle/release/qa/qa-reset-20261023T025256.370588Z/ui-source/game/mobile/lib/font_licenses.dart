import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

bool _registered = false;

/// Keep the pinned SDK's supplied icon-font notice in the existing Licenses UI.
/// This adds attribution without changing, replacing or relicensing the font.
void registerFontLicenses() {
  if (_registered) return;
  _registered = true;
  LicenseRegistry.addLicense(materialIconLicenses);
}

Stream<LicenseEntry> materialIconLicenses() async* {
  final notice = await rootBundle.loadString(
    'assets/licenses/MaterialIcons_LICENSE.txt',
  );
  yield LicenseEntryWithLineBreaks(
    const ['Google Material icons'],
    'Material icons by Google. Bundled through the pinned Flutter SDK. '
    'Tideglass has not changed the source font; Flutter may subset glyphs '
    'when exporting release builds.\n\n'
    'https://developers.google.com/fonts/docs/material_icons\n\n'
    'The following is the exact license notice supplied with this SDK font.\n\n'
    '$notice',
  );
}
