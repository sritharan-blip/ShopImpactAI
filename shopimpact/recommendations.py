"""An explainable local content-based recommender. No APIs or credentials.

TF-IDF vectors are fitted to the catalog at runtime. Cosine similarity matches
shopping intent/history; category, budget and estimated reduction add explicit
ranking signals. Scores are ranking weights, never confidence probabilities.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
import math
import re

from .catalog import CATEGORIES, PRODUCTS

STOPWORDS = {'the', 'a', 'an', 'and', 'or', 'with', 'for', 'to', 'of', 'in', 'from', 'your', 'my', 'i'}


def _tokens(text: str) -> list[str]:
    return [word for word in re.findall(r'[a-z0-9]+', text.casefold()) if word not in STOPWORDS]


@lru_cache(maxsize=1)
def _model() -> tuple[dict, list[dict]]:
    documents = [Counter(_tokens(' '.join(str(p.get(k, '')) for k in
                 ('name', 'category', 'tagline', 'description', 'materials', 'repairability')))) for p in PRODUCTS]
    frequency = Counter(word for document in documents for word in document)
    idf = {word: math.log((1 + len(documents)) / (1 + count)) + 1 for word, count in frequency.items()}
    return idf, [_vector(document, idf) for document in documents]


def _vector(counts: Counter, idf: dict) -> dict:
    weights = {word: (1 + math.log(count)) * idf[word] for word, count in counts.items() if word in idf}
    norm = math.sqrt(sum(weight * weight for weight in weights.values())) or 1
    return {word: weight / norm for word, weight in weights.items()}


def recommend_products(query: str = '', purchases: list[dict] | None = None,
                       category: str | None = None, budget: float | None = None,
                       personalize: bool = True, limit: int = 3) -> list[dict]:
    """Return in-stock candidates with a reproducible score and its reasons.

    An explicit category/budget is a hard filter, including when no match exists.
    Personalization off prevents any reading of ledger content for ranking.
    """
    history = (purchases or []) if personalize else []
    history_text = ' '.join(str(p.get('product', '')) + ' ' + str(p.get('category', '')) for p in history[-20:])
    idf, vectors = _model()
    query_vector = _vector(Counter(_tokens(query or history_text)), idf)
    category_spend = Counter()
    for purchase in history:
        category_spend[purchase.get('category')] += float(purchase.get('co2', 0))
    preferred = category or (category_spend.most_common(1)[0][0] if category_spend else None)
    ranked = []
    for product, vector in zip(PRODUCTS, vectors):
        if product['stock'] <= 0 or (category and product['category'] != category):
            continue
        if budget is not None and product['price'] > budget:
            continue
        similarity = sum(weight * vector.get(word, 0) for word, weight in query_vector.items())
        reduction = max(0, 1 - product['impact_factor'] / CATEGORIES[product['category']]['factor'])
        affinity = 1.0 if product['category'] == preferred else 0.0
        score = 0.65 * similarity + 0.2 * affinity + 0.15 * reduction
        reasons = []
        if query.strip() and similarity > 0:
            reasons.append('Matches your shopping intent')
        elif history and similarity > 0:
            reasons.append('Similar to your recent purchases')
        if affinity:
            reasons.append('In your selected category' if category else 'Targets your highest-footprint category')
        if budget is not None:
            reasons.append('Within your budget')
        reasons.append(f'{reduction:.0%} below the demo category factor')
        ranked.append({**product, 'match_score': round(score, 6), 'reasons': reasons})
    return sorted(ranked, key=lambda p: (-p['match_score'], p['id']))[:max(0, limit)]
