"""Generate test CSV data for profiling."""

from __future__ import annotations

import argparse
import csv
import random
import string
from datetime import datetime, timedelta


SCHEMAS = {
    "article": {
        "fields": ["id", "title", "content", "author", "category", "published_at", "views", "status"],
        "types": {
            "id": "int",
            "title": "text",
            "content": "text",
            "author": "keyword",
            "category": "keyword",
            "published_at": "date",
            "views": "int",
            "status": "keyword",
        },
    },
    "users": {
        "fields": ["id", "name", "email", "country", "created_at", "age", "is_active"],
        "types": {
            "id": "int",
            "name": "text",
            "email": "keyword",
            "country": "keyword",
            "created_at": "date",
            "age": "int",
            "is_active": "bool",
        },
    },
    "transactions": {
        "fields": ["id", "user_id", "amount", "currency", "merchant", "location", "created_at", "status"],
        "types": {
            "id": "int",
            "user_id": "int",
            "amount": "float",
            "currency": "keyword",
            "merchant": "text",
            "location": "keyword",
            "created_at": "date",
            "status": "keyword",
        },
    },
}


def _random_text(min_words=3, max_words=10) -> str:
    words = [
        "".join(random.choices(string.ascii_lowercase, k=random.randint(3, 12)))
        for _ in range(random.randint(min_words, max_words))
    ]
    return " ".join(words)


def _random_date() -> str:
    return (datetime(2024, 1, 1) + timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")


def _random_name() -> str:
    first = _random_text(1, 1)
    last = _random_text(1, 1)
    return f"{first.capitalize()} {last.capitalize()}"


def _random_email() -> str:
    user = _random_text(1, 1).lower()
    domain = random.choice(["gmail.com", "yahoo.com", "outlook.com", "company.io"])
    return f"{user}@{domain}"


def generate(args: argparse.Namespace) -> int:
    """Generate test CSV data for profiling."""
    schema_name = args.schema.lower()
    if schema_name not in SCHEMAS:
        print(f"Unknown schema: {args.schema}", file=__import__('sys').stderr)
        print(f"Available: {', '.join(SCHEMAS.keys())}", file=__import__('sys').stderr)
        return 1

    schema = SCHEMAS[schema_name]
    fields = schema["fields"]
    types = schema["types"]

    rows_data = []
    for i in range(args.rows):
        row = {}
        for field in fields:
            t = types[field]
            if t == "int":
                row[field] = random.randint(1, 1000000) if "id" not in field else i + 1
            elif t == "float":
                row[field] = round(random.uniform(0.01, 99999.99), 2)
            elif t == "text":
                row[field] = _random_text(4, 12)
            elif t == "keyword":
                if field == "category":
                    row[field] = random.choice(["tech", "news", "opinion", "sports", "entertainment"])
                elif field == "country":
                    row[field] = random.choice(["US", "ID", "GB", "DE", "FR", "JP", "CN", "BR"])
                elif field == "currency":
                    row[field] = random.choice(["USD", "EUR", "GBP", "IDR", "JPY"])
                elif field == "status":
                    row[field] = random.choice(["active", "pending", "completed", "cancelled"])
                elif field == "is_active":
                    row[field] = random.choice([True, False])
                else:
                    row[field] = _random_text(1, 2).replace(" ", "_").lower()
            elif t == "date":
                if field == "published_at":
                    row[field] = _random_date()
                elif field == "created_at":
                    row[field] = _random_date()
                else:
                    row[field] = _random_date()
        rows_data.append(row)

    output_path = args.output
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows_data)

    size_kb = __import__('os').path.getsize(output_path) / 1024
    print(f"Generated {args.rows:,} rows → {output_path} ({size_kb:.1f} KB)", file=__import__('sys').stderr)
    return 0