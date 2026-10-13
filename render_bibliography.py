import html
import json
import re
from datetime import datetime

BASE_URL = 'https://tiagoft.github.io/'
PERSON_ID = f'{BASE_URL}#person'


def publication_fragment(entry):
    slug = re.sub(r'[^a-z0-9_-]+', '-', entry.get('key', '').lower()).strip('-')
    return f'publication-{slug or "entry"}'


def publication_page_url(entry):
    return f'{BASE_URL}#{publication_fragment(entry)}'


def clean_doi(entry):
    return entry.get('doi', '').strip().rstrip('.')


def clean_url(entry):
    url = entry.get('url', '').strip()
    if url.lower().startswith('http://dx.doi.org/'):
        return f'https://doi.org/{url[len("http://dx.doi.org/"):]}'
    if url.lower().startswith('http://doi.org/'):
        return f'https://doi.org/{url[len("http://doi.org/"):]}'
    return url


def arxiv_id(entry):
    if entry.get('archiveprefix', '').strip().lower() == 'arxiv':
        return entry.get('eprint', '').strip()
    return ''


def article_url(entry):
    doi = clean_doi(entry)
    if doi:
        return f'https://doi.org/{doi}'

    url = clean_url(entry)
    if url:
        return url

    eprint = arxiv_id(entry)
    if eprint:
        return f'https://arxiv.org/abs/{eprint}'

    return publication_page_url(entry)


def date_published(entry):
    # An arXiv record is dated by its identifier (YYMM.number), not by the year of a later venue.
    match = re.match(r'(\d{2})(\d{2})\.\d+', arxiv_id(entry))
    if match and not clean_doi(entry):
        return f'20{match.group(1)}-{match.group(2)}'
    return entry.get('year', '')


def article_identifier(entry):
    doi = clean_doi(entry)
    if doi:
        return {
            '@type': 'PropertyValue',
            'propertyID': 'DOI',
            'value': doi,
        }

    eprint = arxiv_id(entry)
    if eprint:
        return {
            '@type': 'PropertyValue',
            'propertyID': 'arXiv',
            'value': eprint,
        }

    url = clean_url(entry)
    if url:
        return url

    return {
        '@type': 'PropertyValue',
        'propertyID': 'BibTeX',
        'value': entry.get('key', ''),
    }


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
            'raw': f'@{raw.strip()}',
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


def author_names(entry):
    names = []
    for name in entry.get('author', '').split(' and '):
        name = ' '.join(name.split())
        if ',' in name:
            last, _, first = name.partition(',')
            name = f'{first.strip()} {last.strip()}'
        if name:
            names.append(name)
    return names


def plain_citation(entry):
    author = ', '.join(author_names(entry)) or 'Unknown Author'
    citation = f'{author}, "{entry["title"]}"' if entry.get('title') else f'{author}, Untitled'
    source = (entry.get('journal') or entry.get('booktitle') or
              entry.get('publisher') or entry.get('howpublished') or '')
    if source:
        citation += f'. {source}'
    doi = clean_doi(entry)
    link = f'https://doi.org/{doi}' if doi else clean_url(entry)
    if link:
        citation += f'. {link}'
    note = entry.get('note', '').strip()
    if note:
        citation += f' ({note})'
    return citation


def data_attribute(value):
    return html.escape(value, quote=True).replace('\n', '&#10;')


COPY_BUTTONS = (
    '<span class="text-nowrap small">'
    '<button type="button" class="btn btn-link btn-sm p-0 align-baseline" data-copy="citation">Copy text</button>'
    ' · '
    '<button type="button" class="btn btn-link btn-sm p-0 align-baseline" data-copy="bibtex">Copy BibTeX</button>'
    '</span>'
)


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
            author = ', '.join(author_names(entry)) or 'Unknown Author'
            title = f'<i>"{entry["title"]}"</i>' if entry.get('title') else 'Untitled'
            source = (entry.get('journal') or entry.get('booktitle') or
                      entry.get('publisher') or entry.get('howpublished') or '')
            doi = clean_doi(entry)
            url = clean_url(entry)
            if doi:
                doi_link = f'<a href="https://doi.org/{doi}" target="_blank" rel="noopener noreferrer">{doi}</a>'
            elif url:
                doi_link = f'<a href="{url}" target="_blank" rel="noopener noreferrer">{url}</a>'
            else:
                doi_link = ''

            github = entry.get('github', '').strip()
            note = entry.get('note', '').strip()
            label, color = TYPE_BADGE.get(entry.get('type', ''), ('Other', 'secondary'))
            badge = f'<span class="badge text-bg-{color} me-2">{label}</span>'
            citation = f'{badge}{author}, {title}'
            if source:
                citation += f'. {source}'
            if doi_link:
                citation += f'. {doi_link}'
            if note:
                citation += f' <em>({note})</em>'
            if github:
                citation += f' <a href="{github}" target="_blank" rel="noopener noreferrer">[Code]</a>'

            parts.append(
                f'      <div id="{publication_fragment(entry)}" class="entry mb-2"'
                f' data-citation="{data_attribute(plain_citation(entry))}"'
                f' data-bibtex="{data_attribute(entry["raw"])}">\n'
                f'        <p>{citation} {COPY_BUTTONS}</p>\n'
                f'      </div>'
            )

    return '\n'.join(parts)


def render_jsonld(entries):
    items = []
    for entry in entries:
        def make_author(name):
            node = {'@type': 'Person', 'name': name}
            if 'Tiago' in name and 'Tavares' in name:
                node['@id'] = PERSON_ID
            return node

        authors = [make_author(a) for a in author_names(entry)]
        source = entry.get('journal') or entry.get('booktitle') or ''
        publisher = entry.get('publisher', '').strip()
        url = article_url(entry)

        item = {
            '@type': 'ScholarlyArticle',
            '@id': url,
            'name': entry.get('title', ''),
            'author': authors,
            'datePublished': date_published(entry),
            'url': url,
            'identifier': article_identifier(entry),
        }
        if source:
            item['isPartOf'] = {
                '@type': 'Periodical' if entry.get('journal') else 'CreativeWork',
                'name': source,
            }
        if publisher:
            item['publisher'] = {'@type': 'Organization', 'name': publisher}

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
