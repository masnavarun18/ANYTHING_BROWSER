import unittest
from src.content_filter import ContentFilter, strip_html_css_js


class TestContentFilter(unittest.TestCase):
    def setUp(self):
        self.filter = ContentFilter()

    def test_strip_script_tags(self):
        raw_html = """
        <html>
            <head>
                <script type="text/javascript">
                    alert("Malicious script!");
                    console.log("analytics");
                </script>
                <title>Test Page</title>
            </head>
            <body>
                <h1>Welcome</h1>
                <script>document.write("hidden");</script>
                <p>This is safe content.</p>
            </body>
        </html>
        """
        result = strip_html_css_js(raw_html, base_url="https://example.com")
        clean_text = result["clean_text"]

        self.assertNotIn("alert(", clean_text)
        self.assertNotIn("console.log", clean_text)
        self.assertNotIn("document.write", clean_text)
        self.assertIn("Welcome", clean_text)
        self.assertIn("This is safe content.", clean_text)
        self.assertGreaterEqual(result["scripts_removed"], 2)

    def test_strip_css_and_styles(self):
        raw_html = """
        <html>
            <head>
                <style>
                    body { background-color: red; font-size: 100px; }
                    .hidden { display: none !important; }
                </style>
                <link rel="stylesheet" href="styles.css">
            </head>
            <body>
                <p style="color: blue; text-align: center;">Styled Paragraph</p>
            </body>
        </html>
        """
        result = strip_html_css_js(raw_html, base_url="https://example.com")
        clean_text = result["clean_text"]

        self.assertNotIn("background-color", clean_text)
        self.assertNotIn("font-size", clean_text)
        self.assertNotIn("display: none", clean_text)
        self.assertIn("Styled Paragraph", clean_text)
        self.assertGreaterEqual(result["styles_removed"], 1)

    def test_link_preservation_and_formatting(self):
        raw_html = """
        <html>
            <body>
                <p>Check out <a href="/news">Latest News</a> and <a href="https://wikipedia.org">Wikipedia</a>.</p>
            </body>
        </html>
        """
        result = strip_html_css_js(raw_html, base_url="https://example.com")
        links = result["links"]

        self.assertEqual(len(links), 2)
        self.assertEqual(links[0]["url"], "https://example.com/news")
        self.assertEqual(links[0]["text"], "Latest News")
        self.assertEqual(links[1]["url"], "https://wikipedia.org")

    def test_block_css_js_urls(self):
        self.assertTrue(ContentFilter.is_blocked_resource("https://example.com/app.js"))
        self.assertTrue(ContentFilter.is_blocked_resource("https://example.com/styles.css"))
        self.assertTrue(ContentFilter.is_blocked_resource("https://example.com/font.woff2"))
        self.assertFalse(ContentFilter.is_blocked_resource("https://example.com/article"))
        self.assertFalse(ContentFilter.is_blocked_resource("https://example.com/image.png"))


if __name__ == "__main__":
    unittest.main()
