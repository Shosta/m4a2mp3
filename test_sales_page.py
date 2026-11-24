import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import urlopen


ROOT = Path(__file__).parent
SCRIPT = ROOT / "docs/assets/site.js"
HTML = ROOT / "docs/index.html"


class SalesPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.html = HTML.read_text(encoding="utf-8")
        cls.dictionaries = dict(re.findall(r"\b(fr|en|da):\s*\{(.*?)\n\s*\}", cls.script, re.S))

    def test_translations_have_matching_keys(self):
        self.assertEqual(set(self.dictionaries), {"fr", "en", "da"})
        keys_by_language = [set(re.findall(r"^\s{4}([\w-]+):", body, re.M)) for body in self.dictionaries.values()]
        self.assertTrue(all(keys == keys_by_language[0] for keys in keys_by_language[1:]))

    def test_page_translation_references_exist_in_every_language(self):
        referenced_keys = set(re.findall(r'data-i18n(?:-[\w-]+)?="([\w-]+)"', self.html))
        self.assertTrue(referenced_keys)
        for body in self.dictionaries.values():
            defined_keys = set(re.findall(r"^\s{4}([\w-]+):", body, re.M))
            self.assertLessEqual(referenced_keys, defined_keys)

    def test_translations_explain_formats_and_ffmpeg_requirement(self):
        self.assertIn("M4A, WAV et AIFF", self.script)
        self.assertIn("M4A, WAV, and AIFF", self.script)
        self.assertIn("M4A-, WAV- og AIFF-filer (AIF)", self.script)
        self.assertEqual(self.script.count("FFmpeg"), 6)
        self.assertEqual(self.script.count("PATH"), 3)
        self.assertEqual(self.script.count("Python 3.9"), 3)
        self.assertIn(".aif", (ROOT / "core.py").read_text(encoding="utf-8"))

    def test_appimage_and_repository_links_are_present(self):
        self.assertIn("https://github.com/Shosta/m4a2mp3/releases", self.html)
        self.assertIn("https://github.com/Shosta/m4a2mp3", self.html)
        self.assertIn("AppImage", self.script)

    def test_hero_carousel_uses_three_screenshots_in_order(self):
        paths = [
            "assets/m4a2mp3 - 1.png",
            "assets/m4a2mp3 - 2.png",
            "assets/m4a2mp3 - 3.png",
        ]
        positions = [self.html.index(path) for path in paths]
        self.assertEqual(positions, sorted(positions))
        self.assertTrue(all((ROOT / "docs" / path).is_file() for path in paths))
        self.assertIn("data-carousel", self.html)
        self.assertIn("data-carousel-previous", self.html)
        self.assertIn("data-carousel-next", self.html)
        self.assertEqual(self.html.count("data-carousel-slide="), 3)

    def test_carousel_has_manual_and_timed_navigation(self):
        self.assertIn("data-carousel-previous", self.script)
        self.assertIn("data-carousel-next", self.script)
        self.assertIn("data-carousel-slide", self.script)
        self.assertIn("5000", self.script)
        self.assertIn("prefers-reduced-motion: reduce", self.script)
        self.assertIn("mouseenter", self.script)
        self.assertIn("focusin", self.script)

    def test_app_icon_is_used_as_favicon(self):
        self.assertIn('<link rel="icon" type="image/png" href="assets/m4a2mp3.png">', self.html)
        self.assertTrue((ROOT / "docs/assets/m4a2mp3.png").is_file())

    def test_relative_assets_and_no_external_runtime_dependencies(self):
        self.assertIn('href="assets/site.css"', self.html)
        self.assertIn('src="assets/site.js"', self.html)
        self.assertNotIn("@import url(", (ROOT / "docs/assets/site.css").read_text(encoding="utf-8"))
        base = "https://example.github.io/project/"
        self.assertEqual(urljoin(base, "assets/site.css"), "https://example.github.io/project/assets/site.css")
        self.assertEqual(urljoin(base, "assets/site.js"), "https://example.github.io/project/assets/site.js")

    @unittest.skipUnless(shutil.which("chromium"), "Chromium is not installed")
    def test_carousel_controls_rotation_and_pause_in_chromium(self):
        probe = ROOT / "docs/.carousel-check.html"
        probe.write_text(
            """<!doctype html><iframe id=\"site\" src=\"/\"></iframe><pre id=\"result\"></pre>
<script>
const frame = document.querySelector('#site');
frame.onload = () => {
  const page = frame.contentWindow;
  const doc = page.document;
  const active = () => [...doc.querySelectorAll('[data-carousel-panel]')].findIndex(slide => !slide.hidden);
  const result = { initial: active() };
  doc.querySelector('[data-carousel-next]').click();
  result.next = active();
  doc.querySelector('[data-carousel-slide="0"]').click();
  result.indicator = active();
  doc.querySelector('[data-carousel-slide="2"]').click();
  const language = doc.querySelector('.language-picker');
  language.value = 'da';
  language.dispatchEvent(new page.Event('change', { bubbles: true }));
  result.translatedCaption = doc.querySelector('[data-carousel-caption]').textContent;
  language.value = 'fr';
  language.dispatchEvent(new page.Event('change', { bubbles: true }));
  page.setTimeout(() => {
    result.automatic = active();
    doc.querySelector('[data-carousel]').dispatchEvent(new page.MouseEvent('mouseenter'));
    page.setTimeout(() => {
      result.paused = active();
      document.querySelector('#result').textContent = JSON.stringify(result);
    }, 5200);
  }, 5200);
};
</script>""",
            encoding="utf-8",
        )
        try:
            output = subprocess.run(
                [
                    "chromium", "--headless", "--no-sandbox", "--disable-gpu",
                    "--dump-dom", "--virtual-time-budget=12000",
                    "http://127.0.0.1:8000/.carousel-check.html",
                ],
                check=True, capture_output=True, text=True,
            ).stdout
        finally:
            probe.unlink(missing_ok=True)
        match = re.search(r'<pre id="result">(.*?)</pre>', output, re.S)
        self.assertIsNotNone(match, output)
        self.assertEqual(json.loads(match.group(1)), {
            "initial": 0,
            "next": 1,
            "indicator": 0,
            "translatedCaption": "SIDE B · DINE KONVERTEREDE MP3-FILER",
            "automatic": 0,
            "paused": 0,
        })

    @unittest.skipUnless(shutil.which("chromium"), "Chromium is not installed")
    def test_language_switch_and_mobile_width_in_chromium(self):
        probe = ROOT / "docs/.browser-check.html"
        probe.write_text(
            """<!doctype html><iframe id=\"site\" style=\"width:390px;height:844px;border:0\" src=\"/\"></iframe><pre id=\"result\"></pre>
<script>
const frame = document.querySelector('#site');
frame.onload = () => {
  const page = frame.contentWindow;
  if (page.document.documentElement.lang === 'fr') {
      const select = page.document.querySelector('.language-picker');
      select.value = 'da';
      select.dispatchEvent(new Event('change', { bubbles: true }));
      const result = {
        lang: page.document.documentElement.lang,
        title: page.document.title,
        active: select.value,
      saved: page.localStorage.getItem('m4a2mp3-language'),
      width: page.document.documentElement.scrollWidth,
      viewport: page.innerWidth
    };
    document.querySelector('#result').textContent = JSON.stringify(result);
    frame.src = '/';
  } else {
    document.querySelector('#result').dataset.restored = page.document.documentElement.lang;
    document.querySelector('#result').dataset.title = page.document.title;
  }
};
</script>""",
            encoding="utf-8",
        )
        try:
            output = subprocess.run(
                [
                    "chromium", "--headless", "--no-sandbox", "--disable-gpu",
                    "--dump-dom", "--virtual-time-budget=3000", "--window-size=390,844",
                    "http://127.0.0.1:8000/.browser-check.html",
                ],
                check=True, capture_output=True, text=True,
            ).stdout
        finally:
            probe.unlink(missing_ok=True)
        match = re.search(r'<pre id="result" data-restored="([^"]+)" data-title="([^"]*)">(.*?)</pre>', output, re.S)
        self.assertIsNotNone(match, output)
        data = json.loads(match.group(3))
        self.assertEqual(data["lang"], "da")
        self.assertEqual(data["active"], "da")
        self.assertEqual(data["saved"], "da")
        self.assertLessEqual(data["width"], data["viewport"])
        self.assertEqual(match.group(1), "da")
        self.assertIn("klar til at tage med", match.group(2))


if __name__ == "__main__":
    unittest.main()
