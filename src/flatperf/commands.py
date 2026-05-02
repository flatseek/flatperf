"""Profiling commands for flatperf CLI."""

from __future__ import annotations

import argparse
import cProfile
import io
import os
import pstats
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path


# ─── Helpers ────────────────────────────────────────────────────────────────

def _resolve_flatseek_src(flatseek_src: str | None) -> str:
    """Find the flatseek source dir."""
    env = os.environ.get("FLATSEEK_SRC")
    if env and os.path.isdir(env):
        return os.path.abspath(env)
    if flatseek_src and os.path.isdir(flatseek_src):
        return os.path.abspath(flatseek_src)

    # Try importing from installed package first (pip install -e /path/to/flatseek)
    try:
        import flatseek
        return ""
    except ImportError:
        pass

    candidates = [
        Path(__file__).parent.parent.parent.parent / "flatseek" / "src",
        Path(__file__).parent.parent.parent.parent / "flatseek",
        Path(__file__).parent.parent.parent / "flatseek" / "src",
    ]
    for cand in candidates:
        if cand.is_dir():
            return str(cand)
    raise SystemExit(
        "Could not locate flatseek source. Set FLATSEEK_SRC env var or use --flatseek-src."
    )


def _slice_csv(input_path: str, n_rows: int) -> str:
    """Return path to a temp CSV containing the header + first n_rows rows."""
    fd, dst = tempfile.mkstemp(prefix="flatprofile_", suffix=".csv")
    os.close(fd)
    subprocess.run(
        ["head", "-n", str(n_rows + 1), input_path],
        stdout=open(dst, "wb"),
        check=True,
    )
    return dst


def _count_rows(path: str) -> int:
    """Quick row count (header excluded)."""
    with open(path, "rb") as f:
        return max(0, sum(1 for _ in f) - 1)


def _print_section(title: str) -> None:
    bar = "=" * 78
    print(bar, file=sys.stderr)
    print(f" {title}", file=sys.stderr)
    print(bar, file=sys.stderr)


def _fmt_duration(secs: float) -> str:
    if secs < 60:
        return f"{secs:.2f}s"
    m, s = divmod(secs, 60)
    return f"{int(m)}m{s:.1f}s"


# ─── Build commands ─────────────────────────────────────────────────────────

def profile(args: argparse.Namespace) -> int:
    """Profile a single Flatseek build."""
    src = _resolve_flatseek_src(args.flatseek_src)
    if src:
        sys.path.insert(0, src)

    try:
        from flatseek.cli import cmd_build  # noqa: E402
    except ImportError as e:
        print(f"Failed to import flatseek from {src}: {e}", file=sys.stderr)
        return 2

    csv_in = os.path.abspath(args.csv)
    if not os.path.exists(csv_in):
        print(f"Input not found: {csv_in}", file=sys.stderr)
        return 2

    sliced = None
    target_csv = csv_in
    if args.rows and os.path.isfile(csv_in):
        full_rows = _count_rows(csv_in)
        if full_rows > args.rows:
            target_csv = _slice_csv(csv_in, args.rows)
            sliced = target_csv

    rows = _count_rows(target_csv) if os.path.isfile(target_csv) else None

    out_dir = tempfile.mkdtemp(prefix="flatprofile_idx_")
    print(f"input:    {target_csv}", file=sys.stderr)
    if rows is not None:
        print(f"rows:     {rows:,}", file=sys.stderr)
    print(f"workers:  {args.workers}", file=sys.stderr)
    print(f"output:   {out_dir}", file=sys.stderr)
    print(file=sys.stderr)

    ns = argparse.Namespace(
        csv_dir=target_csv, output=out_dir, map=None, dataset=None,
        sep=",", columns=None, workers=args.workers,
        plan=None, worker_id=None, estimate=False,
        dedup=False, dedup_fields=None, daemon=False,
    )

    profiler = cProfile.Profile()
    t0 = time.monotonic()
    profiler.enable()
    try:
        cmd_build(ns)
    finally:
        profiler.disable()
        elapsed = time.monotonic() - t0

    if args.out:
        profiler.dump_stats(args.out)
        print(f"\n.prof saved → {args.out}", file=sys.stderr)

    _print_section("wall summary")
    rate = (rows / elapsed) if (rows and elapsed > 0) else 0
    print(f" wall:        {elapsed:.2f}s", file=sys.stderr)
    if rows is not None:
        print(f" docs:        {rows:,}", file=sys.stderr)
        print(f" throughput:  {rate:,.0f} docs/s", file=sys.stderr)

    _print_section(f"top {args.top} hotspots — sorted by tottime")
    s = io.StringIO()
    pstats.Stats(profiler, stream=s).strip_dirs().sort_stats("tottime").print_stats(args.top)
    print(s.getvalue(), file=sys.stderr)

    _print_section(f"top {args.top} hotspots — sorted by cumulative")
    s = io.StringIO()
    pstats.Stats(profiler, stream=s).strip_dirs().sort_stats("cumulative").print_stats(args.top)
    print(s.getvalue(), file=sys.stderr)

    if sliced and os.path.exists(sliced):
        os.unlink(sliced)
    if not args.keep_output:
        shutil.rmtree(out_dir, ignore_errors=True)
    else:
        print(f"index kept at: {out_dir}", file=sys.stderr)

    return 0


