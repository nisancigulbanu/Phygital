import 'package:flutter/material.dart';

import 'capture_screen.dart';
import 'online_product_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFFF5EFE2), Color(0xFFE4F0E8)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: SafeArea(
          child: ListView(
            padding: const EdgeInsets.all(24),
            children: [
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.75),
                  borderRadius: BorderRadius.circular(28),
                ),
                child: const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Phygital Fashion Advisor',
                      style: TextStyle(fontSize: 32, fontWeight: FontWeight.w700),
                    ),
                    SizedBox(height: 12),
                    Text(
                      'Etiket, online urun linki ya da ekran goruntusu ile kiyafeti analiz et; kumas kalitesini aninda gor ve daha surdurulebilir secimler yap.',
                      style: TextStyle(fontSize: 16, height: 1.5),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: const [
                      Text('Neler yapar?', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
                      SizedBox(height: 12),
                      Text('- Google ML Kit ile etiketi veya ekran goruntusunu okur'),
                      Text('- Urun linkinden isim, fiyat ve kumas bilgisini toplar'),
                      Text('- Kumasi iyi / orta / kotu olarak puanlar'),
                      Text('- Marka etik skoru ve AI yorumu getirir'),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: () {
                    Navigator.of(context).push(
                      MaterialPageRoute<void>(
                        builder: (_) => const CaptureScreen(),
                      ),
                    );
                  },
                  style: FilledButton.styleFrom(minimumSize: const Size.fromHeight(58)),
                  child: const Text('Etiketi Tara'),
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton(
                  onPressed: () {
                    Navigator.of(context).push(
                      MaterialPageRoute<void>(
                        builder: (_) => const OnlineProductScreen(),
                      ),
                    );
                  },
                  style: OutlinedButton.styleFrom(minimumSize: const Size.fromHeight(56)),
                  child: const Text('Online Urun Ekle'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
