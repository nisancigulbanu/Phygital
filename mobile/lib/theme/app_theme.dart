import 'package:flutter/material.dart';

class AppTheme {
  static ThemeData build() {
    const seed = Color(0xFF184E42);
    const sand = Color(0xFFF6F1E7);

    return ThemeData(
      useMaterial3: true,
      scaffoldBackgroundColor: sand,
      colorScheme: ColorScheme.fromSeed(
        seedColor: seed,
        brightness: Brightness.light,
        primary: seed,
        secondary: const Color(0xFFC98C2E),
        surface: Colors.white,
      ),
      appBarTheme: const AppBarTheme(
        centerTitle: false,
        backgroundColor: sand,
        foregroundColor: Colors.black87,
        elevation: 0,
      ),
      cardTheme: CardThemeData(
        color: Colors.white,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(24),
          side: BorderSide(color: Colors.black.withValues(alpha: 0.06)),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(18),
          borderSide: const BorderSide(color: seed, width: 1.2),
        ),
      ),
    );
  }
}