def compare(args: argparse.Namespace) -> int:
    """A/B benchmark a Flatseek build."""
    src = _resolve_flatseek_src(args.flatseek_src)
    if src:
        sys.path.insert(0, src)

    try:
        from flatseek.cli import cmd_build  # noqa: E402
    except ImportError as e:
        print(f"Failed to import flatseek from {src}: {e}", file=sys.stderr)
        return 2

    csv_in = os.path.abspath(args.csv)
    if not os.path.exists(csv_in):
        print(f"Input not found: {csv_in}", file=sys.stderr)
        return 2

    target_csv = csv_in
    sliced = None
    if args.rows and os.path.isfile(csv_in):
        full_rows = _count_rows(csv_in)
        if full_rows > args.rows:
            target_csv = _slice_csv(csv_in, args.rows)
            sliced = target_csv

    rows = _count_rows(target_csv) if os.path.isfile(target_csv) else None
    label = args.tag or "build"

    print(f"input:   {target_csv}", file=sys.stderr)
    if rows is not None:
        print(f"rows:    {rows:,}", file=sys.stderr)
    print(f"workers: {args.workers}", file=sys.stderr)
    print(f"runs:    {args.runs}", file=sys.stderr)
    print(file=sys.stderr)

    walls = []
    for i in range(args.runs):
        out_dir = tempfile.mkdtemp(prefix="flatcompare_idx_")
        ns = argparse.Namespace(
            csv_dir=target_csv, output=out_dir, map=None, dataset=None,
            sep=",", columns=None, workers=args.workers,
            plan=None, worker_id=None, estimate=False,
            dedup=False, dedup_fields=None, daemon=False,
        )
        t0 = time.monotonic()
        cmd_build(ns)
        elapsed = time.monotonic() - t0
        walls.append(elapsed)
        rate = rows / elapsed if (rows and elapsed > 0) else 0
        print(f"  run {i+1}/{args.runs}: {_fmt_duration(elapsed):>9}  ({rate:,.0f} docs/s)",
              file=sys.stderr)
        shutil.rmtree(out_dir, ignore_errors=True)

    print(file=sys.stderr)
    walls.sort()
    w_min = walls[0]
    w_max = walls[-1]
    w_med = statistics.median(walls)
    rate_med = rows / w_med if (rows and w_med > 0) else 0

    print("-" * 76, file=sys.stderr)
    header = f"{'tag':<24} {'runs':<6} {'min':<10} {'median':<10} {'max':<10} {'docs/s (med)':<14}"
    print(header, file=sys.stderr)
    print("-" * 76, file=sys.stderr)
    print(f"{label:<24} {args.runs:<6} {_fmt_duration(w_min):<10} {_fmt_duration(w_med):<10} {_fmt_duration(w_max):<10} {rate_med:>10,.0f}",
          file=sys.stderr)

    if sliced and os.path.exists(sliced):
        os.unlink(sliced)
    return 0


# ─── Search commands ─────────────────────────────────────────────────────────

