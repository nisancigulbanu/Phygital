# FabricScan

FabricScan, tekstil etiketini tarayip kumas bilesimini, kalite skorunu, fiyat/performans degerini ve daha iyi alternatifleri ureten bir demo alisveris asistani.

## Yapi

- `backend/`: FastAPI API gateway, OCR/NLP/quality/LLM servisleri ve testler
- `mobile/`: Flutter istemcisi
- `data/`: demo veri dosyalari
- `docs/`: ek teknik dokumanlar

## Hizli Baslangic

### Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

### Mobile

```bash
cd mobile
flutter pub get
flutter run
```

## Ortam Degiskenleri

Kokteki `.env.example` dosyasini `.env` olarak kopyalayin. Demo modunda sadece temel backend akisi calisir; `ANTHROPIC_API_KEY` tanimliysa tavsiye ve chat yanitlari API uzerinden uretilir.

## API

- `GET /api/v1/health`
- `POST /api/v1/scan`
- `POST /api/v1/chat`
- `GET /api/v1/alternatives`

Uyumluluk icin eski endpointler de korunur:

- `POST /analyze`
- `POST /extract-product`
