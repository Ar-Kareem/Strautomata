#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="${ROOT_DIR}/.runtime"
VENDOR_DIR="${ROOT_DIR}/vendor"
SRC_DIR="${RUNTIME_DIR}/lc0-v0.20.2"
DEST_DIR="${VENDOR_DIR}/lc0"
NETWORK_DIR="${DEST_DIR}/networks"
LIB_DIR="${DEST_DIR}/lib"
RUNTIME_BIN_DIR="${RUNTIME_DIR}/bin"
REPO_ENV_PYTHON="${ROOT_DIR}/../../../env3.12/bin/python"

REPO_URL="https://github.com/LeelaChessZero/lc0.git"
TAG="v0.20.2"
NETWORK_URL="https://storage.lczero.org/files/networks/00af53b081e80147172e6f281c01daf5ca19ada173321438914c730370aa4267"
NETWORK_FILENAME="weights.pb.gz"
EXTRA_CXXFLAGS="-include condition_variable -include cstdint"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

setup_python_tool_shim() {
  local cmd_name="$1"
  local module_name="$2"
  if command -v "${cmd_name}" >/dev/null 2>&1; then
    return 0
  fi
  if [ ! -x "${REPO_ENV_PYTHON}" ]; then
    return 1
  fi
  if ! "${REPO_ENV_PYTHON}" -m "${module_name}" --help >/dev/null 2>&1; then
    return 1
  fi

  mkdir -p "${RUNTIME_BIN_DIR}"
  cat > "${RUNTIME_BIN_DIR}/${cmd_name}" <<EOF
#!/usr/bin/env bash
exec "${REPO_ENV_PYTHON}" -m "${module_name}" "\$@"
EOF
  chmod +x "${RUNTIME_BIN_DIR}/${cmd_name}"
  export PATH="${RUNTIME_BIN_DIR}:${PATH}"
  return 0
}

require_build_tool() {
  local cmd_name="$1"
  local module_name="$2"
  if setup_python_tool_shim "${cmd_name}" "${module_name}"; then
    return 0
  fi
  echo "Missing required command: ${cmd_name}" >&2
  echo "lc0's upstream build.sh invokes ${cmd_name} directly." >&2
  if [ -x "${REPO_ENV_PYTHON}" ]; then
    echo "Install it system-wide or into env3.12, e.g.:" >&2
    echo "  ${REPO_ENV_PYTHON} -m pip install meson ninja" >&2
  fi
  exit 1
}

require_cmd git
require_cmd curl
require_cmd pkg-config
require_build_tool meson mesonbuild.mesonmain
require_build_tool ninja ninja

if ! pkg-config --exists openblas; then
  echo "OpenBLAS development files are required (pkg-config openblas not found)." >&2
  echo "Install libopenblas-dev or equivalent and rerun this script." >&2
  exit 1
fi

mkdir -p "${RUNTIME_DIR}" "${VENDOR_DIR}" "${NETWORK_DIR}"

if [ -d "${SRC_DIR}/.git" ]; then
  git -C "${SRC_DIR}" fetch --force --tags origin
  git -C "${SRC_DIR}" checkout --force "${TAG}"
  git -C "${SRC_DIR}" submodule update --init --recursive
else
  rm -rf "${SRC_DIR}"
  git clone --branch "${TAG}" --depth 1 --recurse-submodules "${REPO_URL}" "${SRC_DIR}"
fi

OPENBLAS_INCLUDE_RAW="$(pkg-config --cflags-only-I openblas || true)"
OPENBLAS_LIBDIR_RAW="$(pkg-config --libs-only-L openblas || true)"

OPENBLAS_INCLUDE_CSV="$(
  printf '%s\n' "${OPENBLAS_INCLUDE_RAW}" \
  | tr ' ' '\n' \
  | sed -n 's/^-I//p' \
  | paste -sd, -
)"
OPENBLAS_LIBDIR_CSV="$(
  printf '%s\n' "${OPENBLAS_LIBDIR_RAW}" \
  | tr ' ' '\n' \
  | sed -n 's/^-L//p' \
  | paste -sd, -
)"

pushd "${SRC_DIR}" >/dev/null
rm -rf build/release

BUILD_ARGS=(
  -Dgtest=false
  -Dblas=true
  -Dopenblas=true
  -Dmkl=false
  -Daccelerate=false
  -Dcudnn=false
  -Dopencl=false
  -Dtensorflow=false
  -Dispc=false
)

if [ -n "${OPENBLAS_INCLUDE_CSV}" ]; then
  BUILD_ARGS+=("-Dopenblas_include=${OPENBLAS_INCLUDE_CSV}")
fi
if [ -n "${OPENBLAS_LIBDIR_CSV}" ]; then
  BUILD_ARGS+=("-Dopenblas_libdirs=${OPENBLAS_LIBDIR_CSV}")
fi

CXXFLAGS_VALUE="${CXXFLAGS:-}"
if [ -n "${CXXFLAGS_VALUE}" ]; then
  CXXFLAGS_VALUE="${CXXFLAGS_VALUE} ${EXTRA_CXXFLAGS}"
else
  CXXFLAGS_VALUE="${EXTRA_CXXFLAGS}"
fi

CXXFLAGS="${CXXFLAGS_VALUE}" ./build.sh release "${BUILD_ARGS[@]}"
popd >/dev/null

mkdir -p "${DEST_DIR}" "${NETWORK_DIR}" "${LIB_DIR}"
cp "${SRC_DIR}/build/release/lc0" "${DEST_DIR}/lc0"
chmod +x "${DEST_DIR}/lc0"
cp "${SRC_DIR}/build/release/subprojects/protobuf-"*/libprotobuf*.so "${LIB_DIR}/"
curl -L "${NETWORK_URL}" -o "${NETWORK_DIR}/${NETWORK_FILENAME}"
