#!/usr/bin/env python3
"""flatperf CLI entry point."""

from flatperf.commands import (
    profile, compare,
    search, bench_search,
    join, bench_join,
    aggregate, bench_aggregate,
    encrypt, decrypt,
    compress, delete_bench,
)
from flatperf.generate import generate

import sys


def main():
    """Main entry point for flatperf CLI."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="flatperf",
        description="Profiling toolkit for Flatseek build pipeline",
    )
    sub = parser.add_subparsers(dest="command")

    # ── generate ──────────────────────────────────────────────────────────────
    g = sub.add_parser("generate", help="Generate test CSV data for profiling")
    g.add_argument("--schema", default="article",
                   choices=["article", "users", "transactions"],
                   help="Data schema to generate (default: article)")
    g.add_argument("--rows", type=int, default=1000,
                   help="Number of rows to generate (default: 1000)")
    g.add_argument("--output", required=True,
                   help="Output CSV file path")

    # ── build: profile ────────────────────────────────────────────────────────
    p = sub.add_parser("profile", help="Profile a single Flatseek build")
    p.add_argument("csv", help="CSV / JSON file or directory to index")
    p.add_argument("-w", "--workers", type=int, default=1)
    p.add_argument("-r", "--rows", type=int, default=None)
    p.add_argument("-n", "--top", type=int, default=25)
    p.add_argument("--out", default=None)
    p.add_argument("--keep-output", action="store_true")
    p.add_argument("--flatseek-src", default=None)

    # ── build: compare ─────────────────────────────────────────────────────────
    c = sub.add_parser("compare", help="A/B benchmark a Flatseek build")
    c.add_argument("csv", help="CSV / JSON file or directory")
    c.add_argument("-n", "--runs", type=int, default=3)
    c.add_argument("-w", "--workers", type=int, default=1)
    c.add_argument("-r", "--rows", type=int, default=None)
    c.add_argument("--tag", default=None)
    c.add_argument("--flatseek-src", default=None)

    # ── search: profile ────────────────────────────────────────────────────────
    sp = sub.add_parser("search", help="Profile a single search query")
    sp.add_argument("data_dir", help="Index directory")
    sp.add_argument("query", help="Search query string")
    sp.add_argument("-n", "--top", type=int, default=25)
    sp.add_argument("-p", "--page-size", type=int, default=20)
    sp.add_argument("--flatseek-src", default=None)

    # ── search: bench ──────────────────────────────────────────────────────────
    sb = sub.add_parser("bench-search", help="Benchmark search queries repeatedly")
    sb.add_argument("data_dir", help="Index directory")
    sb.add_argument("query", help="Search query string")
    sb.add_argument("-n", "--runs", type=int, default=10)
    sb.add_argument("-p", "--page-size", type=int, default=20)
    sb.add_argument("--tag", default=None)
    sb.add_argument("--flatseek-src", default=None)

    # ── join: profile ─────────────────────────────────────────────────────────
    j = sub.add_parser("join", help="Profile a single join query")
    j.add_argument("data_dir", help="Index directory")
    j.add_argument("query_a", help="First query (e.g. '_dataset:logs AND service:api')")
    j.add_argument("query_b", help="Second query")
    j.add_argument("--on", required=True, help="Shared field to join on (e.g. trace_id)")
    j.add_argument("-n", "--top", type=int, default=25)
    j.add_argument("-p", "--page-size", type=int, default=20)
    j.add_argument("--flatseek-src", default=None)

    # ── join: bench ───────────────────────────────────────────────────────────
    jb = sub.add_parser("bench-join", help="Benchmark join queries repeatedly")
    jb.add_argument("data_dir", help="Index directory")
    jb.add_argument("query_a", help="First query")
    jb.add_argument("query_b", help="Second query")
    jb.add_argument("--on", required=True, help="Shared field to join on")
    jb.add_argument("-n", "--runs", type=int, default=10)
    jb.add_argument("-p", "--page-size", type=int, default=20)
    jb.add_argument("--tag", default=None)
    jb.add_argument("--flatseek-src", default=None)

    # ── aggregate: profile ─────────────────────────────────────────────────────
    ag = sub.add_parser("aggregate", help="Profile a single aggregation query")
    ag.add_argument("data_dir", help="Index directory")
    ag.add_argument("-q", "--query", default=None,
                    help="Lucene query to filter docs (optional)")
    ag.add_argument("--aggs", default=None,
                    help="JSON aggregation config, e.g. '{\"terms\":{\"field\":\"category\",\"size\":10}}'")
    ag.add_argument("-s", "--size", type=int, default=10,
                    help="Max buckets for terms aggregation (default: 10)")
    ag.add_argument("-n", "--top", type=int, default=25)
    ag.add_argument("--flatseek-src", default=None)

    # ── aggregate: bench ──────────────────────────────────────────────────────
    agb = sub.add_parser("bench-aggregate", help="Benchmark aggregation queries repeatedly")
    agb.add_argument("data_dir", help="Index directory")
    agb.add_argument("-q", "--query", default=None,
                     help="Lucene query to filter docs (optional)")
    agb.add_argument("--aggs", default=None,
                     help="JSON aggregation config")
    agb.add_argument("-s", "--size", type=int, default=10)
    agb.add_argument("-n", "--runs", type=int, default=10)
    agb.add_argument("--tag", default=None)
    agb.add_argument("--flatseek-src", default=None)

    # ── encrypt ────────────────────────────────────────────────────────────────
    enc = sub.add_parser("encrypt", help="Profile index encryption")
    enc.add_argument("data_dir", help="Index directory")
    enc.add_argument("--passphrase", default=None,
                     help="Encryption passphrase (prompted if omitted)")
    enc.add_argument("-w", "--workers", type=int, default=None)
    enc.add_argument("-n", "--top", type=int, default=25)
    enc.add_argument("--flatseek-src", default=None)

    # ── decrypt ────────────────────────────────────────────────────────────────
    dec = sub.add_parser("decrypt", help="Profile index decryption")
    dec.add_argument("data_dir", help="Index directory")
    dec.add_argument("--passphrase", default=None,
                      help="Decryption passphrase (prompted if omitted)")
    dec.add_argument("-n", "--top", type=int, default=25)
    dec.add_argument("--flatseek-src", default=None)

    # ── compress ───────────────────────────────────────────────────────────────
    cp = sub.add_parser("compress", help="Profile index compression")
    cp.add_argument("data_dir", help="Index directory")
    cp.add_argument("-l", "--level", type=int, default=6,
                    choices=range(1, 10), help="Compression level 1-9 (default: 6)")
    cp.add_argument("-w", "--workers", type=int, default=None)
    cp.add_argument("-n", "--top", type=int, default=25)
    cp.add_argument("--flatseek-src", default=None)

    # ── delete ─────────────────────────────────────────────────────────────────
    d = sub.add_parser("delete", help="Benchmark index deletion")
    d.add_argument("data_dir", help="Index directory to delete")
    d.add_argument("-n", "--runs", type=int, default=3)
    d.add_argument("-w", "--workers", type=int, default=None)
    d.add_argument("--flatseek-src", default=None)

    args = parser.parse_args()

    if args.command == "generate":
        sys.exit(generate(args))
    elif args.command == "profile":
        sys.exit(profile(args))
    elif args.command == "compare":
        sys.exit(compare(args))
    elif args.command == "search":
        sys.exit(search(args))
    elif args.command == "bench-search":
        sys.exit(bench_search(args))
    elif args.command == "join":
        sys.exit(join(args))
    elif args.command == "bench-join":
        sys.exit(bench_join(args))
    elif args.command == "aggregate":
        sys.exit(aggregate(args))
    elif args.command == "bench-aggregate":
        sys.exit(bench_aggregate(args))
    elif args.command == "encrypt":
        sys.exit(encrypt(args))
    elif args.command == "decrypt":
        sys.exit(decrypt(args))
    elif args.command == "compress":
        sys.exit(compress(args))
    elif args.command == "delete":
        sys.exit(delete_bench(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()