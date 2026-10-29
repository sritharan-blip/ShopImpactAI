# ShopImpactAI

ShopImpact is a Streamlit demo for tracking everyday purchases and exploring more conscious shopping choices. It estimates spending and category-based carbon impact, and brings purchase tracking, product discovery, and mindful shopping tools together in one app.

## Features

- Overview of monthly spending, estimated footprint, lower-impact choices, and trends.
- Purchase log with category-based impact estimates and CSV import/export.
- Swap studio for comparing purchases with lower-impact alternatives.
- Demo marketplace, wishlist, cart, and checkout flow.
- Local demo profile, order tracking, rewards, and support/returns views.

Impact values are directional estimates based on category factors; they are not independently verified lifecycle assessments. The marketplace, checkout, orders, and support features are demos. No payment is charged and no real order or support request is sent.

## Run locally

Use Python 3.10 or later.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run ShopImpactAI.py
```

The app opens in your browser, usually at `http://localhost:8501`.

## Import purchase history

In **Log purchase**, download the CSV template or upload a CSV with these columns:

- Required: `product`, `category`, `price`
- Optional: `date`, `brand`

The impact estimate is recalculated from the selected category and price. Invalid rows may be skipped and reported during import.

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub.
2. In Streamlit Community Cloud, create an app from this repository and select the `main` branch.
3. Set the main file path to `ShopImpactAI.py`, then deploy.

Dependencies are listed in `requirements.txt`. The app does not require Streamlit secrets to run.

## Data and privacy

App data is kept in the current Streamlit session; it is not backed by a database or user account and may be lost when the session ends. Do not upload `.venv`, `__pycache__`, or `.streamlit/secrets.toml` to GitHub. The repository's `.gitignore` excludes these local or sensitive files.
