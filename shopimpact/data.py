"""Bounded imports and versioned backups with lossless estimate snapshots."""
from __future__ import annotations

import csv
from datetime import date
import io
import json
import math
from uuid import uuid4

from .catalog import CATEGORIES
from .logic import _new_purchase, _new_wishlist_item, calculate_impact

MAX_BYTES = 5 * 1024 * 1024
MAX_PURCHASES = 5000
MAX_WISHLIST = 500


def _number(value, label: str, positive: bool = False) -> float:
    if isinstance(value, bool):
        raise ValueError(f'{label} must be a number')
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(f'{label} must be a finite non-negative number') from None
    if not math.isfinite(result) or result < 0 or result > 1e9 or (positive and result == 0):
        raise ValueError(f'{label} is outside the supported range')
    return round(result, 2)


def _text(value, label: str, required: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f'{label} must be text')
    value = value.strip()
    if (required and not value) or len(value) > 2000:
        raise ValueError(f'{label} is blank or too long')
    return value


def _day(value, label: str, future: bool = False) -> date:
    try:
        result = date.fromisoformat(str(value))
    except (ValueError, TypeError):
        raise ValueError(f'{label} must be an ISO date (YYYY-MM-DD)') from None
    if not future and result > date.today():
        raise ValueError(f'{label} cannot be in the future')
    return result


def _parse_purchase_csv(uploaded_file) -> tuple[list[dict], list[str]]:
    """Import category estimates; external CSV emissions are never trusted."""
    try:
        raw = uploaded_file.getvalue()
        if len(raw) > MAX_BYTES:
            return [], ['CSV files are limited to 5 MB.']
        reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
        headers = [h.strip().casefold() for h in reader.fieldnames or []]
        if len(headers) != len(set(headers)):
            return [], ['CSV column names must be unique.']
        if not {'product', 'category', 'price'} <= set(headers):
            return [], ['Required CSV columns: product, category, price.']
        reader.fieldnames = headers
        accepted, issues = [], []
        for index, row in enumerate(reader, 1):
            if index > MAX_PURCHASES:
                return [], ['Import is limited to 5,000 rows at a time.']
            try:
                if None in row:
                    raise ValueError('too many fields')
                product = _text(row.get('product'), 'product', required=True)
                category = _text(row.get('category'), 'category', required=True)
                if category not in CATEGORIES:
                    raise ValueError('unrecognized category')
                price = _number(row.get('price'), 'price')
                purchased_on = _day(row['date'].strip(), 'date') if (row.get('date') or '').strip() else date.today()
                brand = _text(row.get('brand') or '', 'brand')
                accepted.append(_new_purchase(product, category, brand, price, purchased_on))
            except (ValueError, AttributeError) as error:
                if len(issues) < 20:
                    issues.append(f'Row {index + 1}: {error}.')
        return accepted, issues
    except (UnicodeDecodeError, csv.Error, AttributeError) as error:
        return [], [f'Could not read this CSV: {error}']


def _make_data_backup(purchases: list[dict], wishlist: list[dict]) -> bytes:
    return json.dumps({'schema_version': 2, 'exported_on': date.today().isoformat(),
                       'purchases': purchases, 'wishlist': wishlist},
                      indent=2, ensure_ascii=False, allow_nan=False).encode('utf-8')


def _parse_data_backup(uploaded_file) -> tuple[dict | None, list[str]]:
    """Validate atomically, preserving IDs, dates, and recorded estimate snapshots.

    v1 green_savings mixed units, so reductions are recalculated from its saved
    footprint and category baseline. v2 preserves the baseline snapshot too.
    """
    try:
        raw = uploaded_file.getvalue()
        if len(raw) > MAX_BYTES:
            return None, ['Backup files are limited to 5 MB.']
        payload = json.loads(raw.decode('utf-8-sig'))
        if not isinstance(payload, dict) or type(payload.get('schema_version')) is not int or payload['schema_version'] not in (1, 2):
            return None, ['This is not a supported ShopImpact backup.']
        purchases, wishlist = payload.get('purchases'), payload.get('wishlist')
        if not isinstance(purchases, list) or not isinstance(wishlist, list):
            return None, ['The backup must contain purchase and wishlist lists.']
        if len(purchases) > MAX_PURCHASES or len(wishlist) > MAX_WISHLIST:
            return None, ['Backup limit: 5,000 purchases and 500 wishlist items.']
        result = {'purchases': [], 'wishlist': []}
        seen, issues = set(), []
        for kind, rows in [('purchases', purchases), ('wishlist', wishlist)]:
            for index, row in enumerate(rows, 1):
                try:
                    if not isinstance(row, dict):
                        raise ValueError('expected an object')
                    product = _text(row.get('product'), 'product', required=True)
                    category = _text(row.get('category'), 'category', required=True)
                    if category not in CATEGORIES:
                        raise ValueError('unrecognized category')
                    price = _number(row.get('price'), 'price', positive=kind == 'wishlist')
                    brand = _text(row.get('brand', ''), 'brand')
                    item_id = _text(row.get('id', str(uuid4())), 'id', required=True)
                    if item_id in seen:
                        raise ValueError('duplicate item ID')
                    seen.add(item_id)
                    if kind == 'purchases':
                        purchased_on = _day(row.get('date'), 'purchase date')
                        co2 = _number(row.get('co2', calculate_impact(category, price)), 'footprint')
                        baseline = _number(row.get('baseline_co2', calculate_impact(category, price)), 'baseline')
                        item = _new_purchase(product, category, brand, price, purchased_on, co2_override=co2)
                        item.update(baseline_co2=baseline, carbon_saved_kg=max(0, round(baseline - co2, 2)),
                                    estimate_method=_text(row.get('estimate_method', 'legacy-snapshot'), 'estimate method', True))
                        if payload['schema_version'] == 2:
                            stored = _number(row.get('carbon_saved_kg', 0), 'carbon reduction')
                            if abs(stored - item['carbon_saved_kg']) > 0.011:
                                raise ValueError('carbon reduction does not match its baseline')
                    else:
                        revisit_on = _day(row.get('revisit_on'), 'revisit date', future=True)
                        priority = row.get('priority', 'Want')
                        if priority not in ('Need', 'Want'):
                            raise ValueError('invalid priority')
                        item = _new_wishlist_item(product, category, brand, price, revisit_on, priority,
                                                  _text(row.get('note', ''), 'note'))
                        item['added_on'] = _day(row.get('added_on', date.today().isoformat()), 'added date').isoformat()
                        item['estimated_co2'] = _number(row.get('estimated_co2', item['estimated_co2']), 'wishlist footprint')
                    item['id'] = item_id
                    result[kind].append(item)
                except (ValueError, TypeError, OverflowError) as error:
                    if len(issues) < 20:
                        issues.append(f'{kind.title()} item {index}: {error}.')
        return (None, issues) if issues else (result, [])
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError, RecursionError) as error:
        return None, [f'Could not read this backup: {error}']
