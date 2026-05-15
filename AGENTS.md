# AGENTS.md - Akilli Tekstil Alisveris Asistani

Bu dosya proje mimarisinin referansini tutar. Proje, kamera veya urun etiketi goruntusunu OCR ile okuyup NLP parser, kalite skoru motoru, alternatif onerileri ve LLM tavsiyesi ile tamamlanan bir analiz hattina sahip olacak sekilde duzenlenmistir.

## Hedef Akis

`Mobil Uygulama -> FastAPI -> OCR -> NLP Parser -> Quality Engine -> Similarity Engine -> LLM Advice`

## Backend Endpointleri

- `POST /api/v1/scan`
- `GET /api/v1/health`
- `POST /api/v1/chat`
- `GET /api/v1/alternatives`

## Servisler

- `backend/services/ocr_service.py`
- `backend/services/nlp_parser.py`
- `backend/services/quality_engine.py`
- `backend/services/similarity_engine.py`
- `backend/services/llm_service.py`

## Notlar

- OCR tarafinda demo modunda base64 icinde UTF-8 metin de kabul edilir; bu test kolayligi icindir.
- LLM entegrasyonu `ANTHROPIC_API_KEY` varsa aktif olur, yoksa kurala dayali fallback kullanilir.
- Eski `/analyze` ve `/extract-product` endpointleri geriye donuk uyumluluk icin korunur.
