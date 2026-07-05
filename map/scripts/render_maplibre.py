"""Screenshot MapLibre GL renders of vector-tile styles for the Cayce bbox."""

from pathlib import Path

from playwright.sync_api import sync_playwright

from maptools import CAYCE_BBOX, mercator_aspect

STYLES = {
    "positron": "https://tiles.openfreemap.org/styles/positron",
    "bright": "https://tiles.openfreemap.org/styles/bright",
    "liberty": "https://tiles.openfreemap.org/styles/liberty",
}
ROOT = Path(__file__).resolve().parent.parent  # map/
WIDTH = 1600
HEIGHT = round(WIDTH * mercator_aspect(CAYCE_BBOX))


def render(name: str, style_url: str) -> Path:
    out = ROOT / "previews" / f"{name}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    page_url = (ROOT / "scripts" / "maplibre.html").as_uri() + f"?style={style_url}"
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(
            viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=2
        )
        page.goto(page_url)
        page.wait_for_function("window._mapReady === true", timeout=120_000)
        page.screenshot(path=str(out))
        browser.close()
    return out


if __name__ == "__main__":
    for name, url in STYLES.items():
        print(f"saved {render(name, url)}")