def search(args: argparse.Namespace) -> int:
    """Profile a single search query."""
    src = _resolve_flatseek_src(args.flatseek_src)
    if src:
        sys.path.insert(0, src)

    try:
        from flatseek.core.query_engine import QueryEngine  # noqa: E402
    except ImportError as e:
        print(f"Failed to import flatseek from {src}: {e}", file=sys.stderr)
        return 2

    data_dir = os.path.abspath(args.data_dir)
    if not os.path.isdir(data_dir):
        print(f"Data directory not found: {data_dir}", file=sys.stderr)
        return 2

    qe = QueryEngine(data_dir)

    profiler = cProfile.Profile()
    t0 = time.monotonic()
    profiler.enable()
    try:
        result = qe.query(args.query, page=0, page_size=args.page_size)
    finally:
        profiler.disable()
        elapsed = time.monotonic() - t0

    _print_section("search result")
    print(f" query:      {args.query}", file=sys.stderr)
    print(f" total:      {result['total']:,} matches", file=sys.stderr)
    print(f" returned:   {len(result['results'])} docs", file=sys.stderr)
    print(f" wall:       {elapsed:.4f}s", file=sys.stderr)
    print(f" qps:        {1/elapsed:.1f} queries/s", file=sys.stderr)

    _print_section(f"top {args.top} hotspots — sorted by tottime")
    s = io.StringIO()
    pstats.Stats(profiler, stream=s).strip_dirs().sort_stats("tottime").print_stats(args.top)
    print(s.getvalue(), file=sys.stderr)

    _print_section(f"top {args.top} hotspots — sorted by cumulative")
    s = io.StringIO()
    pstats.Stats(profiler, stream=s).strip_dirs().sort_stats("cumulative").print_stats(args.top)
    print(s.getvalue(), file=sys.stderr)

    return 0


def bench_search(args: argparse.Namespace) -> int:
    """Benchmark search queries, repeated N times."""
    src = _resolve_flatseek_src(args.flatseek_src)
    if src:
        sys.path.insert(0, src)

    try:
        from flatseek.core.query_engine import QueryEngine  # noqa: E402
    except ImportError as e:
        print(f"Failed to import flatseek from {src}: {e}", file=sys.stderr)
        return 2

    data_dir = os.path.abspath(args.data_dir)
    if not os.path.isdir(data_dir):
        print(f"Data directory not found: {data_dir}", file=sys.stderr)
        return 2

    qe = QueryEngine(data_dir)
    label = args.tag or args.query

    print(f"query:    {args.query}", file=sys.stderr)
    print(f"data:     {data_dir}", file=sys.stderr)
    print(f"runs:     {args.runs}", file=sys.stderr)
    print(file=sys.stderr)

    latencies = []
    for i in range(args.runs):
        t0 = time.monotonic()
        result = qe.query(args.query, page=0, page_size=args.page_size)
        elapsed = time.monotonic() - t0
        latencies.append(elapsed * 1000)  # ms
        print(f"  run {i+1}/{args.runs}: {elapsed*1000:.2f}ms  ({result['total']:,} matches)",
              file=sys.stderr)

    print(file=sys.stderr)
    latencies.sort()
    p50 = statistics.median(latencies)
    p95 = latencies[int(len(latencies) * 0.95)] if len(latencies) > 1 else latencies[0]
    p99 = latencies[int(len(latencies) * 0.99)] if len(latencies) > 1 else latencies[0]
    qps_med = 1000 / p50

    print("-" * 76, file=sys.stderr)
    header = f"{'query':<30} {'runs':<6} {'min(ms)':<10} {'median':<10} {'p95':<10} {'p99':<10} {'qps':<10}"
    print(header, file=sys.stderr)
    print("-" * 76, file=sys.stderr)
    print(f"{label[:30]:<30} {args.runs:<6} {latencies[0]:<10.2f} {p50:<10.2f} {p95:<10.2f} {p99:<10.2f} {qps_med:<10.1f}",
          file=sys.stderr)

    return 0


# ─── Join ────────────────────────────────────────────────────────────────────

