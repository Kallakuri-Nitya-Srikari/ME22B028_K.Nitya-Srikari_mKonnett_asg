"""
Sales API client with JSON caching (FIXED for API response structure).
"""

import os
import json
import time
from typing import List, Dict, Any
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SALES_API_URL = os.getenv('SALES_API_URL', 'https://sandbox.mkonnekt.net/ch-portal/api/v1/orders/recent')
CACHE_PATH = Path(os.getenv('CACHE_PATH', './.cache/orders_cache.json'))
CACHE_TTL = int(os.getenv('CACHE_TTL_SECONDS', 60 * 5))  # 5 minutes default


def _ensure_cache_dir():
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)


def fetch_recent_orders(use_cache: bool = True) -> List[Dict[str, Any]]:
    """
    Fetch recent orders from the Sales API.
    Returns a list of order dicts, not the full wrapper object.
    """
    _ensure_cache_dir()

    # Use cached data if valid
    if use_cache and CACHE_PATH.exists():
        try:
            with open(CACHE_PATH, 'r') as f:
                payload = json.load(f)
            ts = payload.get('_cached_at', 0)
            if time.time() - ts < CACHE_TTL:
                data = payload.get('data', [])
                if isinstance(data, dict) and "orders" in data:
                    return data["orders"]
                return data
        except Exception:
            pass

    # Fetch from API
    try:
        resp = requests.get(SALES_API_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()   # <-- Now a dict, not a list

        # ✅ FIX: Extract "orders" list if present
        orders = data.get("orders", data)

        # Save entire data to cache to allow future usage
        try:
            with open(CACHE_PATH, 'w') as f:
                json.dump({'_cached_at': time.time(), 'data': data}, f)
        except Exception:
            pass

        # Must return a list
        if not isinstance(orders, list):
            raise ValueError("API format changed: 'orders' is not a list")

        return orders

    except requests.RequestException as e:
        # If API fails, fallback to cached data
        if CACHE_PATH.exists():
            try:
                with open(CACHE_PATH, 'r') as f:
                    payload = json.load(f)
                data = payload.get('data', {})

                if isinstance(data, dict) and "orders" in data:
                    return data["orders"]
                elif isinstance(data, list):
                    return data
            except Exception:
                pass

        raise RuntimeError(f"Failed to fetch Sales API: {e}")


def flatten_orders(orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Flatten orders into line items for analysis."""
    items = []
    if not isinstance(orders, list):
        return items

    for order in orders:
        if not isinstance(order, dict):
            continue

        created = order.get('createdTime')
        total = order.get('total')
        currency = order.get('currency')

        for li in order.get('lineItems', []) or []:
            item = dict(li)
            item['_order_created'] = created
            item['_order_total'] = total
            item['_order_currency'] = currency
            items.append(item)

    return items
