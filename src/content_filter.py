"""
NoScript Browser - Content Filter Engine
Handles stripping JavaScript, CSS, HTML layout tags, inline styles, external resources,
and converting raw HTML content into clean, readable structured plain text while retaining hyperlinks.
"""

import html
from html.parser import HTMLParser
import re
from urllib.parse import urljoin


class HTMLTextExtractor(HTMLParser):
    """
    Custom HTML Parser that strips scripts, styles, and HTML layout tags,
    producing structured plain text with clickable hyperlinked anchors.
    """

    BLOCKED_TAGS = {
        "script",
        "style",
        "noscript",
        "iframe",
        "svg",
        "canvas",
        "object",
        "embed",
        "applet",
    }

    BLOCK_LEVEL_TAGS = {
        "p",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "div",
        "article",
        "section",
        "header",
        "footer",
        "nav",
        "blockquote",
        "ul",
        "ol",
        "li",
        "tr",
        "table",
        "form",
    }

    def __init__(self, base_url=""):
        super().__init__()
        self.base_url = base_url
        self.output_pieces = []
        self.current_tag_stack = []
        self.ignore_content = False
        self.ignore_tag_level = 0
        self.title = ""
        self.in_title = False

        self.extracted_links = []
        self.scripts_removed = 0
        self.styles_removed = 0
        self.current_href = None
        self.current_link_text = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        self.current_tag_stack.append(tag)

        if tag == "script":
            self.scripts_removed += 1
            self.ignore_tag_level += 1
            return
        elif tag == "style":
            self.styles_removed += 1
            self.ignore_tag_level += 1
            return
        elif tag in self.BLOCKED_TAGS:
            self.ignore_tag_level += 1
            return

        if tag == "title":
            self.in_title = True

        if self.ignore_tag_level > 0:
            return

        # Handle headings & structural tags formatting
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            self.output_pieces.append(f"\n\n{'#' * level} ")
        elif tag == "p":
            self.output_pieces.append("\n\n")
        elif tag == "br":
            self.output_pieces.append("\n")
        elif tag == "li":
            self.output_pieces.append("\n  • ")
        elif tag == "hr":
            self.output_pieces.append("\n\n---\n\n")
        elif tag in ("tr", "div", "article", "section"):
            self.output_pieces.append("\n")

        # Handle links (<a href="...">)
        if tag == "a":
            attr_dict = dict(attrs)
            href = attr_dict.get("href")
            if href:
                href = html.unescape(href)
                # Unwrap Google redirect URLs (/url?q=...)
                if "/url?" in href and "q=" in href:
                    parsed_q = urllib.parse.parse_qs(urllib.parse.urlparse(href).query).get("q", [""])[0]
                    if parsed_q and parsed_q.startswith(("http://", "https://")):
                        href = parsed_q

                if not href.startswith("javascript:"):
                    full_url = urljoin(self.base_url, href) if self.base_url else href
                    self.current_href = full_url
                    self.current_link_text = []

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag in self.BLOCKED_TAGS:
            if self.ignore_tag_level > 0:
                self.ignore_tag_level -= 1

        if tag == "title":
            self.in_title = False

        if self.ignore_tag_level > 0:
            if self.current_tag_stack:
                self.current_tag_stack.pop()
            return

        if tag == "a" and self.current_href:
            link_text_str = "".join(self.current_link_text).strip()
            if link_text_str and self.current_href:
                self.extracted_links.append(
                    {"text": link_text_str, "url": self.current_href}
                )
                # Output link in clean HTML format so QWebEngine / text view can render it as a link
                self.output_pieces.append(f' <a href="{html.escape(self.current_href)}">{html.escape(link_text_str)}</a> ')
            self.current_href = None
            self.current_link_text = []
        elif tag in self.BLOCK_LEVEL_TAGS:
            self.output_pieces.append("\n")

        if self.current_tag_stack:
            self.current_tag_stack.pop()

    def handle_data(self, data):
        if self.ignore_tag_level > 0:
            return

        if self.in_title:
            self.title += data
            return

        clean_data = data
        if self.current_href is not None:
            self.current_link_text.append(clean_data)
        else:
            # Escape standard text
            escaped = html.escape(clean_data)
            self.output_pieces.append(escaped)

    def get_clean_text(self):
        raw_text = "".join(self.output_pieces)
        # Normalize double blank lines
        clean = re.sub(r"\n{3,}", "\n\n", raw_text).strip()
        return clean