def join(args: argparse.Namespace) -> int:
    """Profile a single join query."""
    src = _resolve_flatseek_src(args.flatseek_src)
    if src:
        sys.path.insert(0, src)

    try:
        from flatseek.core.query_engine import QueryEngine  # noqa: E402
    except ImportError as e:
        print(f"Failed to import flatseek from {src}: {e}", file=sys.stderr)
        return 2

    data_dir = os.path.abspath(args.data_dir)
    if not os.path.isdir(data_dir):
        print(f"Data directory not found: {data_dir}", file=sys.stderr)
        return 2

    qe = QueryEngine(data_dir)

    profiler = cProfile.Profile()
    t0 = time.monotonic()
    profiler.enable()
    try:
        result = qe.join(args.query_a, args.query_b, on=args.on,
                         page=0, page_size=args.page_size)
    except SyntaxError as e:
        print(f"Query syntax error: {e}", file=sys.stderr)
        return 1
    finally:
        profiler.disable()
        elapsed = time.monotonic() - t0

    _print_section("join result")
    print(f" query_a:    {args.query_a}", file=sys.stderr)
    print(f" query_b:    {args.query_b}", file=sys.stderr)
    print(f" join_on:   {args.on}", file=sys.stderr)
    print(f" total:     {result['total']:,} pairs", file=sys.stderr)
    print(f" returned:  {len(result['results'])} pairs", file=sys.stderr)
    print(f" wall:      {elapsed:.4f}s", file=sys.stderr)
    print(f" qps:       {1/elapsed:.1f} joins/s", file=sys.stderr)

    _print_section(f"top {args.top} hotspots — sorted by tottime")
    s = io.StringIO()
    pstats.Stats(profiler, stream=s).strip_dirs().sort_stats("tottime").print_stats(args.top)
    print(s.getvalue(), file=sys.stderr)

    _print_section(f"top {args.top} hotspots — sorted by cumulative")
    s = io.StringIO()
    pstats.Stats(profiler, stream=s).strip_dirs().sort_stats("cumulative").print_stats(args.top)
    print(s.getvalue(), file=sys.stderr)

    return 0


def bench_join(args: argparse.Namespace) -> int:
    """Benchmark join queries, repeated N times."""
    src = _resolve_flatseek_src(args.flatseek_src)
    if src:
        sys.path.insert(0, src)

    try:
        from flatseek.core.query_engine import QueryEngine  # noqa: E402
    except ImportError as e:
        print(f"Failed to import flatseek from {src}: {e}", file=sys.stderr)
        return 2

    data_dir = os.path.abspath(args.data_dir)
    if not os.path.isdir(data_dir):
        print(f"Data directory not found: {data_dir}", file=sys.stderr)
        return 2

    qe = QueryEngine(data_dir)
    label = args.tag or f"{args.query_a}+{args.query_b}"

    print(f"query_a:   {args.query_a}", file=sys.stderr)
    print(f"query_b:   {args.query_b}", file=sys.stderr)
    print(f"join_on:   {args.on}", file=sys.stderr)
    print(f"data:      {data_dir}", file=sys.stderr)
    print(f"runs:      {args.runs}", file=sys.stderr)
    print(file=sys.stderr)

    latencies = []
    for i in range(args.runs):
        t0 = time.monotonic()
        result = qe.join(args.query_a, args.query_b, on=args.on,
                         page=0, page_size=args.page_size)
        elapsed = time.monotonic() - t0
        latencies.append(elapsed * 1000)  # ms
        print(f"  run {i+1}/{args.runs}: {elapsed*1000:.2f}ms  ({result['total']:,} pairs)",
              file=sys.stderr)

    print(file=sys.stderr)
    latencies.sort()
    p50 = statistics.median(latencies)
    p95 = latencies[int(len(latencies) * 0.95)] if len(latencies) > 1 else latencies[0]
    p99 = latencies[int(len(latencies) * 0.99)] if len(latencies) > 1 else latencies[0]
    qps_med = 1000 / p50

    print("-" * 76, file=sys.stderr)
    header = f"{'query':<36} {'runs':<6} {'min(ms)':<10} {'median':<10} {'p95':<10} {'p99':<10} {'qps':<10}"
    print(header, file=sys.stderr)
    print("-" * 76, file=sys.stderr)
    print(f"{label[:36]:<36} {args.runs:<6} {latencies[0]:<10.2f} {p50:<10.2f} {p95:<10.2f} {p99:<10.2f} {qps_med:<10.1f}",
          file=sys.stderr)

    return 0


# ─── Aggregate ─────────────────────────────────────────────────────────────

