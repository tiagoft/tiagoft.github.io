// URL of the BibTeX file
const bibtexURL = 'bibliography.bib';

// Fetch the BibTeX file
fetch(bibtexURL)
  .then(response => response.text())
  .then(bibtex => {
    const entries = parseBibtex(bibtex);

    const html = renderHTML(entries);
    document.getElementById('bibtexEntries').innerHTML = html;
    console.log(entries); // debug
  })
  .catch(error => {
    console.error('Error fetching BibTeX file:', error);
  });

// Parse BibTeX into objects
function parseBibtex(bibtex) {
  const entries = [];
  const rawEntries = bibtex.split('@').slice(1); // split at each entry

  const currentYear = new Date().getFullYear();
  const limYear = currentYear - 3;

  rawEntries.forEach(raw => {
    const [typeAndKey, ...fields] = raw.split('\n');
    const [type, key] = typeAndKey.split('{');
    const entry = {
      type: type.trim(),
      key: key ? key.replace(',', '').trim() : ''
    };

    fields.forEach(line => {
      line = line.trim();
      if (line.includes('=')) {
        const [k, v] = line.split('=');
        const field = k.trim().toLowerCase();
        const value = v.replace(/[{}"]/g, '').replace(/,$/, '').trim();
        entry[field] = value;
      }
    });

    // Only include entries from the last 3 years
    if (entry.year && parseInt(entry.year) >= limYear) {
      entries.push(entry);
    }
  });

  return entries;
}

// Render HTML
function renderHTML(entries) {
  entries.sort((a, b) => (b.year || 0) - (a.year || 0));
  return entries.map(entry => {
    const author = entry.author ? entry.author.replace(/ and /gi, ', ') : 'Unknown Author';
    const title = entry.title ? `<i>"${entry.title}"</i>` : 'Untitled';
    const source = entry.journal || entry.booktitle || entry.publisher || entry.howpublished || '';
    const doiLink = entry.doi ? `<a href="https://doi.org/${entry.doi}" target="_blank">${entry.doi}</a>` : '';

    return `
      <div class="entry mb-2">
        <p>
          ${author}, ${title}. ${source}, ${entry.year || ''}. ${doiLink}
        </p>
      </div>
    `;
  }).join('');
}
