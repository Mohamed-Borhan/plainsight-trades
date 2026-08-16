# PlainSight — Public Trade Intelligence

PlainSight is a public-filings research interface that adds context to SEC insider filings and official congressional trade disclosures.

## Live website

[mohamed-borhan.github.io/plainsight-trades](https://mohamed-borhan.github.io/plainsight-trades/)

## Research principles

- Use official public sources only
- Separate corporate insider filings from political disclosures
- Enter follower backtests only after publication
- Display unavailable data as N/A
- Keep sample size and caveats beside every score
- Never execute broker orders

## Stage 1 automation

- A GitHub workflow checks official SEC daily indexes every weekday after EDGAR closes.
- The collector parses ownership XML and keeps direct, non-derivative common-stock open-market purchases (code P) of at least $50,000 and notable direct sales (code S) of at least $250,000.
- Accession numbers provide deduplication, and amended or ambiguous filings are routed to a review-needed list.
- A second workflow generates an on-site weekly preview every Saturday.
- The weekly newsletter remains explicitly labeled as a work in progress while the project collects enough validated history for more meaningful rankings and grades.
- Email collection and email delivery are disabled during Stage 1.

Both workflows can also be started manually from the repository's Actions page. The collector uses only Python's standard library, identifies itself to the SEC, caches processed accessions, and stays below the SEC's published fair-access request limit.

## Technology

- Semantic HTML5
- Responsive CSS
- Lightweight JavaScript
- Python standard-library data collector
- GitHub Actions scheduling
- GitHub Pages

## Important notice

This project is educational research, not financial, legal, or investment advice. Public filings may be delayed or incomplete, and past outcomes do not predict future returns.