def aggregate(args: argparse.Namespace) -> int:
    """Profile a single aggregation query."""
    src = _resolve_flatseek_src(args.flatseek_src)
    if src:
        sys.path.insert(0, src)

    try:
        from flatseek.core.query_engine import QueryEngine  # noqa: E402
    except ImportError as e:
        print(f"Failed to import flatseek from {src}: {e}", file=sys.stderr)
        return 2

    data_dir = os.path.abspath(args.data_dir)
    if not os.path.isdir(data_dir):
        print(f"Data directory not found: {data_dir}", file=sys.stderr)
        return 2

    qe = QueryEngine(data_dir)

    # Parse aggregation config
    import json as _json
    try:
        aggs = _json.loads(args.aggs) if args.aggs else {}
    except Exception as e:
        print(f"Failed to parse --aggs JSON: {e}", file=sys.stderr)
        return 1

    profiler = cProfile.Profile()
    t0 = time.monotonic()
    profiler.enable()
    try:
        result = qe.aggregate(q=args.query, aggs=aggs, size=args.size)
    except Exception as e:
        print(f"Aggregation error: {e}", file=sys.stderr)
        return 1
    finally:
        profiler.disable()
        elapsed = time.monotonic() - t0

    _print_section("aggregate result")
    if args.query:
        print(f" query:      {args.query}", file=sys.stderr)
    print(f" aggs:       {args.aggs or '{}'}", file=sys.stderr)
    print(f" took:       {result.get('took', 0):.2f}ms", file=sys.stderr)
    print(f" hits:       {result.get('hits', {}).get('total', 0):,}", file=sys.stderr)
    if result.get("aggregations"):
        for name, agg_result in result["aggregations"].items():
            print(f" {name}:     {agg_result}", file=sys.stderr)
    print(f" wall:       {elapsed:.4f}s", file=sys.stderr)
    print(f" qps:        {1/elapsed:.1f} agg/s", file=sys.stderr)

    _print_section(f"top {args.top} hotspots — sorted by tottime")
    s = io.StringIO()
    pstats.Stats(profiler, stream=s).strip_dirs().sort_stats("tottime").print_stats(args.top)
    print(s.getvalue(), file=sys.stderr)

    _print_section(f"top {args.top} hotspots — sorted by cumulative")
    s = io.StringIO()
    pstats.Stats(profiler, stream=s).strip_dirs().sort_stats("cumulative").print_stats(args.top)
    print(s.getvalue(), file=sys.stderr)

    return 0


def bench_aggregate(args: argparse.Namespace) -> int:
    """Benchmark aggregation queries, repeated N times."""
    src = _resolve_flatseek_src(args.flatseek_src)
    if src:
        sys.path.insert(0, src)

    try:
        from flatseek.core.query_engine import QueryEngine  # noqa: E402
    except ImportError as e:
        print(f"Failed to import flatseek from {src}: {e}", file=sys.stderr)
        return 2

    data_dir = os.path.abspath(args.data_dir)
    if not os.path.isdir(data_dir):
        print(f"Data directory not found: {data_dir}", file=sys.stderr)
        return 2

    qe = QueryEngine(data_dir)

    import json as _json
    try:
        aggs = _json.loads(args.aggs) if args.aggs else {}
    except Exception as e:
        print(f"Failed to parse --aggs JSON: {e}", file=sys.stderr)
        return 1

    label = args.tag or f"agg"

    print(f"query:    {args.query or '(none)'}", file=sys.stderr)
    print(f"aggs:     {args.aggs or '{}'}", file=sys.stderr)
    print(f"data:     {data_dir}", file=sys.stderr)
    print(f"runs:     {args.runs}", file=sys.stderr)
    print(file=sys.stderr)

    latencies = []
    for i in range(args.runs):
        t0 = time.monotonic()
        result = qe.aggregate(q=args.query, aggs=aggs, size=args.size)
        elapsed = time.monotonic() - t0
        latencies.append(elapsed * 1000)  # ms
        hits = result.get("hits", {}).get("total", 0)
        print(f"  run {i+1}/{args.runs}: {elapsed*1000:.2f}ms  ({hits:,} hits)",
              file=sys.stderr)

    print(file=sys.stderr)
    latencies.sort()
    p50 = statistics.median(latencies)
    p95 = latencies[int(len(latencies) * 0.95)] if len(latencies) > 1 else latencies[0]
    p99 = latencies[int(len(latencies) * 0.99)] if len(latencies) > 1 else latencies[0]
    qps_med = 1000 / p50

    print("-" * 76, file=sys.stderr)
    header = f"{'label':<30} {'runs':<6} {'min(ms)':<10} {'median':<10} {'p95':<10} {'p99':<10} {'qps':<10}"
    print(header, file=sys.stderr)
    print("-" * 76, file=sys.stderr)
    print(f"{label[:30]:<30} {args.runs:<6} {latencies[0]:<10.2f} {p50:<10.2f} {p95:<10.2f} {p99:<10.2f} {qps_med:<10.1f}",
          file=sys.stderr)

    return 0


