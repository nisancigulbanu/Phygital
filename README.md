# Phygital

Phygital, tekstil etiketini veya urun sayfasini analiz edip kumas bilesimini, kalite skorunu, fiyat/performans degerini ve daha iyi alternatifleri ureten bir demo alisveris asistani.

## Yapi

- `backend/`: FastAPI API gateway, OCR/NLP/quality/LLM servisleri ve testler
- `mobile/`: Flutter istemcisi
- `data/`: demo veri dosyalari
- `docs/`: ek teknik dokumanlar
- `scripts/`: yerel backend/frontend baslatma scriptleri

## Hizli Baslangic

### Backend

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Windows'ta hazir script ile baslatmak istersen:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_backend.ps1
```

`start_backend.ps1`, once proje icindeki `.venv` Python'unu kullanmaya calisir. Gerekirse `PHYGITAL_PYTHON` ile override edebilirsin.

### Mobile

```bash
cd mobile
flutter pub get
flutter run -d chrome
```

Windows script'i varsayilan olarak Chrome acacak sekilde kullanabilirsin:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_frontend_windows.ps1
```

Farkli cihaz icin:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_frontend_windows.ps1 -Device windows
```

## Ortam Degiskenleri

Kokteki `.env.example` dosyasini `.env` olarak kopyalayin. Demo modunda sadece temel backend akisi calisir; `ANTHROPIC_API_KEY` tanimliysa tavsiye ve chat yanitlari API uzerinden uretilir.

## API

- `GET /api/v1/health`
- `POST /api/v1/scan`
- `POST /api/v1/chat`
- `GET /api/v1/alternatives`
- `POST /extract-product`

Uyumluluk icin eski endpointler de korunur:

- `POST /analyze`

## Notlar

- Urun linki okuma akisi statik HTML, gomulu JSON ve dinamik render fallback'leri ile calisir.
- Dinamik site destegi kullandigin Python ortamindaki opsiyonel scraping bagimliliklarina baglidir.
