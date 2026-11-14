from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os
import threading
import unittest
from playwright.sync_api import sync_playwright


class ParserTests(unittest.TestCase):
    def test_messages_are_safe_and_do_not_retain_previous_patient(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=str(Path(__file__).parent)))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            with sync_playwright() as runner:
                browser = runner.chromium.launch(channel=os.environ.get('BROWSER_CHANNEL') or None)
                page = browser.new_page()
                page.route('https://**/*', lambda route: route.abort())
                page.goto(f'http://127.0.0.1:{server.server_port}/parser.html')
                page.locator('#loadHl7Btn').click()
                page.locator('#parseBtn').click()
                self.assertIn('MOHAMMED', page.locator('#patName').inner_text())
                raw = 'MSH|^~\\&|TEST||||20261114103000\rOBX|1|ST|<img src=x onerror="window.injected=true">||value|unit|range|N'
                page.locator('#rawInput').fill(raw)
                page.locator('#parseBtn').click()
                self.assertEqual(page.locator('#patName').inner_text(), 'N/A')
                self.assertEqual(page.locator('#resultsTableBody tr').count(), 1)
                self.assertEqual(page.locator('#resultsTableBody img').count(), 0)
                self.assertFalse(page.evaluate('Boolean(window.injected)'))
                page.locator('#loadAstmBtn').click()
                page.locator('#parseBtn').click()
                self.assertEqual(page.locator('#ordTime').inner_text(), '2026-07-24 08:30')
                browser.close()
        finally:
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    unittest.main()
