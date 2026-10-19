#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="${ROOT_DIR}/.runtime"
VENDOR_DIR="${ROOT_DIR}/vendor"
DEST_DIR="${VENDOR_DIR}/stockfish"
STOCKFISH_REF="${STOCKFISH_3_REF:-sf_3}"
SAFE_REF="${STOCKFISH_REF//\//_}"
ARCHIVE_PATH="${RUNTIME_DIR}/stockfish-${SAFE_REF}.tar.gz"

if [[ "${STOCKFISH_REF}" =~ ^[0-9a-fA-F]{40}$ ]]; then
  ARCHIVE_URL="https://github.com/official-stockfish/Stockfish/archive/${STOCKFISH_REF}.tar.gz"
  SRC_DIR="${RUNTIME_DIR}/Stockfish-${STOCKFISH_REF}"
else
  ARCHIVE_URL="https://github.com/official-stockfish/Stockfish/archive/refs/tags/${STOCKFISH_REF}.tar.gz"
  SRC_DIR="${RUNTIME_DIR}/Stockfish-${STOCKFISH_REF}"
fi

mkdir -p "${RUNTIME_DIR}" "${VENDOR_DIR}"
curl -L "${ARCHIVE_URL}" -o "${ARCHIVE_PATH}"
rm -rf "${SRC_DIR}" "${DEST_DIR}"
tar -xzf "${ARCHIVE_PATH}" -C "${RUNTIME_DIR}"

NPROC="$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 1)"

pushd "${SRC_DIR}/src" >/dev/null
make clean || true
if make build ARCH=x86-64-modern COMP=gcc -j"${NPROC}"; then
  :
elif make build ARCH=x86-64 COMP=gcc -j"${NPROC}"; then
  :
elif make profile-build ARCH=x86-64-modern COMP=gcc -j"${NPROC}"; then
  :
elif make profile-build ARCH=x86-64 COMP=gcc -j"${NPROC}"; then
  :
elif make -j"${NPROC}"; then
  :
else
  echo "Failed to build Stockfish ref ${STOCKFISH_REF}" >&2
  exit 1
fi
popd >/dev/null

mkdir -p "${DEST_DIR}"
cp -R "${SRC_DIR}/." "${DEST_DIR}/"
if [[ -f "${DEST_DIR}/src/stockfish" ]]; then
  chmod +x "${DEST_DIR}/src/stockfish"
elif [[ -f "${DEST_DIR}/stockfish" ]]; then
  chmod +x "${DEST_DIR}/stockfish"
else
  echo "Built Stockfish binary not found under ${DEST_DIR}" >&2
  exit 1
fi
