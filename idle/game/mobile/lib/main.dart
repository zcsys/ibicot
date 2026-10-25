import 'package:flutter/material.dart';
import 'bootstrap.dart';
import 'study_gate.dart';
import 'font_licenses.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  registerFontLicenses();
  runApp(const StudyGate(child: TideglassBootstrap()));
}
