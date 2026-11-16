#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 WORD" >&2
  exit 1
fi

WORD="$1"

find ./ \
  \( \
    -path './analysis/results_tmp/exp_results_somerset_may_1_cluster_code' -o \
    -path './analysis/results_tmp/another_long_dir' \
  \) -prune -o \
  -type d \( \
    -name logs -o \
    -name DELETE -o \
    -name env -o \
    -name env3.12 -o \
    -name results_old -o \
    -name results_current -o \
    -name results_side_experiments -o \
    -name temp -o \
    -name z_arc \
  \) -prune -o \
  -type f -print0 |
xargs -0 grep -Il -- "$WORD"
