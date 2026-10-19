#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="${ROOT_DIR}/.runtime"
VENDOR_DIR="${ROOT_DIR}/vendor"
ASSET_URL="https://github.com/official-stockfish/Stockfish/releases/download/sf_18/stockfish-ubuntu-x86-64-avx2.tar"
ASSET_PATH="${RUNTIME_DIR}/stockfish-ubuntu-x86-64-avx2.tar"

mkdir -p "${RUNTIME_DIR}" "${VENDOR_DIR}"
curl -L "${ASSET_URL}" -o "${ASSET_PATH}"
rm -rf "${VENDOR_DIR}/stockfish"
tar -xf "${ASSET_PATH}" -C "${VENDOR_DIR}"
chmod +x "${VENDOR_DIR}/stockfish/stockfish-ubuntu-x86-64-avx2"
