// URL of the BibTeX file
const bibtexURL = 'bibliography.bib';

// Fetch the BibTeX file
fetch(bibtexURL)
  .then(response => response.text())
  .then(bibtex => {
    // Parse the BibTeX entries
    const entries = parseBibtex(bibtex);

    // Render the HTML
    const html = renderHTML(entries);
    document.getElementById('bibtexEntries').innerHTML = html;
    console.log(html);
  })
  .catch(error => {
    console.error('Error fetching BibTeX file:', error);
  });

// Function to parse a BibTeX entry
function parseBibtex(bibtex) {
  const entries = [];
  const lines = bibtex.split('\n');
  let currentEntry = {};

  lines.forEach(line => {
    line = line.trim();
    if (line.startsWith('@')) {
      // Start of a new BibTeX entry
      if (Object.keys(currentEntry).length !== 0) {
        entries.push(currentEntry);
      }
      currentEntry = {};
      const [type, key] = line.substring(1).split('{');
      currentEntry.type = type.trim();
      currentEntry.key = key.trim().replace(/,/g, '');
    } else if (line.includes('=')) {
      // BibTeX field
      const [key, value] = line.split('=');
      currentEntry[key.trim()] = value.trim().replace(/[{},]/g, '');
    }
  });

  // Push the last entry
  if (Object.keys(currentEntry).length !== 0) {
    entries.push(currentEntry);
  }

  return entries;
}

// Function to render HTML from BibTeX entries
function renderHTML(entries) {
  const html = entries.map(entry => {
    return `
      <div class="entry">
        <p>
        ${entry.author},
        <i>"${entry.title}"</i>
        ${entry.journal || entry.booktitle || entry.publisher || entry.howpublished}, ${entry.year}
        </p>
      </div>
    `;
  }).join('');

  return `
    <html>
      <head>
        <title>BibTeX Entries</title>
      </head>
      <body>
        ${html}
      </body>
    </html>
  `;
}
