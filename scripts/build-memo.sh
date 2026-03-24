#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$ROOT_DIR/build"

cd "$ROOT_DIR/memo"
latexmk -r "$ROOT_DIR/latexmkrc" memo.tex
