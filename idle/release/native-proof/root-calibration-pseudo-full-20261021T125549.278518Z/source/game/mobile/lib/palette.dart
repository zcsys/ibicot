import 'package:flutter/material.dart';

abstract final class TideColors {
  static const deep = Color(0xFF071923);
  static const panel = Color(0xFF102A37);
  static const raised = Color(0xFF173643);
  static const line = Color(0xFF294753);
  static const teal = Color(0xFF79E0CC);
  static const amber = Color(0xFFF4CA88);
  static const text = Color(0xFFE6EEE9);
  static const muted = Color(0xFFA1BAC3);
  static const warning = Color(0xFFFFAE9A);
}

ThemeData tideglassTheme() => ThemeData(
  useMaterial3: true,
  brightness: Brightness.dark,
  scaffoldBackgroundColor: TideColors.deep,
  colorScheme: const ColorScheme.dark(
    primary: TideColors.teal,
    onPrimary: TideColors.deep,
    secondary: TideColors.amber,
    secondaryContainer: TideColors.raised,
    onSecondaryContainer: TideColors.teal,
    surface: TideColors.panel,
    onSurface: TideColors.text,
    error: TideColors.warning,
  ),
  textTheme: const TextTheme(
    headlineLarge: TextStyle(
      fontSize: 36,
      fontWeight: FontWeight.w400,
      letterSpacing: -1,
    ),
    headlineMedium: TextStyle(
      fontSize: 28,
      fontWeight: FontWeight.w400,
      letterSpacing: -.5,
    ),
    titleLarge: TextStyle(fontSize: 21, fontWeight: FontWeight.w500),
    titleMedium: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
    bodyLarge: TextStyle(fontSize: 16, height: 1.45),
    bodyMedium: TextStyle(fontSize: 14, height: 1.45),
    labelLarge: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
    labelSmall: TextStyle(
      fontSize: 10,
      letterSpacing: 1.6,
      fontWeight: FontWeight.w600,
    ),
  ).apply(bodyColor: TideColors.text, displayColor: TideColors.text),
  filledButtonTheme: FilledButtonThemeData(
    style: FilledButton.styleFrom(
      minimumSize: const Size(48, 48),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    ),
  ),
  outlinedButtonTheme: OutlinedButtonThemeData(
    style: OutlinedButton.styleFrom(
      minimumSize: const Size(48, 48),
      side: const BorderSide(color: TideColors.line),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    ),
  ),
  iconButtonTheme: IconButtonThemeData(
    style: IconButton.styleFrom(minimumSize: const Size(48, 48)),
  ),
  navigationBarTheme: const NavigationBarThemeData(
    backgroundColor: TideColors.deep,
    indicatorColor: TideColors.raised,
    height: 74,
    labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
  ),
  dividerTheme: const DividerThemeData(color: TideColors.line, space: 1),
  dialogTheme: DialogThemeData(
    backgroundColor: TideColors.panel,
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
  ),
);
