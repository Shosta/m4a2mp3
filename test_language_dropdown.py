import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).parent
HTML = ROOT / "docs/index.html"
SCRIPT = ROOT / "docs/assets/site.js"


class LanguageDropdownTests(unittest.TestCase):
    def test_native_select_offers_flags_and_native_language_names(self):
        html = HTML.read_text(encoding="utf-8")
        self.assertRegex(html, r'<select[^>]*class="language-picker"')
        self.assertIn('id="language-picker"', html)
        self.assertIn('value="fr"', html)
        self.assertIn("🇫🇷 Français", html)
        self.assertIn("🇬🇧 English", html)
        self.assertIn("🇩🇰 Dansk", html)

    @unittest.skipUnless(shutil.which("chromium"), "Chromium is not installed")
    def test_selection_changes_document_and_persists_after_reload(self):
        probe = ROOT / "docs/.language-check.html"
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
    document.querySelector('#result').textContent = JSON.stringify({
      lang: page.document.documentElement.lang,
      title: page.document.title,
      selected: select.value,
      saved: page.localStorage.getItem('m4a2mp3-language'),
      width: page.document.documentElement.scrollWidth,
      viewport: page.innerWidth
    });
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
                    "http://127.0.0.1:8000/.language-check.html",
                ],
                check=True, capture_output=True, text=True,
            ).stdout
        finally:
            probe.unlink(missing_ok=True)
        match = re.search(r'<pre id="result" data-restored="([^"]+)" data-title="([^"]*)">(.*?)</pre>', output, re.S)
        self.assertIsNotNone(match, output)
        data = json.loads(match.group(3))
        self.assertEqual(data["lang"], "da")
        self.assertEqual(data["selected"], "da")
        self.assertEqual(data["saved"], "da")
        self.assertLessEqual(data["width"], data["viewport"])
        self.assertEqual(match.group(1), "da")
        self.assertIn("klar til at tage med", match.group(2))


if __name__ == "__main__":
    unittest.main()
