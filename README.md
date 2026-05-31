# ICLR 2026 Topic Explorer

An interactive explorer for ICLR 2026 accepted papers (5,352 papers), organized by a 4-level semantic topic phylogeny.

🔗 **Live Demo**: **[https://kenkuuu.github.io/iclr-explorer/](https://kenkuuu.github.io/iclr-explorer/)**

## Features

- **4-level Topic Phylogeny**: Phylum → Class → Order → Genus (10 phylums, 100% coverage)
- **Multi-label classification**: Up to 3 topic tags per paper (23% multi-labeled)
- **Interactive tree**: Click any node to filter papers
- **3 search inputs** with AND/OR logic across title and abstract
- **Chart.js visualizations**: Topic distribution bar charts
- **Expandable paper cards**: Click title to show abstract

## Data

- Source: [OpenReview](https://openreview.net) (ICLR 2026, CC0 license)
- Total submitted: 19,814 | Accepted: 5,352 (27.0%)
- Oral: 224 | Poster: 5,128
- Classification: keyword-based semantic matching (task/domain-first principle)

## Tech Stack

- **Frontend**: Vanilla JS + Chart.js (static, no build tools)
- **Backend**: Python 3.11 + uv
- **Data pipeline**: OpenReview API → keyword classification → GitHub Pages

## Run Locally

```bash
# Install dependencies
uv sync

# Fetch papers (requires OpenReview API, no key needed)
uv run scripts/fetch_papers.py

# Classify papers
uv run scripts/classify_phylogeny.py --stats

# Build distribution JSON
uv run scripts/build_json.py

# Serve locally
cd docs && python3 -m http.server 8000
# Open http://localhost:8000
```

## Re-classify

Edit `data/phylogeny.json` to add/modify topic keywords, then:
```bash
uv run scripts/classify_phylogeny.py --stats
uv run scripts/build_json.py
```

## License

- Source code: MIT
- Paper metadata: CC0 (OpenReview)
- Paper PDFs: Copyright belongs to respective authors
