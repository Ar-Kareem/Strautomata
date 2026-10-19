#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RULES_DIR="${SCRIPT_DIR}/offline_mirror/rules"
MATCH_PY="${SCRIPT_DIR}/stanford_gamemaster_match.py"
RANDOM_BOT="${SCRIPT_DIR}/stanford_gamemaster_random_bot.py"
TIME_LIMIT_SECONDS="${TIME_LIMIT_SECONDS:-5}"

if [[ ! -d "${RULES_DIR}" ]]; then
  echo "Missing rules directory: ${RULES_DIR}" >&2
  exit 1
fi

if [[ ! -f "${MATCH_PY}" ]]; then
  echo "Missing match runner: ${MATCH_PY}" >&2
  exit 1
fi

if [[ ! -f "${RANDOM_BOT}" ]]; then
  echo "Missing random bot: ${RANDOM_BOT}" >&2
  exit 1
fi

printf "%-24s  %-8s  %10s\n" "game" "status" "seconds"

for rules_path in "${RULES_DIR}"/*.hrf; do
  game="$(basename "${rules_path}" .hrf)"
  start_ns="$(date +%s%N)"

  timeout -k 1s "${TIME_LIMIT_SECONDS}s" \
    python "${MATCH_PY}" \
      --rules "${rules_path}" \
      --bot-a "${RANDOM_BOT}" \
      --bot-b "${RANDOM_BOT}" \
      >/dev/null 2>&1
  status_code="$?"

  end_ns="$(date +%s%N)"
  elapsed_ms="$(((end_ns - start_ns) / 1000000))"
  elapsed_text="$(python - <<PY
ms = ${elapsed_ms}
print(f"{ms / 1000.0:.3f}")
PY
)"

  if [[ "${status_code}" -eq 0 ]]; then
    status="ok"
  elif [[ "${status_code}" -eq 124 || "${status_code}" -eq 137 ]]; then
    status="timeout"
  else
    status="error:${status_code}"
  fi

  printf "%-24s  %-8s  %10s\n" "${game}" "${status}" "${elapsed_text}"
done
