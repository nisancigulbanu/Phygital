# Mobile

Bu klasor Phygital Flutter istemcisini icerir.

## Gelistirme

```bash
flutter pub get
flutter run -d chrome
```

Backend varsayilan olarak `http://127.0.0.1:8000` adresine baglanir. Farkli adres kullanacaksan:

```bash
flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

## Ana Ekranlar

- `lib/screens/capture_screen.dart`: kamera veya galeriden etiket OCR akisi
- `lib/screens/online_product_screen.dart`: urun URL'si veya ekran goruntusu ile analiz akisi
- `lib/screens/review_screen.dart`: kullanicinin son kontrol ve duzeltme ekrani
