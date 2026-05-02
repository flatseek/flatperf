# flatperf

<div align="center">

![FlatSeek Logo](https://raw.githubusercontent.com/flatseek/flatbench/main/public/logo.svg)
[![PyPI version](https://img.shields.io/pypi/v/flatperf.svg)](https://pypi.org/project/flatperf/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Test](https://github.com/flatseek/flatperf/actions/workflows/test.yml/badge.svg)](https://github.com/flatseek/flatperf/actions/workflows/test.yml)

**Profiling toolkit for the Flatseek build pipeline.**

</div>

---

## Installation

### PyPI

```bash
pip install flatperf
```

Requires Python 3.10+. Dependencies (`flatseek`, `flatbench`) are installed automatically.

### Development

```bash
git clone https://github.com/flatseek/flatperf.git
cd flatperf
pip install -e .
```

---

## CLI Commands

### `flatperf generate`

Generate test CSV data for profiling.

```bash
flatperf generate --schema article --rows 1000 --output /tmp/test.csv
flatperf generate --schema transactions --rows 100000 --output /tmp/trans.csv
```

| Schema | Fields |
|--------|--------|
| `article` | id, title, content, author, category, published_at, views, status |
| `users` | id, name, email, country, created_at, age, is_active |
| `transactions` | id, user_id, amount, currency, merchant, location, created_at, status |

| Flag | Default | Description |
|---|---|---|
| `--schema` | `article` | Data schema to generate |
| `--rows` | `1000` | Number of rows to generate |
| `--output` | (required) | Output CSV file path |

---

### `flatperf profile`

Profile a single Flatseek build.

```bash
flatperf profile /tmp/data.csv --rows 100000

# Save profile for snakeviz
flatperf profile /tmp/data.csv --top 30 --out /tmp/build.prof
snakeviz /tmp/build.prof
```

**Sample Output:**

```
input:    /tmp/article_100k.csv
rows:     100,000
workers:  1
output:   /var/folders/c_/.../flatprofile_idx_abc123

══════════════════════════════════════════════════════════════════════════════
 wall summary
══════════════════════════════════════════════════════════════════════════════
 wall:        93.14s
 docs:        100,000
 throughput:  1,074 docs/s

══════════════════════════════════════════════════════════════════════════════
 top 25 hotspots — sorted by tottime
══════════════════════════════════════════════════════════════════════════════
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
   387094   28.534    0.000   28.534    0.000 {method 'acquire' of '_thread.lock' objects}
    900000   25.236    0.000   43.227    0.000 builder.py:875(_index_value)
  ...
```

| Flag | Default | Description |
|---|---|---|
| `csv` | (required) | CSV / JSON file or directory to index |
| `-w, --workers N` | `1` | Number of parallel build workers |
| `-r, --rows N` | (unbounded) | Profile only the first N rows |
| `-n, --top N` | `25` | Hotspots to show in each ranking |
| `--out PATH` | (none) | Write a binary `.prof` file |
| `--keep-output` | off | Keep the temporary index after profiling |
| `--flatseek-src DIR` | auto | Path to flatseek source |

---

### `flatperf compare`

A/B benchmark a Flatseek build, repeated N times.

```bash
flatperf compare ./data/big.csv --rows 100000 --runs 3 --tag "baseline"
flatperf compare ./data/big.csv --rows 100000 --runs 3 --tag "after-cache"
```

**Sample Output:**

```
input:   /tmp/article_100k.csv
rows:    100,000
workers: 1
runs:    3

  run 1/3:    93.14s  (1,074 docs/s)
  run 2/3:    91.82s  (1,089 docs/s)
  run 3/3:    94.01s  (1,064 docs/s)

────────────────────────────────────────────────────────────────────────────
tag                      runs   min        median     max        docs/s (med)
────────────────────────────────────────────────────────────────────────────
baseline                 3      91.82s     93.14s     94.01s          1074
```

| Flag | Default | Description |
|---|---|---|
| `csv` | (required) | CSV / JSON file or directory |
| `-n, --runs N` | `3` | Number of repeated builds |
| `-w, --workers N` | `1` | Parallel workers per run |
| `-r, --rows N` | (unbounded) | Trim input to first N rows |
| `--tag NAME` | `build` | Label for the result row |
| `--flatseek-src DIR` | auto | Path to flatseek source |

---

### `flatperf search`

Profile a single search query.

```bash
flatperf search ./data "program:raydium AND signer:*7xMg*"
flatperf search ./data "ERROR" --top 30 --out /tmp/search.prof
```

**Sample Output:**

```
══════════════════════════════════════════════════════════════════════════════
 search result
══════════════════════════════════════════════════════════════════════════════
 query:      program:raydium
 total:      12,456 matches
 returned:   20 docs
 wall:       0.0034s
 qps:        294.1 queries/s

══════════════════════════════════════════════════════════════════════════════
 top 25 hotspots — sorted by tottime
══════════════════════════════════════════════════════════════════════════════
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
      542    0.001    0.000    0.001    0.000 {method 'acquire' of '_thread.lock' objects}
       42    0.000    0.000    0.003    0.000 query_engine.py:234(_search_trigrams)
  ...
```

| Flag | Default | Description |
|---|---|---|
| `data_dir` | (required) | Index directory |
| `query` | (required) | Search query string |
| `-n, --top N` | `25` | Hotspots to show |
| `-p, --page-size N` | `20` | Number of results per page |
| `--flatseek-src DIR` | auto | Path to flatseek source |

---

### `flatperf bench-search`

Benchmark search queries, repeated N times to get latency percentiles.

```bash
flatperf bench-search ./data "program:raydium" --runs 100
flatperf bench-search ./data "status:ERROR" --runs 50 --tag "error-queries"
```

**Sample Output:**

```
query:    program:raydium
data:     ./data
runs:     100

  run 1/100: 3.45ms  (12,456 matches)
  run 2/100: 3.21ms  (12,456 matches)
  ...

────────────────────────────────────────────────────────────────────────────
query                         runs   min(ms)    median     p95       p99       qps
────────────────────────────────────────────────────────────────────────────
program:raydium               100    2.98       3.34       4.12      5.87      299.4
```

| Flag | Default | Description |
|---|---|---|
| `data_dir` | (required) | Index directory |
| `query` | (required) | Search query string |
| `-n, --runs N` | `10` | Number of repeated queries |
| `-p, --page-size N` | `20` | Number of results per page |
| `--tag NAME` | query | Label for the result row |
| `--flatseek-src DIR` | auto | Path to flatseek source |

---

### `flatperf join`

Profile a single join query.

```bash
flatperf join ./data "dataset:logs" "service:api" --on trace_id
```

**Sample Output:**

```
══════════════════════════════════════════════════════════════════════════════
 join result
══════════════════════════════════════════════════════════════════════════════
 query_a:    dataset:logs
 query_b:    service:api
 join_on:    trace_id
 total:      12,450 pairs
 returned:   20 pairs
 wall:       0.0089s
 qps:        112.4 joins/s
```

| Flag | Default | Description |
|---|---|---|
| `data_dir` | (required) | Index directory |
| `query_a` | (required) | First query |
| `query_b` | (required) | Second query |
| `--on` | (required) | Shared field to join on |
| `-n, --top N` | `25` | Hotspots to show |
| `-p, --page-size N` | `20` | Number of results per page |
| `--flatseek-src DIR` | auto | Path to flatseek source |

---

### `flatperf bench-join`

Benchmark join queries, repeated N times.

```bash
flatperf bench-join ./data "dataset:logs" "service:api" --on trace_id --runs 50
```

**Sample Output:**

```
query_a:   dataset:logs
query_b:   service:api
join_on:   trace_id
data:      ./data
runs:      50

────────────────────────────────────────────────────────────────────────────
query                             runs   min(ms)    median     p95       p99       qps
────────────────────────────────────────────────────────────────────────────
dataset:logs+service:api           50    7.12      8.94      14.23     22.10     111.9
```

| Flag | Default | Description |
|---|---|---|
| `data_dir` | (required) | Index directory |
| `query_a` | (required) | First query |
| `query_b` | (required) | Second query |
| `--on` | (required) | Shared field to join on |
| `-n, --runs N` | `10` | Number of repeated runs |
| `-p, --page-size N` | `20` | Number of results per page |
| `--tag NAME` | auto | Label for the result row |
| `--flatseek-src DIR` | auto | Path to flatseek source |

---

### `flatperf aggregate`

Profile a single aggregation query (terms, stats, cardinality, histogram).

```bash
# Terms aggregation
flatperf aggregate ./data --aggs '{"terms":{"field":"category","size":10}}'

# Stats on numeric field
flatperf aggregate ./data --aggs '{"stats":{"field":"amount"}}'

# With query filter
flatperf aggregate ./data -q "status:ACTIVE" --aggs '{"terms":{"field":"author","size":20}}'

# Cardinality - unique users
flatperf aggregate ./data --aggs '{"cardinality":{"field":"user_id"}}'
```

**Sample Output:**

```
══════════════════════════════════════════════════════════════════════════════
 aggregate result
══════════════════════════════════════════════════════════════════════════════
 query:      status:ACTIVE
 aggs:       {"terms":{"field":"category","size":10}}
 wall:       0.0089s
 hits:       45,230

 terms aggregation (category):
   tech      12,450 docs
   news       9,820 docs
   sports     7,230 docs
```

| Supported Types | Description |
|---|---|
| `terms` | Bucket aggregation — count docs per field value |
| `stats` | Min, max, sum, avg, count on numeric field |
| `cardinality` | Count unique values (approximate) |
| `histogram` | Bucket by numeric interval |

| Flag | Default | Description |
|---|---|---|
| `data_dir` | (required) | Index directory |
| `-q, --query` | (none) | Lucene query to filter docs |
| `--aggs` | (none) | JSON aggregation config |
| `-s, --size N` | `10` | Max buckets for terms aggregation |
| `-n, --top N` | `25` | Hotspots to show |
| `--flatseek-src DIR` | auto | Path to flatseek source |

---

### `flatperf bench-aggregate`

Benchmark aggregation queries, repeated N times.

```bash
flatperf bench-aggregate ./data --aggs '{"terms":{"field":"category","size":10}}' --runs 50
flatperf bench-aggregate ./data -q "type:article" --aggs '{"stats":{"field":"views"}}' --runs 100 --tag "article-stats"
```

**Sample Output:**

```
query:    {"terms":{"field":"category","size":10}}
data:     ./data
filter:   status:ACTIVE
runs:     50

────────────────────────────────────────────────────────────────────────────
aggregation                   runs   min(ms)   median    p95       p99       qps
────────────────────────────────────────────────────────────────────────────
terms(category)                 50    6.12      8.34     12.45     18.23     119.8
```

| Flag | Default | Description |
|---|---|---|
| `data_dir` | (required) | Index directory |
| `-q, --query` | (none) | Lucene query to filter docs |
| `--aggs` | (none) | JSON aggregation config |
| `-s, --size N` | `10` | Max buckets |
| `-n, --runs N` | `10` | Number of repeated runs |
| `--tag NAME` | aggregate | Label for the result row |
| `--flatseek-src DIR` | auto | Path to flatseek source |

---

### `flatperf encrypt`

Profile index encryption.

```bash
flatperf encrypt ./data --passphrase "mysecretpass" --top 30
flatperf encrypt ./data --passphrase "mysecretpass" --workers 8
```

**Sample Output:**

```
══════════════════════════════════════════════════════════════════════════════
 encrypt summary
══════════════════════════════════════════════════════════════════════════════
 wall:       45.23s

══════════════════════════════════════════════════════════════════════════════
 top 25 hotspots — sorted by tottime
══════════════════════════════════════════════════════════════════════════════
  524288    32.45    0.000   32.45    0.000 query_engine.py:156(encrypt_bytes)
   65600     8.12    0.000   12.34    0.000 builder.py:452(_encrypt_file)
  ...
```

| Flag | Default | Description |
|---|---|---|
| `data_dir` | (required) | Index directory |
| `--passphrase` | (required) | Encryption passphrase |
| `-w, --workers N` | auto | Parallel workers |
| `-n, --top N` | `25` | Hotspots to show |
| `--flatseek-src DIR` | auto | Path to flatseek source |

---

### `flatperf decrypt`

Profile index decryption.

```bash
flatperf decrypt ./data --passphrase "mysecretpass"
```

| Flag | Default | Description |
|---|---|---|
| `data_dir` | (required) | Index directory |
| `--passphrase` | (required) | Decryption passphrase |
| `-n, --top N` | `25` | Hotspots to show |
| `--flatseek-src DIR` | auto | Path to flatseek source |

---

### `flatperf compress`

Profile index compression.

```bash
flatperf compress ./data
flatperf compress ./data --level 9
flatperf compress ./data --workers 8
```

**Sample Output:**

```
══════════════════════════════════════════════════════════════════════════════
 compress summary
══════════════════════════════════════════════════════════════════════════════
 wall:        28.45s
 before:     256.3 MB
 after:      89.7 MB
 saved:      166.6 MB  (2.86x)

══════════════════════════════════════════════════════════════════════════════
 top 25 hotspots — sorted by tottime
══════════════════════════════════════════════════════════════════════════════
  65536     18.23    0.000   18.23    0.000 {built-in method zlib.compress}
      1      5.12    0.000   23.45    0.000 builder.py:892(cmd_compress)
  ...
```

| Flag | Default | Description |
|---|---|---|
| `data_dir` | (required) | Index directory |
| `-l, --level N` | `6` | Compression level 1-9 |
| `-w, --workers N` | auto | Parallel workers |
| `-n, --top N` | `25` | Hotspots to show |
| `--flatseek-src DIR` | auto | Path to flatseek source |

---

### `flatperf delete`

Benchmark index deletion.

```bash
flatperf delete ./data --runs 3
flatperf delete ./data --workers 16
```

**Sample Output:**

```
data:     /tmp/flatperf_deleterun_0_abc123
runs:     3

  run 1/3:    12.34s
  run 2/3:    11.89s
  run 3/3:    13.21s

────────────────────────────────────────────────────────────────────────────
operation              runs   min        median     max
────────────────────────────────────────────────────────────────────────────
delete                 3      11.89s     12.34s     13.21s
```

| Flag | Default | Description |
|---|---|---|
| `data_dir` | (required) | Index directory to delete |
| `-n, --runs N` | `3` | Number of repeated runs |
| `-w, --workers N` | auto | Parallel workers |
| `--flatseek-src DIR` | auto | Path to flatseek source |

---

## Reading the Output

cProfile output shows two rankings:

- **`tottime`** — seconds spent inside the function itself (excluding callees). Optimize the top of this list to win wall time.

- **`cumtime`** — seconds spent inside the function plus everything it called. Use it to find which code subtree dominates a long-running call.

A function with high `cumtime` but low `tottime` is just a wrapper — its expensive callee is the actual cost. Look further down.

## Recipe — Find the Next Bottleneck

```bash
# 1. Generate test data and establish a baseline
flatperf generate --schema article --rows 100000 --output /tmp/data.csv
flatperf compare /tmp/data.csv --rows 100000 --runs 3 --tag "baseline"

# 2. Profile to see where time goes
flatperf profile /tmp/data.csv --rows 100000 --top 30 \
    --out /tmp/build.prof
snakeviz /tmp/build.prof

# 3. Pick the highest-tottime function and inspect it. Edit. Test.

# 4. Confirm the gain
flatperf compare /tmp/data.csv --rows 100000 --runs 3 --tag "after-X"

# 5. For search: profile individual queries
flatperf search /tmp/data "common_query" --top 30

# 6. Benchmark search latency
flatperf bench-search /tmp/data "common_query" --runs 100
```

Repeat until the top-of-list is "intrinsic work" (per-cell tokenize, per-term encode) — not setup, parsing, or IO that can be cached.

## Development

```bash
pip install -e .
pip install pytest
pytest
```

## License

Apache 2.0