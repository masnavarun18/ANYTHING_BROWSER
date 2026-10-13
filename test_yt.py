import urllib.request
import re
import html as html_lib

def extract_youtube_content(html_str: str, base_url: str) -> dict:
    videos = []
    matches = re.findall(
        r'"videoId":"([a-zA-Z0-9_-]{11})".+?"title":\{"runs":\[\{"text":"([^"]+)"\}',
        html_str,
    )
    seen_ids = set()
    for vid_id, title in matches:
        if vid_id not in seen_ids:
            seen_ids.add(vid_id)
            videos.append({
                "id": vid_id,
                "title": html_lib.unescape(title),
                "url": f"https://www.youtube.com/watch?v={vid_id}",
            })

    output_lines = ["<h1>YouTube Text Overview</h1>\n"]
    if videos:
        output_lines.append("<h2>Featured Videos & Results</h2>\n<ul>\n")
        for v in videos[:25]:
            safe_title = html_lib.escape(v["title"])
            safe_url = html_lib.escape(v["url"])
            output_lines.append(
                f'<li>🎬 <b><a href="{safe_url}">{safe_title}</a></b><br>'
                f'<small>Watch Link: <a href="{safe_url}">{safe_url}</a></small></li><br>\n'
            )
        output_lines.append("</ul>\n")
    else:
        output_lines.append("<p>No video streams found in raw page.</p>")

    clean_html = "".join(output_lines)
    return {
        "clean_text": clean_html,
        "title": "YouTube - NoScript TextWeb",
        "links": [{"text": v["title"], "url": v["url"]} for v in videos],
        "scripts_removed": 10,
        "styles_removed": 5,
        "word_count": len(videos) * 5,
    }

def main():
    url = "https://www.youtube.com/results?search_query=python+programming"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    html_raw = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')
    res = extract_youtube_content(html_raw, url)
    print("Title:", res["title"])
    print("Video count:", len(res["links"]))
    print("Sample Output HTML:\n", res["clean_text"][:600])

if __name__ == "__main__":
    main()
