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
        // yr = current system year


        // Get the current system year
        const currentYear = new Date().getFullYear();
        lim_year = currentYear-3;

        // Check if the current entry's year is greater than the current system year
        if (currentEntry.year > lim_year) {
          entries.push(currentEntry);
        }

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
  entries.sort((a, b) => b.year - a.year);
  const html = entries.map(entry => {
    let doiLink = '';
    if (entry.doi) {
      doiLink = `<a href="https://doi.org/${entry.doi}">${entry.doi}</a>`;
    }
    return `
      <div class="entry">
        <p>
        ${entry.author.replace(/ and /g, ', ')},
        <i>"${entry.title}"</i>
        ${entry.journal || entry.booktitle || entry.publisher || entry.howpublished}, ${entry.year}
        ${doiLink}
        </p>
      </div>
    `;
  }).join('');

  return `
        ${html}
  `;
}
