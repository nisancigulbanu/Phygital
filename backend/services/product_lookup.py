from __future__ import annotations

from html import unescape
from html.parser import HTMLParser
import json
import re
from typing import Any
from urllib.parse import urljoin
from urllib.request import Request, urlopen

try:  # pragma: no cover - optional dependency
    import httpx
except ImportError:  # pragma: no cover
    httpx = None

try:  # pragma: no cover - optional dependency
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    PlaywrightTimeoutError = None
    sync_playwright = None

try:  # pragma: no cover - optional dependency
    from selenium import webdriver
    from selenium.common.exceptions import TimeoutException as SeleniumTimeoutException
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
except ImportError:  # pragma: no cover
    webdriver = None
    SeleniumTimeoutException = None
    ChromeOptions = None
    By = None
    EC = None
    WebDriverWait = None

from backend.schemas import ProductLookupResponse
from backend.utils.fabric_parser import extract_fabrics_from_text
from backend.utils.text_normalization import repair_mojibake


class _HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        value = data.strip()
        if value:
            self.parts.append(value)

    def text(self) -> str:
        return " ".join(self.parts)


class ProductLookupService:
    def __init__(self, timeout: float = 10.0, render_timeout: float = 20.0):
        self.timeout = timeout
        self.render_timeout = render_timeout

    def fetch_product(self, *, product_url: str = "", page_text: str = "") -> ProductLookupResponse:
        resolved_url = product_url.strip()
        html = ""
        fetch_error = False
        if resolved_url:
            try:
                html = self._fetch_html(resolved_url)
            except Exception:
                fetch_error = True
        elif page_text.strip():
            html = page_text

        static_result = self._parse_product_html(html, base_url=resolved_url)
        if not resolved_url or self._has_fabrics(static_result):
            if fetch_error and not static_result.notes:
                static_result.notes = "Sayfa dogrudan indirilemedi; eldeki veri sinirli olabilir."
            return static_result

        api_result = self._try_generic_api_pipeline(resolved_url, html, fallback=static_result)
        if self._has_fabrics(api_result):
            return api_result

        network_result = self._try_dynamic_network_pipeline(resolved_url, fallback=api_result)
        if self._has_fabrics(network_result):
            return network_result

        rendered_result = self._try_rendered_dom_pipeline(resolved_url, fallback=network_result)
        if fetch_error and not self._has_fabrics(rendered_result):
            rendered_result.notes = (
                "Sayfa dogrudan indirilemedi veya urun bilgisi engellendi; dinamik okumalar denendi ama yeterli veri bulunamadi."
            )
        return rendered_result

    def _try_generic_api_pipeline(
        self,
        url: str,
        html: str,
        *,
        fallback: ProductLookupResponse,
    ) -> ProductLookupResponse:
        payloads = list(self._extract_embedded_json_objects(html))
        payloads.extend(self._fetch_candidate_api_payloads(url, html))

        if not payloads:
            return fallback

        text_sources = self._extract_text_sources(html)
        for payload in payloads:
            text_sources.extend(self._collect_relevant_strings(payload))

        result = self._response_from_sources(
            text_sources,
            html=html,
            base_url=url,
            note_if_found="Kumas bilgisi statik HTML veya gomulu API/JSON verisinden cikarildi.",
            note_if_missing=fallback.notes,
        )
        return self._merge_results(fallback, result)

    def _try_dynamic_network_pipeline(
        self,
        url: str,
        *,
        fallback: ProductLookupResponse,
    ) -> ProductLookupResponse:
        network_sources, final_html = self._capture_dynamic_network_sources(url)
        if not network_sources and not final_html:
            return fallback

        text_sources = list(network_sources)
        if final_html:
            text_sources.extend(self._extract_text_sources(final_html))

        result = self._response_from_sources(
            text_sources,
            html=final_html or "",
            base_url=url,
            note_if_found="Kumas bilgisi tarayici ag isteklerinden veya dinamik veri cevaplarindan cikarildi.",
            note_if_missing=fallback.notes,
        )
        return self._merge_results(fallback, result)

    def _try_rendered_dom_pipeline(
        self,
        url: str,
        *,
        fallback: ProductLookupResponse,
    ) -> ProductLookupResponse:
        rendered_html = self._fetch_rendered_html(url)
        if not rendered_html:
            return fallback

        result = self._parse_product_html(rendered_html, base_url=url)
        if result.fabrics:
            result.notes = "Kumas dagilimi dinamik render sonrasi DOM metninden cikarildi."
        return self._merge_results(fallback, result)

    def _parse_product_html(self, html: str, *, base_url: str = "") -> ProductLookupResponse:
        html = repair_mojibake(html)
        text_sources = self._extract_text_sources(html)
        return self._response_from_sources(
            text_sources,
            html=html,
            base_url=base_url,
            note_if_found="Urun sayfasindaki metinden veya gomulu veri bloklarindan kumas dagilimi cikarildi.",
            note_if_missing="Kumas bilgisi sayfada net bulunamadi; gorsel ya da urun aciklamasi ile elle kontrol etmek gerekebilir.",
        )

    def _response_from_sources(
        self,
        text_sources: list[str],
        *,
        html: str,
        base_url: str,
        note_if_found: str,
        note_if_missing: str,
    ) -> ProductLookupResponse:
        raw_text = "\n".join(source for source in text_sources if source).strip()
        fabrics = self._extract_fabrics(text_sources)
        title = self._extract_title(html)
        brand = self._extract_brand(html, title)
        price = self._extract_price(html)
        image_url = self._extract_image_url(html, base_url)
        return ProductLookupResponse(
            title=title,
            brand=brand,
            price=price,
            image_url=image_url,
            fabrics=fabrics,
            extracted_text=raw_text[:3000],
            notes=note_if_found if fabrics else note_if_missing,
        )

    def _fetch_html(self, url: str) -> str:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        if httpx is not None:
            response = httpx.get(
                url,
                timeout=self.timeout,
                headers=headers,
                follow_redirects=True,
            )
            response.raise_for_status()
            return response.text

        request_obj = Request(url, headers=headers)
        with urlopen(request_obj, timeout=self.timeout) as response:
            return response.read().decode("utf-8", errors="ignore")

    def _fetch_rendered_html(self, url: str) -> str:
        rendered_html = self._fetch_rendered_html_with_playwright(url)
        if rendered_html:
            return rendered_html
        return self._fetch_rendered_html_with_selenium(url)

    def _capture_dynamic_network_sources(self, url: str) -> tuple[list[str], str]:
        return self._capture_dynamic_network_sources_with_playwright(url)

    def _capture_dynamic_network_sources_with_playwright(self, url: str) -> tuple[list[str], str]:
        if sync_playwright is None or PlaywrightTimeoutError is None:
            return [], ""

        timeout_ms = int(self.render_timeout * 1000)
        captured_sources: list[str] = []
        final_html = ""

        def _store_response(response: Any) -> None:
            try:
                resource_type = response.request.resource_type
            except Exception:
                resource_type = ""
            if resource_type not in {"xhr", "fetch", "document"}:
                return

            try:
                content_type = (response.headers or {}).get("content-type", "").lower()
            except Exception:
                content_type = ""

            if "json" in content_type:
                try:
                    payload = response.json()
                except Exception:
                    try:
                        payload = json.loads(response.text())
                    except Exception:
                        payload = None
                if payload is not None:
                    captured_sources.extend(self._collect_relevant_strings(payload))
                    return

            try:
                body = response.text()
            except Exception:
                body = ""
            if self._looks_like_relevant_text(body):
                captured_sources.append(body)

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page(
                    locale="tr-TR",
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
                    ),
                )
                page.on("response", _store_response)
                page.goto(url, wait_until="networkidle", timeout=timeout_ms)
                page.wait_for_timeout(1500)
                page.evaluate(self._expand_details_script())
                page.wait_for_timeout(1200)
                final_html = page.content()
                browser.close()
        except Exception:
            return [], ""

        return self._dedupe_strings(captured_sources), final_html

    def _fetch_rendered_html_with_playwright(self, url: str) -> str:
        if sync_playwright is None or PlaywrightTimeoutError is None:
            return ""

        timeout_ms = int(self.render_timeout * 1000)
        script = self._expand_details_script()

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page(
                    locale="tr-TR",
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
                    ),
                )
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                page.wait_for_timeout(1500)
                page.evaluate(script)
                page.wait_for_timeout(1200)
                content = page.content()
                browser.close()
                return content
        except Exception:
            return ""

    def _fetch_rendered_html_with_selenium(self, url: str) -> str:
        if (
            webdriver is None
            or ChromeOptions is None
            or By is None
            or WebDriverWait is None
            or EC is None
            or SeleniumTimeoutException is None
        ):
            return ""

        options = ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--lang=tr-TR")
        options.add_argument("--window-size=1440,2400")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        )

        driver = None
        try:
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(self.render_timeout)
            driver.get(url)

            wait = WebDriverWait(driver, self.render_timeout)
            wait.until(lambda current_driver: current_driver.execute_script("return document.readyState") == "complete")

            buttons = driver.find_elements(By.CSS_SELECTOR, "button, summary, [role='button'], [aria-controls]")
            for button in buttons:
                text = (button.text or "").strip().lower()
                if not text:
                    continue
                if any(
                    token in text
                    for token in ("malzeme", "bakim", "bakÄ±m", "material", "care", "composition", "kumas", "urun bilgileri")
                ):
                    try:
                        driver.execute_script("arguments[0].click();", button)
                    except Exception:
                        continue

            try:
                wait.until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            "//*[contains(translate(normalize-space(.), "
                            "'ABCDEFGHIJKLMNOPQRSTUVWXYZÃ‡ÄžÄ°Ã–ÅžÃœ', "
                            "'abcdefghijklmnopqrstuvwxyzÃ§ÄŸiÃ¶ÅŸÃ¼'), '%')]",
                        )
                    )
                )
            except SeleniumTimeoutException:
                pass

            return driver.page_source
        except Exception:
            return ""
        finally:
            if driver is not None:
                driver.quit()

    def _extract_text(self, html: str) -> str:
        extractor = _HTMLTextExtractor()
        extractor.feed(unescape(html))
        return extractor.text()

    def _extract_text_sources(self, html: str) -> list[str]:
        sources = [self._extract_text(html)]
        for product in self._extract_product_json_ld_nodes(html):
            sources.extend(self._collect_relevant_strings(product))
        for payload in self._extract_embedded_json_objects(html):
            sources.extend(self._collect_relevant_strings(payload))
        return [source.strip() for source in sources if isinstance(source, str) and source.strip()]

    def _has_fabrics(self, result: ProductLookupResponse) -> bool:
        return bool(result.fabrics)

    def _fetch_candidate_api_payloads(self, url: str, html: str) -> list[dict]:
        payloads: list[dict] = []
        for candidate_url in self._extract_candidate_api_urls(url, html):
            try:
                response_text = self._fetch_html(candidate_url)
            except Exception:
                continue
            payloads.extend(self._parse_json_like_payloads(response_text))
        return payloads

    def _extract_candidate_api_urls(self, url: str, html: str) -> list[str]:
        candidates: list[str] = []
        patterns = (
            r'"(https?://[^"]+?/api/[^"]+)"',
            r'"(https?://[^"]+?/products?[^"]*\.json[^"]*)"',
            r'"(/api/[^"]+)"',
            r'"(/[^"]*products?[^"]*\.json[^"]*)"',
        )
        for pattern in patterns:
            for match in re.findall(pattern, html, re.IGNORECASE):
                resolved = urljoin(url, unescape(match))
                if resolved not in candidates:
                    candidates.append(resolved)
        return candidates[:10]

    def _parse_json_like_payloads(self, payload_text: str) -> list[dict]:
        payload_text = payload_text.strip()
        if not payload_text:
            return []
        try:
            parsed = json.loads(payload_text)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, dict):
            return [parsed]
        if isinstance(parsed, list):
            return [item for item in parsed if isinstance(item, dict)]
        return []

    def _extract_fabrics(self, text_sources: list[str]) -> dict[str, int]:
        best: dict[str, int] = {}
        for source in text_sources:
            parsed = extract_fabrics_from_text(source)
            if sum(parsed.values()) > sum(best.values()):
                best = parsed
        return best

    def _extract_title(self, html: str) -> str:
        for pattern in (
            r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+name=["\']twitter:title["\'][^>]+content=["\']([^"\']+)["\']',
            r"<title>([^<]+)</title>",
        ):
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return unescape(match.group(1)).strip()

        product = self._extract_product_json_ld(html)
        return product.get("name", "").strip()

    def _extract_brand(self, html: str, title: str) -> str:
        meta_match = re.search(
            r'<meta[^>]+(?:name|property)=["\'](?:brand|product:brand)["\'][^>]+content=["\']([^"\']+)["\']',
            html,
            re.IGNORECASE,
        )
        if meta_match:
            return meta_match.group(1).strip().lower()

        product = self._extract_product_json_ld(html)
        brand = product.get("brand")
        if isinstance(brand, dict):
            brand = brand.get("name", "")
        if isinstance(brand, str) and brand.strip():
            return brand.strip().lower()

        if "|" in title:
            return title.split("|")[-1].strip().lower()
        return ""

    def _extract_price(self, html: str) -> float | None:
        meta_patterns = (
            r'<meta[^>]+property=["\']product:price:amount["\'][^>]+content=["\']([^"\']+)["\']',
            r'"price"\s*:\s*"([^"]+)"',
        )
        for pattern in meta_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if not match:
                continue
            value = self._parse_price(match.group(1))
            if value is not None:
                return value

        text_match = re.search(r"(\d+[.,]?\d*)\s*(?:TL|TRY)", html, re.IGNORECASE)
        if text_match:
            return self._parse_price(text_match.group(1))
        return None

    def _extract_image_url(self, html: str, base_url: str) -> str:
        match = re.search(
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            html,
            re.IGNORECASE,
        )
        if not match:
            return ""
        image_url = match.group(1).strip()
        return urljoin(base_url, image_url) if base_url else image_url

    def _extract_product_json_ld(self, html: str) -> dict:
        nodes = self._extract_product_json_ld_nodes(html)
        return nodes[0] if nodes else {}

    def _extract_product_json_ld_nodes(self, html: str) -> list[dict]:
        scripts = re.findall(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            html,
            re.IGNORECASE | re.DOTALL,
        )
        products: list[dict] = []
        for script in scripts:
            try:
                parsed = json.loads(script.strip())
            except json.JSONDecodeError:
                continue

            product = self._find_product_node(parsed)
            if product:
                products.append(product)
        return products

    def _extract_embedded_json_objects(self, html: str) -> list[dict]:
        objects: list[dict] = []
        script_patterns = (
            r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
            r'<script[^>]+type=["\']application/json["\'][^>]*>(.*?)</script>',
        )
        for pattern in script_patterns:
            for match in re.findall(pattern, html, re.IGNORECASE | re.DOTALL):
                try:
                    objects.append(json.loads(match.strip()))
                except json.JSONDecodeError:
                    continue

        assignment_patterns = (
            r'window\.__PRELOADED_STATE__\s*=\s*({.*?})\s*;',
            r'window\.__INITIAL_STATE__\s*=\s*({.*?})\s*;',
        )
        for pattern in assignment_patterns:
            for match in re.findall(pattern, html, re.IGNORECASE | re.DOTALL):
                try:
                    objects.append(json.loads(match))
                except json.JSONDecodeError:
                    continue
        return objects

    def _find_product_node(self, node):
        if isinstance(node, dict):
            if node.get("@type") == "Product":
                return node
            for value in node.values():
                found = self._find_product_node(value)
                if found:
                    return found
        elif isinstance(node, list):
            for item in node:
                found = self._find_product_node(item)
                if found:
                    return found
        return None

    def _collect_relevant_strings(self, node, parent_key: str = "") -> list[str]:
        strings: list[str] = []
        relevant_keys = {
            "composition",
            "material",
            "materials",
            "fabric",
            "fabrics",
            "description",
            "details",
            "attributes",
            "content",
            "specifications",
            "name",
            "fabriccomposition",
            "fibercontent",
            "features",
            "descriptiontext",
        }
        if isinstance(node, dict):
            for key, value in node.items():
                strings.extend(self._collect_relevant_strings(value, str(key).lower()))
        elif isinstance(node, list):
            for item in node:
                strings.extend(self._collect_relevant_strings(item, parent_key))
        elif isinstance(node, str):
            lowered = node.lower()
            if parent_key in relevant_keys or "%" in node or any(
                token in lowered
                for token in (
                    "pamuk",
                    "cotton",
                    "polyester",
                    "viskon",
                    "polyamid",
                    "wool",
                    "linen",
                    "elastane",
                    "akrilik",
                    "acrylic",
                    "kumas",
                    "fabric",
                    "material",
                    "composition",
                )
            ):
                strings.append(node)
        return strings

    def _merge_results(
        self,
        baseline: ProductLookupResponse,
        candidate: ProductLookupResponse,
    ) -> ProductLookupResponse:
        return ProductLookupResponse(
            title=candidate.title or baseline.title,
            brand=candidate.brand or baseline.brand,
            price=candidate.price if candidate.price is not None else baseline.price,
            image_url=candidate.image_url or baseline.image_url,
            fabrics=candidate.fabrics or baseline.fabrics,
            extracted_text=candidate.extracted_text or baseline.extracted_text,
            notes=candidate.notes or baseline.notes,
        )

    def _dedupe_strings(self, values: list[str]) -> list[str]:
        deduped: list[str] = []
        seen: set[str] = set()
        for value in values:
            normalized = value.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(normalized)
        return deduped

    def _looks_like_relevant_text(self, value: str) -> bool:
        lowered = value.lower()
        return any(
            token in lowered
            for token in (
                "pamuk",
                "cotton",
                "polyester",
                "viskon",
                "polyamid",
                "wool",
                "linen",
                "fabric",
                "material",
                "composition",
                "%",
            )
        )

    def _expand_details_script(self) -> str:
        keyword_pattern = (
            "material|materials|composition|fabric|fabrics|care|origin|"
            "malzeme|malzemeler|bakim|bakÄ±m|kumas|kumaÅŸ|icerik|iÃ§erik|urun bilgileri"
        )
        return f"""
        (() => {{
            const pattern = /{keyword_pattern}/i;
            const elements = Array.from(
                document.querySelectorAll('button, summary, [role="button"], [aria-controls]')
            );
            const clicked = [];
            for (const element of elements) {{
                const text = (element.innerText || element.textContent || '').trim();
                if (!text || !pattern.test(text)) {{
                    continue;
                }}
                try {{
                    element.click();
                    clicked.push(text);
                }} catch (error) {{
                }}
            }}
            return clicked;
        }})()
        """

    def _parse_price(self, value: str) -> float | None:
        cleaned = value.strip().replace(" ", "")
        if "," in cleaned and "." in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None