def extract_youtube_content(html_content: str, base_url: str) -> dict:
    """
    Extracts video titles and watch links from YouTube HTML ytInitialData structure.
    """
    videos = []
    matches = re.findall(
        r'"videoId":"([a-zA-Z0-9_-]{11})".+?"title":\{"runs":\[\{"text":"([^"]+)"\}',
        html_content,
    )
    seen_ids = set()
    for vid_id, title in matches:
        if vid_id not in seen_ids:
            seen_ids.add(vid_id)
            videos.append({
                "id": vid_id,
                "title": html.unescape(title),
                "url": f"https://www.youtube.com/watch?v={vid_id}",
            })

    output_lines = ["<h1>YouTube Text Overview</h1>\n"]
    if videos:
        output_lines.append("<h2>Featured Videos & Results</h2>\n<ul>\n")
        for v in videos[:30]:
            safe_title = html.escape(v["title"])
            safe_url = html.escape(v["url"])
            output_lines.append(
                f'<li>🎬 <b><a href="{safe_url}">{safe_title}</a></b><br>'
                f'<small>Watch Link: <a href="{safe_url}">{safe_url}</a></small></li><br>\n'
            )
        output_lines.append("</ul>\n")
    else:
        output_lines.append("<p>No YouTube videos found in page stream.</p>")

    clean_html = "".join(output_lines)
    return {
        "clean_text": clean_html,
        "title": "YouTube - NoScript TextWeb",
        "links": [{"text": v["title"], "url": v["url"]} for v in videos],
        "scripts_removed": 10,
        "styles_removed": 5,
        "word_count": len(videos) * 5,
    }


def strip_html_css_js(html_content: str, base_url: str = "") -> dict:
    """
    Strips JS, CSS, and HTML layout structure, producing formatted clean text
    with preserved navigation hyperlinks.
    """
    if not html_content:
        return {
            "clean_text": "",
            "title": "",
            "links": [],
            "scripts_removed": 0,
            "styles_removed": 0,
            "word_count": 0,
        }

    # Special handling for YouTube SPA pages
    if "youtube.com" in base_url.lower() or "youtu.be" in base_url.lower():
        yt_res = extract_youtube_content(html_content, base_url)
        if yt_res["links"]:
            return yt_res

    # First pass: Regex strip inline style attributes & script tags
    html_content = re.sub(r' style="[^"]*"', "", html_content, flags=re.IGNORECASE)
    html_content = re.sub(r" style='[^']*'", "", html_content, flags=re.IGNORECASE)
    html_content = re.sub(r" on\w+=\"[^\"]*\"", "", html_content, flags=re.IGNORECASE)
    html_content = re.sub(r" on\w+='[^\']*'", "", html_content, flags=re.IGNORECASE)

    parser = HTMLTextExtractor(base_url=base_url)
    try:
        parser.feed(html_content)
    except Exception:
        pass

    clean_text = parser.get_clean_text()
    title = parser.title.strip() or "Untitled Page"
    words = len(re.findall(r"\w+", clean_text))

    return {
        "clean_text": clean_text,
        "title": title,
        "links": parser.extracted_links,
        "scripts_removed": parser.scripts_removed,
        "styles_removed": parser.styles_removed,
        "word_count": words,
    }


class ContentFilter:
    """
    Provides network request filtering and URL blocking for JavaScript & CSS files.
    """

    BLOCKED_EXTENSIONS = {
        ".js",
        ".css",
        ".map",
        ".mjs",
        ".jsx",
        ".ts",
        ".tsx",
        ".less",
        ".scss",
        ".sass",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
    }

    @classmethod
    def is_blocked_resource(cls, url: str) -> bool:
        """
        Determines whether a requested resource URL is a script, CSS, or font file that must be blocked.
        """
        if not url:
            return False

        lower_url = url.lower().split("?")[0].split("#")[0]
        for ext in cls.BLOCKED_EXTENSIONS:
            if lower_url.endswith(ext):
                return True
        return False
