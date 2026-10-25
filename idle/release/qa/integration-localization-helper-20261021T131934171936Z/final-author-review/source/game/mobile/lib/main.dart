import 'package:flutter/material.dart';
import 'bootstrap.dart';
import 'study_gate.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const StudyGate(child: TideglassBootstrap()));
}
