from backend.services.product_lookup import ProductLookupService


def test_product_lookup_extracts_fabrics_from_embedded_json():
    html = """
    <html>
      <head><title>Demo Knit</title></head>
      <body>
        <script id="__NEXT_DATA__" type="application/json">
          {
            "props": {
              "pageProps": {
                "product": {
                  "name": "Kazak",
                  "composition": "%84 Viskon %16 Polyamid"
                }
              }
            }
          }
        </script>
      </body>
    </html>
    """
    service = ProductLookupService()
    result = service._parse_product_html(html)
    assert result.fabrics == {"viscose": 84, "polyamide": 16}


def test_product_lookup_uses_generic_api_payload_when_static_html_has_no_fabrics():
    class StubProductLookupService(ProductLookupService):
        def _fetch_html(self, url: str) -> str:
            return """
            <html>
              <head><title>Demo Product</title></head>
              <body>
                <script>
                  window.__API__ = "/api/product/123";
                </script>
              </body>
            </html>
            """

        def _fetch_candidate_api_payloads(self, url: str, html: str) -> list[dict]:
            return [
                {
                    "product": {
                        "name": "Demo Product",
                        "fabricComposition": "80% cotton 20% polyester",
                    }
                }
            ]

    service = StubProductLookupService()
    result = service.fetch_product(product_url="https://example.com/product")
    assert result.fabrics == {"cotton": 80, "polyester": 20}
    assert "api" in result.notes.lower() or "json" in result.notes.lower()


def test_product_lookup_uses_dynamic_network_when_static_and_api_fail():
    class StubProductLookupService(ProductLookupService):
        def _fetch_html(self, url: str) -> str:
            return "<html><head><title>Demo Knit</title></head><body></body></html>"

        def _fetch_candidate_api_payloads(self, url: str, html: str) -> list[dict]:
            return []

        def _capture_dynamic_network_sources(self, url: str) -> tuple[list[str], str]:
            return (
                ["49% polyester 30% wool 21% acrylic"],
                "<html><head><title>Demo Knit</title></head><body></body></html>",
            )

    service = StubProductLookupService()
    result = service.fetch_product(product_url="https://example.com/product")
    assert result.fabrics == {"polyester": 49, "wool": 30, "acrylic": 21}
    assert "ag" in result.notes.lower() or "dinamik veri" in result.notes.lower()


def test_product_lookup_survives_static_fetch_error_and_uses_dynamic_network():
    class StubProductLookupService(ProductLookupService):
        def _fetch_html(self, url: str) -> str:
            raise RuntimeError("403 forbidden")

        def _capture_dynamic_network_sources(self, url: str) -> tuple[list[str], str]:
            return (
                ["80% cotton 20% polyester"],
                "<html><head><title>Recovered Product</title></head><body></body></html>",
            )

    service = StubProductLookupService()
    result = service.fetch_product(product_url="https://example.com/product")
    assert result.fabrics == {"cotton": 80, "polyester": 20}
    assert "dinamik veri" in result.notes.lower() or "ag" in result.notes.lower()


def test_product_lookup_uses_dynamic_render_when_static_html_has_no_fabrics():
    class StubProductLookupService(ProductLookupService):
        def _fetch_html(self, url: str) -> str:
            return "<html><head><title>Demo Knit</title></head><body><button>Malzemeler ve bakim</button></body></html>"

        def _fetch_candidate_api_payloads(self, url: str, html: str) -> list[dict]:
            return []

        def _capture_dynamic_network_sources(self, url: str) -> tuple[list[str], str]:
            return [], ""

        def _fetch_rendered_html(self, url: str) -> str:
            return """
            <html>
              <head><title>Demo Knit</title></head>
              <body>
                <button>Malzemeler ve bakim</button>
                <section>49% polyester, 30% yun, 21% akrilik</section>
              </body>
            </html>
            """

    service = StubProductLookupService()
    result = service.fetch_product(product_url="https://example.com/product")
    assert result.fabrics == {"polyester": 49, "wool": 30, "acrylic": 21}
    assert "dinamik" in result.notes.lower()
