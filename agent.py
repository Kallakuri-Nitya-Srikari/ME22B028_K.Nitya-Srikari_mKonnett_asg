"""
Main CLI for the Sales Insight Agent (PowerShell Friendly).
"""

import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import argparse
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import dateparser
from rich.console import Console
from rich.table import Table

from sales_api import fetch_recent_orders, flatten_orders
from llm import polish_response

console = Console()


def parse_args():
    p = argparse.ArgumentParser(description='Sales Insight Agent - CLI')
    p.add_argument('--query', type=str, required=True, help='Natural language query')
    p.add_argument('--no-cache', action='store_true', help='Do not use local cache')
    return p.parse_args()


def filter_orders_by_date(orders, start_dt=None, end_dt=None):
    """Filter orders by date range."""
    filtered = []
    for o in orders:
        if not isinstance(o, dict):
            continue  # skip bad data
        ts = o.get('createdTime')
        if not ts:
            continue
        dt = dateparser.parse(ts)
        if not dt:
            continue
        if start_dt and dt < start_dt:
            continue
        if end_dt and dt > end_dt:
            continue
        filtered.append(o)
    return filtered


def interpret_date_range(user_text: str):
    now = datetime.now()
    text = (user_text or "").lower()

    if "yesterday" in text:
        start = datetime(now.year, now.month, now.day) - timedelta(days=1)
        return start, start + timedelta(days=1)

    if "today" in text:
        start = datetime(now.year, now.month, now.day)
        return start, start + timedelta(days=1)

    if "last week" in text:
        last_monday = (now - timedelta(days=now.weekday()+7)).replace(hour=0, minute=0)
        return last_monday, last_monday + timedelta(days=7)

    if "this week" in text:
        monday = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0)
        return monday, monday + timedelta(days=7)

    if "last month" in text:
        first_of_this_month = datetime(now.year, now.month, 1)
        last_month_end = first_of_this_month - timedelta(days=1)
        start = datetime(last_month_end.year, last_month_end.month, 1)
        return start, last_month_end

    return None, None


def compute_metrics(orders):
    flat_items = flatten_orders(orders)

    total_revenue = sum((o.get('total') or 0) for o in orders if isinstance(o, dict))
    num_orders = len(orders)
    avg_order_value = (total_revenue / num_orders) if num_orders else 0

    name_counts = Counter()
    revenue_by_item = defaultdict(int)

    for li in flat_items:
        name = li.get('name') or "(unknown)"
        name_counts[name] += 1
        revenue_by_item[name] += (li.get('price') or 0)

    top_items = [
        {"name": n, "count": c, "revenue": revenue_by_item[n]}
        for n, c in name_counts.most_common(5)
    ]

    return {
        "num_orders": num_orders,
        "total_revenue": total_revenue,
        "avg_order_value": avg_order_value,
        "top_items": top_items
    }


def format_currency(cents):
    return f"${cents/100:.2f}"


def main():
    args = parse_args()
    query = args.query

    try:
        orders = fetch_recent_orders(use_cache=not args.no_cache)
        if not isinstance(orders, list):
            raise ValueError("API returned unexpected format.")
    except Exception as e:
        console.print(f"[red]Error fetching orders: {e}[/red]")
        return

    start_dt, end_dt = interpret_date_range(query)
    filtered_orders = filter_orders_by_date(orders, start_dt, end_dt)

    metrics = compute_metrics(filtered_orders)

    summary = (
        f"Orders: {metrics['num_orders']}\n"
        f"Revenue: {format_currency(metrics['total_revenue'])}\n"
        f"Avg Order: {format_currency(metrics['avg_order_value'])}"
    )

    polished = polish_response(summary, query)

    console.rule("[bold green]Sales Insight Agent[/bold green]")
    console.print(f"Query: [bold]{query}[/bold]\n")
    console.print(polished)

    table = Table(title="Top Items")
    table.add_column("Item")
    table.add_column("Count", justify="right")
    table.add_column("Revenue", justify="right")

    for it in metrics["top_items"]:
        table.add_row(it["name"], str(it["count"]), format_currency(it["revenue"]))

    console.print(table)


if __name__ == "__main__":
    main()
