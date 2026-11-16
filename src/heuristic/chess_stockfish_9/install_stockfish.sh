#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="${ROOT_DIR}/.runtime"
VENDOR_DIR="${ROOT_DIR}/vendor"
ARCHIVE_URL="https://github.com/official-stockfish/Stockfish/archive/refs/tags/sf_9.tar.gz"
ARCHIVE_PATH="${RUNTIME_DIR}/stockfish-sf_9.tar.gz"
SRC_DIR="${RUNTIME_DIR}/Stockfish-sf_9"
DEST_DIR="${VENDOR_DIR}/stockfish"

mkdir -p "${RUNTIME_DIR}" "${VENDOR_DIR}"
curl -L "${ARCHIVE_URL}" -o "${ARCHIVE_PATH}"
rm -rf "${SRC_DIR}" "${DEST_DIR}"
tar -xzf "${ARCHIVE_PATH}" -C "${RUNTIME_DIR}"

pushd "${SRC_DIR}/src" >/dev/null
make clean || true
make build ARCH=x86-64-modern COMP=gcc -j"$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 1)"
popd >/dev/null

mkdir -p "${DEST_DIR}"
cp -R "${SRC_DIR}/." "${DEST_DIR}/"
chmod +x "${DEST_DIR}/src/stockfish"

