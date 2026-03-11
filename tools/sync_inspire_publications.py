from __future__ import annotations

import datetime as dt
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
AUTHOR_RECID = "2163140"
AUTHOR_API = f"https://inspirehep.net/api/authors/{AUTHOR_RECID}"
LITERATURE_API = "https://inspirehep.net/api/literature"
USER_AGENT = "xiaoCornell.github.io publication sync (+https://xiaocornell.github.io/)"
DATA_PATH = ROOT / "data" / "publications.json"
TEMPLATE_PATH = ROOT / "templates" / "publications.html.tpl"
OUTPUT_PATH = ROOT / "publications.html"


def fetch_json(url: str) -> dict:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def fetch_author_record() -> dict:
    payload = fetch_json(AUTHOR_API)
    metadata = payload.get("metadata", {})
    bai = None
    orcid = None
    for identifier in metadata.get("ids", []):
        if identifier.get("schema") == "INSPIRE BAI":
            bai = identifier.get("value")
        if identifier.get("schema") == "ORCID":
            orcid = identifier.get("value")

    if not bai:
        raise RuntimeError("Could not find INSPIRE BAI in author profile.")

    preferred_name = metadata.get("name", {}).get("preferred_name") or metadata.get("name", {}).get("value") or "Xiao Wang"
    return {
        "name": preferred_name,
        "bai": bai,
        "orcid": orcid,
        "profile_url": f"https://inspirehep.net/authors/{AUTHOR_RECID}?ui-citation-summary=true",
    }


def fetch_literature_records(bai: str) -> list[dict]:
    params = {
        "q": f"a {bai}",
        "sort": "mostrecent",
        "size": "250",
    }
    next_url = f"{LITERATURE_API}?{urlencode(params)}"
    results: list[dict] = []

    while next_url:
        payload = fetch_json(next_url)
        results.extend(payload.get("hits", {}).get("hits", []))
        next_url = payload.get("links", {}).get("next")

    if not results:
        raise RuntimeError("INSPIRE literature query returned no records; refusing to overwrite publications page.")

    return results


def display_name(raw_name: str) -> str:
    if "," in raw_name:
        last, first = [part.strip() for part in raw_name.split(",", 1)]
        return f"{first} {last}" if first else last
    return raw_name


def clean_text(value: str) -> str:
    text = re.sub(r"<[^>]+>", "", value)
    return html.unescape(text).strip()


def is_current_author(author: dict, bai: str) -> bool:
    if str(author.get("recid", "")) == AUTHOR_RECID:
        return True
    for identifier in author.get("ids", []):
        if identifier.get("schema") == "INSPIRE BAI" and identifier.get("value") == bai:
            return True
    return False


def format_authors(authors: list[dict], bai: str) -> str:
    if not authors:
        return ""

    rendered: list[str] = []
    for author in authors:
        name = html.escape(display_name(author.get("full_name", "Unknown Author")))
        if is_current_author(author, bai):
            name = f"<strong>{name}</strong>"
        rendered.append(name)

    if len(rendered) > 12:
        rendered = rendered[:12] + ["et al."]

    return ", ".join(rendered)


def extract_year(metadata: dict) -> str:
    for key in ("preprint_date", "earliest_date"):
        value = metadata.get(key)
        if value:
            return str(value)[:4]

    for info in metadata.get("publication_info", []):
        year = info.get("year")
        if year:
            return str(year)

    return "N/A"


def extract_venue(metadata: dict) -> tuple[str, bool]:
    for info in metadata.get("publication_info", []):
        if info.get("pubinfo_freetext"):
            return str(info["pubinfo_freetext"]), True

        journal = info.get("journal_title")
        if journal:
            parts = [str(journal)]
            if info.get("journal_volume"):
                parts.append(str(info["journal_volume"]))
            if info.get("artid"):
                parts.append(str(info["artid"]))
            elif info.get("page_start") and info.get("page_end"):
                parts.append(f"{info['page_start']}-{info['page_end']}")
            elif info.get("page_start"):
                parts.append(str(info["page_start"]))
            year = info.get("year")
            venue = " ".join(parts)
            if year:
                venue = f"{venue} ({year})"
            return venue, True

    arxiv = metadata.get("arxiv_eprints", [])
    if arxiv:
        return f"arXiv:{arxiv[0].get('value', 'unknown')}", False

    document_types = metadata.get("document_type", [])
    if document_types:
        return ", ".join(document_types), False

    return "INSPIRE record", False


