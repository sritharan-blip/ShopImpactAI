# ShopImpactAI

ShopImpact is a session-based Streamlit demo for conscious shopping. It helps you record purchases, explore directional carbon-impact estimates, compare alternatives, and review spending and impact trends.

> **Demo notice:** Impact values are estimates based on broad category factors, not product-specific or independently verified lifecycle assessments. The marketplace, cart, checkout, orders, returns, and support tools are illustrative local demo flows. The app does not process payments, place real orders, contact a support team, or connect to a carrier.

## What you can do

Use the sidebar to move between these sections:

- **Overview** — See monthly spending, estimated footprint, lower-impact choices, eco score, and recent activity. Quick actions lead to common tasks.
- **Discover** — Browse and filter a curated demo catalog, inspect product details, and explore suggested picks.
- **Log a purchase** — Record a product, category, shop, price, date, and whether you chose a greener alternative. Each entry is added to your impact ledger.
- **Wishlist** — Save ideas with a category, estimated price, priority, note, and revisit date. Wishlist estimates are not included in purchase totals.
- **Cart & checkout** — Try the demo cart and checkout flow. No card details are collected and no payment or real order is submitted.
- **My orders** — Review illustrative orders created in the current session.
- **Impact analytics** — Explore summaries and charts based on the purchases in your current session.
- **Swap studio** — Compare a purchase category with suggested lower-impact alternatives and review estimated differences.
- **Eco rewards** — Review progress, badges, and challenges calculated from the session ledger.
- **Help & returns** — Try the demo return and support forms. Requests are saved only in the current session and are not sent to anyone.
- **Profile** — Set up the local demo profile; it is not a real account.

## Impact estimate

For logged purchases and CSV imports, ShopImpact calculates:

```text
estimated kg CO2e = category factor × price ÷ 10
```

The built-in factors are expressed as estimated kg CO2e per $10:

| Category | Factor | Indicative level |
|---|---:|---|
| Electronics | 3.5 | High |
| Fast fashion / leather | 2.8 | High |
| Groceries / organic food | 0.4 | Low |
| Sustainable apparel / second-hand | 0.2 | Very low |
| Beauty & personal care | 1.1 | Medium |
| Home & living | 1.5 | Medium |

These simplified factors are for exploration and comparison only. Results can vary substantially by product, materials, location, energy source, transport, and methodology; do not use them as a formal footprint report.

## Run locally

Use Python 3.10 or later.

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run ShopImpactAI.py
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run ShopImpactAI.py
```

Streamlit prints a local URL (usually `http://localhost:8501`) when the app starts. Stop the local server with **Ctrl+C** in the terminal.

## Dependencies

Install the project's dependencies from [`requirements.txt`](requirements.txt):

- Streamlit — app interface and session state
- pandas — purchase data handling and CSV import/export
- Plotly — interactive charts
- Pillow — generated app illustration

## Import purchase history

1. Open **Log purchase** and expand **Import an existing purchase log**.
2. Select **Get CSV template** to download a header row.
3. Fill in the CSV and upload it.
4. Select **Validate and import** to add valid rows to the current session ledger.

Required columns:

| Column | Description |
|---|---|
| `product` | Non-empty product name |
| `category` | One of the exact categories listed in the impact table above |
| `price` | Finite, non-negative number |

Optional columns:

| Column | Description |
|---|---|
| `date` | Purchase date; defaults to today if blank. Future dates are rejected. |
| `brand` | Brand or shop name |

Example:

```csv
date,product,category,brand,price
2026-01-15,Refill hand wash,Beauty & personal care,Ethique,18.00
2026-01-16,Second-hand reading lamp,Home & living,Etsy (vintage),35.00
```

Imports are limited to 5,000 rows at a time. Invalid rows are skipped and reported. The app recalculates impact from the submitted category and price; any supplied emissions values are not used.

## Back up and restore

In the sidebar's **Data backup** section:

- Download a JSON backup of your purchase ledger and wishlist.
- Restore a compatible ShopImpact backup after confirming that restoration replaces the current ledger and wishlist.

Backup files include those two data sets, but not the cart, profile, orders, support/return requests, or display preferences. Backups are limited to 5 MB and support up to 5,000 purchases and 500 wishlist items.

## Deploy on Streamlit Community Cloud

1. Push the repository to GitHub.
2. In [Streamlit Community Cloud](https://share.streamlit.io/), create an app from this repository.
3. Select the `main` branch and set **Main file path** to `ShopImpactAI.py`.
4. Deploy the app. Community Cloud installs packages from `requirements.txt`.

No Streamlit secrets are required for the current app. Do not add credentials or private data to the repository.

## Data, privacy, and limitations

- The app stores its working data in Streamlit session state; there is no database or real user account.
- Session data may be lost when the session ends or the app restarts. Download a backup if you want to keep your ledger and wishlist.
- The app does not send purchases, profile details, checkout information, or support requests to external commerce or support services.
- `.gitignore` excludes local Streamlit secrets, Python virtual environments, and Python cache files. Do not commit `.streamlit/secrets.toml`, `.venv`, `.venv-1`, or `__pycache__`.
- The app is a prototype for exploration and is not financial, environmental, or lifecycle-assessment advice.
