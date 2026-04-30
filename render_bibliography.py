import json
import re
from datetime import datetime


def parse_bibtex(content):
    current_year = datetime.now().year
    lim_year = current_year - 5
    entries = []

    for raw in content.split('@')[1:]:
        lines = raw.strip().split('\n')
        if not lines:
            continue

        type_key = lines[0]
        brace_idx = type_key.find('{')
        if brace_idx == -1:
            continue

        entry = {
            'type': type_key[:brace_idx].strip().lower(),
            'key': type_key[brace_idx + 1:].replace(',', '').strip(),
        }

        for line in lines[1:]:
            line = line.strip()
            if '=' not in line:
                continue
            k, _, v = line.partition('=')
            field = k.strip().lower()
            value = re.sub(r'[{}"]', '', v).rstrip(',').strip()
            entry[field] = value

        try:
            year = int(entry.get('year', 0))
        except ValueError:
            year = 0

        if year >= lim_year:
            entries.append(entry)

    return entries


TYPE_BADGE = {
    'article':       ('Journal',    'primary'),
    'inproceedings': ('Conference', 'success'),
    'misc':          ('Preprint',   'warning'),
}


def render_html(entries):
    entries = sorted(entries, key=lambda e: int(e.get('year', 0)), reverse=True)

    by_year = {}
    for entry in entries:
        by_year.setdefault(entry.get('year', 'Unknown'), []).append(entry)

    parts = []
    for year in sorted(by_year, reverse=True):
        parts.append(f'      <h4 class="mt-4 mb-2 border-bottom pb-1">{year}</h4>')
        for entry in by_year[year]:
            author = entry.get('author', 'Unknown Author').replace(' and ', ', ')
            title = f'<i>"{entry["title"]}"</i>' if entry.get('title') else 'Untitled'
            source = (entry.get('journal') or entry.get('booktitle') or
                      entry.get('publisher') or entry.get('howpublished') or '')
            doi = entry.get('doi', '').strip()
            url = entry.get('url', '').strip()
            if doi:
                doi_link = f'<a href="https://doi.org/{doi}" target="_blank">{doi}</a>'
            elif url:
                doi_link = f'<a href="{url}" target="_blank">{url}</a>'
            else:
                doi_link = ''

            label, color = TYPE_BADGE.get(entry.get('type', ''), ('Other', 'secondary'))
            badge = f'<span class="badge badge-{color} mr-2">{label}</span>'

            parts.append(
                f'      <div class="entry mb-2">\n'
                f'        <p>{badge}{author}, {title}. {source}. {doi_link}</p>\n'
                f'      </div>'
            )

    return '\n'.join(parts)


def render_jsonld(entries):
    items = []
    for entry in entries:
        def make_author(name):
            name = name.strip()
            node = {'@type': 'Person', 'name': name}
            if 'Tiago' in name and 'Tavares' in name:
                node['@id'] = 'https://tiagoft.github.io/'
            return node

        authors = [
            make_author(a)
            for a in entry.get('author', '').split(' and ')
            if a.strip()
        ]
        source = entry.get('journal') or entry.get('booktitle') or ''
        doi = entry.get('doi', '').strip()
        url = entry.get('url', '').strip()

        item = {
            '@type': 'ScholarlyArticle',
            'name': entry.get('title', ''),
            'author': authors,
            'datePublished': entry.get('year', ''),
        }
        if source:
            item['isPartOf'] = {'name': source}
        if doi:
            item['url'] = f'https://doi.org/{doi}'
            item['identifier'] = doi
        elif url:
            item['url'] = url

        items.append(item)

    graph = {'@context': 'https://schema.org', '@graph': items}
    block = json.dumps(graph, ensure_ascii=False, indent=2)
    return f'    <script type="application/ld+json">\n    {block}\n    </script>'


def main():
    with open('bibliography.bib', encoding='utf-8') as f:
        bibtex = f.read()

    entries = parse_bibtex(bibtex)
    html = render_html(entries)
    jsonld = render_jsonld(entries)

    with open('index.html', encoding='utf-8') as f:
        content = f.read()

    new_content = re.sub(
        r'<!-- BIBLIOGRAPHY_START -->.*?<!-- BIBLIOGRAPHY_END -->',
        f'<!-- BIBLIOGRAPHY_START -->\n{html}\n<!-- BIBLIOGRAPHY_END -->',
        content,
        flags=re.DOTALL,
    )
    new_content = re.sub(
        r'<!-- JSONLD_START -->.*?<!-- JSONLD_END -->',
        f'<!-- JSONLD_START -->\n{jsonld}\n<!-- JSONLD_END -->',
        new_content,
        flags=re.DOTALL,
    )

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f'Rendered {len(entries)} entries.')


if __name__ == '__main__':
    main()