def extract_links(metadata: dict, recid: str) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []

    arxiv = metadata.get("arxiv_eprints", [])
    if arxiv:
        arxiv_id = arxiv[0].get("value")
        if arxiv_id:
            links.append({"label": "arXiv", "url": f"https://arxiv.org/abs/{arxiv_id}"})

    dois = metadata.get("dois", [])
    if dois:
        doi = dois[0].get("value")
        if doi:
            links.append({"label": "DOI", "url": f"https://doi.org/{doi}"})

    links.append({"label": "INSPIRE", "url": f"https://inspirehep.net/literature/{recid}"})
    return links


def normalize_record(hit: dict, bai: str) -> dict:
    metadata = hit.get("metadata", {})
    title_entries = metadata.get("titles", [])
    title = "Untitled"
    preferred_sources = ("arXiv", "submitter", "publication", "APS")
    for source in preferred_sources:
        for entry in title_entries:
            if entry.get("source") == source and entry.get("title"):
                title = clean_text(entry["title"])
                break
        if title != "Untitled":
            break
    if title == "Untitled" and title_entries:
        title = clean_text(title_entries[0].get("title", "Untitled"))
    venue, peer_reviewed = extract_venue(metadata)
    return {
        "recid": str(metadata.get("control_number") or hit.get("id")),
        "title": title,
        "year": extract_year(metadata),
        "authors_html": format_authors(metadata.get("authors", []), bai),
        "venue": venue,
        "citation_count": metadata.get("citation_count", 0),
        "peer_reviewed": peer_reviewed,
        "links": extract_links(metadata, str(metadata.get("control_number") or hit.get("id"))),
    }


def render_publication_card(publication: dict) -> str:
    authors_html = publication.get("authors_html")
    authors_block = f"        <p>{authors_html}</p>\n" if authors_html else ""
    links_html = "\n".join(
        f'          <a href="{html.escape(link["url"])}">{html.escape(link["label"])}</a>'
        for link in publication.get("links", [])
    )
    link_block = (
        "        <div class=\"link-row\">\n"
        f"{links_html}\n"
        "        </div>\n"
        if links_html
        else ""
    )

    return (
        "        <article class=\"publication-card reveal\">\n"
        f"          <div class=\"pub-meta\"><span>{html.escape(publication['year'])}</span><span>{html.escape(publication['venue'])}</span></div>\n"
        f"          <h3>{html.escape(publication['title'])}</h3>\n"
        f"{authors_block}"
        f"{link_block}"
        "        </article>"
    )


def render_publications_page(author: dict, publications: list[dict]) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    synced_at = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
    peer_reviewed_count = sum(1 for publication in publications if publication.get("peer_reviewed"))
    author_label = f"{author['name']} ({author['bai']})"
    publication_items = "\n".join(render_publication_card(publication) for publication in publications)

    replacements = {
        "__SYNCED_AT__": synced_at,
        "__AUTHOR_LABEL__": author_label,
        "__PUBLICATION_COUNT__": str(len(publications)),
        "__PEER_REVIEWED_COUNT__": str(peer_reviewed_count),
        "__PUBLICATION_ITEMS__": publication_items,
    }

    rendered = template
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)
    return rendered


def main() -> int:
    author = fetch_author_record()
    records = fetch_literature_records(author["bai"])
    publications = [normalize_record(record, author["bai"]) for record in records]

    payload = {
        "synced_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "author": {
            "recid": AUTHOR_RECID,
            "name": author["name"],
            "bai": author["bai"],
            "orcid": author["orcid"],
            "profile_url": author["profile_url"],
        },
        "publication_count": len(publications),
        "peer_reviewed_count": sum(1 for publication in publications if publication.get("peer_reviewed")),
        "publications": publications,
    }

    DATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_PATH.write_text(render_publications_page(author, publications), encoding="utf-8")

    print(f"Synced {len(publications)} records for {author['name']} ({author['bai']}).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI failure path
        print(f"Sync failed: {exc}", file=sys.stderr)
        raise SystemExit(1)