# ─── Encrypt / Decrypt ──────────────────────────────────────────────────────

def encrypt(args: argparse.Namespace) -> int:
    """Profile index encryption."""
    src = _resolve_flatseek_src(args.flatseek_src)
    if src:
        sys.path.insert(0, src)

    try:
        from flatseek.cli import cmd_encrypt  # noqa: E402
    except ImportError as e:
        print(f"Failed to import flatseek from {src}: {e}", file=sys.stderr)
        return 2

    data_dir = os.path.abspath(args.data_dir)
    if not os.path.isdir(data_dir):
        print(f"Data directory not found: {data_dir}", file=sys.stderr)
        return 2

    if not args.passphrase:
        print("Passphrase required. Use --passphrase PASSPHRASE", file=sys.stderr)
        return 1

    profiler = cProfile.Profile()
    t0 = time.monotonic()
    profiler.enable()
    try:
        cmd_encrypt(argparse.Namespace(
            data_dir=data_dir,
            passphrase=args.passphrase,
        ))
    finally:
        profiler.disable()
        elapsed = time.monotonic() - t0

    _print_section("encrypt summary")
    print(f" wall:       {elapsed:.2f}s", file=sys.stderr)

    _print_section(f"top {args.top} hotspots — sorted by tottime")
    s = io.StringIO()
    pstats.Stats(profiler, stream=s).strip_dirs().sort_stats("tottime").print_stats(args.top)
    print(s.getvalue(), file=sys.stderr)

    return 0


def decrypt(args: argparse.Namespace) -> int:
    """Profile index decryption."""
    src = _resolve_flatseek_src(args.flatseek_src)
    if src:
        sys.path.insert(0, src)

    try:
        from flatseek.cli import cmd_decrypt  # noqa: E402
    except ImportError as e:
        print(f"Failed to import flatseek from {src}: {e}", file=sys.stderr)
        return 2

    data_dir = os.path.abspath(args.data_dir)
    if not os.path.isdir(data_dir):
        print(f"Data directory not found: {data_dir}", file=sys.stderr)
        return 2

    if not args.passphrase:
        print("Passphrase required. Use --passphrase PASSPHRASE", file=sys.stderr)
        return 1

    profiler = cProfile.Profile()
    t0 = time.monotonic()
    profiler.enable()
    try:
        cmd_decrypt(argparse.Namespace(
            data_dir=data_dir,
            passphrase=args.passphrase,
        ))
    finally:
        profiler.disable()
        elapsed = time.monotonic() - t0

    _print_section("decrypt summary")
    print(f" wall:       {elapsed:.2f}s", file=sys.stderr)

    _print_section(f"top {args.top} hotspots — sorted by tottime")
    s = io.StringIO()
    pstats.Stats(profiler, stream=s).strip_dirs().sort_stats("tottime").print_stats(args.top)
    print(s.getvalue(), file=sys.stderr)

    return 0


# ─── Compress ────────────────────────────────────────────────────────────────

def compress(args: argparse.Namespace) -> int:
    """Profile index compression."""
    src = _resolve_flatseek_src(args.flatseek_src)
    if src:
        sys.path.insert(0, src)

    try:
        from flatseek.cli import cmd_compress  # noqa: E402
    except ImportError as e:
        print(f"Failed to import flatseek from {src}: {e}", file=sys.stderr)
        return 2

    data_dir = os.path.abspath(args.data_dir)
    if not os.path.isdir(data_dir):
        print(f"Data directory not found: {data_dir}", file=sys.stderr)
        return 2

    before_size = 0
    index_dir = os.path.join(data_dir, "index")
    if os.path.isdir(index_dir):
        for root, _, files in os.walk(index_dir):
            for f in files:
                if f.endswith(".bin"):
                    before_size += os.path.getsize(os.path.join(root, f))

    profiler = cProfile.Profile()
    t0 = time.monotonic()
    profiler.enable()
    try:
        cmd_compress(argparse.Namespace(
            data_dir=data_dir,
            level=args.level,
            workers=args.workers,
        ))
    finally:
        profiler.disable()
        elapsed = time.monotonic() - t0

    after_size = 0
    if os.path.isdir(index_dir):
        for root, _, files in os.walk(index_dir):
            for f in files:
                if f.endswith(".bin"):
                    after_size += os.path.getsize(os.path.join(root, f))

    _print_section("compress summary")
    print(f" wall:        {elapsed:.2f}s", file=sys.stderr)
    if before_size > 0:
        ratio = before_size / after_size if after_size > 0 else float('inf')
        saved_mb = (before_size - after_size) / 1e6
        print(f" before:     {before_size/1e6:.1f} MB", file=sys.stderr)
        print(f" after:      {after_size/1e6:.1f} MB", file=sys.stderr)
        print(f" saved:      {saved_mb:.1f} MB  ({ratio:.2f}x)", file=sys.stderr)

    _print_section(f"top {args.top} hotspots — sorted by tottime")
    s = io.StringIO()
    pstats.Stats(profiler, stream=s).strip_dirs().sort_stats("tottime").print_stats(args.top)
    print(s.getvalue(), file=sys.stderr)

    return 0


# ─── Delete ─────────────────────────────────────────────────────────────────

def delete_bench(args: argparse.Namespace) -> int:
    """Benchmark index deletion."""
    src = _resolve_flatseek_src(args.flatseek_src)
    if src:
        sys.path.insert(0, src)

    try:
        from flatseek.cli import cmd_delete  # noqa: E402
    except ImportError as e:
        print(f"Failed to import flatseek from {src}: {e}", file=sys.stderr)
        return 2

    # Copy index to temp location for benchmarking
    data_dir = os.path.abspath(args.data_dir)
    if not os.path.isdir(data_dir):
        print(f"Data directory not found: {data_dir}", file=sys.stderr)
        return 2

    import glob
    orig_cwd = os.getcwd()
    temp_dir = tempfile.mkdtemp(prefix="flatperf_delete_")
    try:
        # Copy index structure
        for item in os.listdir(data_dir):
            src_path = os.path.join(data_dir, item)
            dst_path = os.path.join(temp_dir, item)
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)

        print(f"data:     {temp_dir}", file=sys.stderr)
        print(f"runs:     {args.runs}", file=sys.stderr)
        print(file=sys.stderr)

        walls = []
        for i in range(args.runs):
            # Re-copy for each run
            run_dir = tempfile.mkdtemp(prefix=f"flatperf_deleterun_{i}_")
            for item in os.listdir(data_dir):
                src_path = os.path.join(data_dir, item)
                dst_path = os.path.join(run_dir, item)
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path)
                else:
                    shutil.copy2(src_path, dst_path)

            t0 = time.monotonic()
            cmd_delete(argparse.Namespace(
                data_dir=run_dir,
                yes=True,
                workers=args.workers,
            ))
            elapsed = time.monotonic() - t0
            walls.append(elapsed)
            print(f"  run {i+1}/{args.runs}: {_fmt_duration(elapsed)}", file=sys.stderr)

        print(file=sys.stderr)
        walls.sort()
        w_med = statistics.median(walls)

        print("-" * 76, file=sys.stderr)
        header = f"{'operation':<20} {'runs':<6} {'min':<10} {'median':<10} {'max':<10}"
        print(header, file=sys.stderr)
        print("-" * 76, file=sys.stderr)
        print(f"{'delete':<20} {args.runs:<6} {_fmt_duration(walls[0]):<10} {_fmt_duration(w_med):<10} {_fmt_duration(walls[-1]):<10}",
              file=sys.stderr)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
        os.chdir(orig_cwd)

    return 0