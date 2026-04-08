#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
#  run.sh  –  DSPy Prompt Evolution Demo
#
#  Uses the Ollama binary installed locally by install_ollama.sh.
#  On macOS this automatically uses the Apple Silicon GPU (Metal).
#  On Linux it uses the GPU if the Ollama binary was built with
#  GPU support and the drivers are present.
#
#  Usage:
#    ./run.sh                       # default model: llama3.2
#    OLLAMA_MODEL=mistral ./run.sh  # custom model
# ─────────────────────────────────────────────────────────────

set -euo pipefail

# ── Config ────────────────────────────────────────────────────
OLLAMA_MODEL="${OLLAMA_MODEL:-llama3.2}"
OLLAMA_PORT="11434"
OLLAMA_BASE="http://localhost:${OLLAMA_PORT}"
MAX_WAIT_SECS=30
VENV_DIR=".venv"

# Local Ollama binary + model storage (installed by install_ollama.sh)
LOCAL_OLLAMA=".ollama/bin/ollama"
export OLLAMA_MODELS=".ollama/models"   # keep models local to this dir
export OLLAMA_HOST="127.0.0.1:${OLLAMA_PORT}"

# ── Colours ───────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}[run.sh]${RESET} $*"; }
success() { echo -e "${GREEN}[run.sh]${RESET} $*"; }
warn()    { echo -e "${YELLOW}[run.sh]${RESET} $*"; }
error()   { echo -e "${RED}[run.sh] ERROR:${RESET} $*" >&2; }

# ── Cleanup ───────────────────────────────────────────────────
OLLAMA_PID=""
cleanup() {
  echo ""
  if [[ -n "${OLLAMA_PID}" ]]; then
    info "Stopping Ollama server (PID ${OLLAMA_PID})…"
    kill "${OLLAMA_PID}" 2>/dev/null && wait "${OLLAMA_PID}" 2>/dev/null || true
    success "Ollama stopped. Bye!"
  fi
}
trap cleanup EXIT INT TERM

# ── Preflight checks ──────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  error "python3 not found in PATH."
  exit 1
fi

# ── Resolve Ollama binary ─────────────────────────────────────
if [[ -x "${LOCAL_OLLAMA}" ]]; then
  OLLAMA="${LOCAL_OLLAMA}"
  info "Using local Ollama: ${OLLAMA}"
elif command -v ollama &>/dev/null; then
  OLLAMA="ollama"
  warn "Local .ollama/bin/ollama not found — using system Ollama."
  warn "Run ./install_ollama.sh to install a local copy."
else
  error "Ollama not found. Run:  ./install_ollama.sh"
  exit 1
fi

OLLAMA_VERSION=$("${OLLAMA}" --version 2>/dev/null || echo "unknown")
OS_TYPE="$(uname -s)"

echo ""
echo -e "${BOLD}┌────────────────────────────────────────────────────────────┐${RESET}"
echo -e "${BOLD}│  Ollama: ${OLLAMA_VERSION}${RESET}"
if [[ "${OS_TYPE}" == "Darwin" ]]; then
echo -e "${BOLD}│  GPU:    Apple Silicon Metal (automatic on macOS) ✅       │${RESET}"
else
echo -e "${BOLD}│  GPU:    CUDA/ROCm if drivers present                      │${RESET}"
fi
echo -e "${BOLD}│  Models: ${OLLAMA_MODELS}                              │${RESET}"
echo -e "${BOLD}└────────────────────────────────────────────────────────────┘${RESET}"
echo ""

# ── Start Ollama serve ────────────────────────────────────────
if curl -sf "${OLLAMA_BASE}/api/tags" >/dev/null 2>&1; then
  info "Ollama is already running at ${OLLAMA_BASE}."
else
  info "Starting Ollama server…"
  OLLAMA_MODELS="${OLLAMA_MODELS}" OLLAMA_HOST="${OLLAMA_HOST}" \
    "${OLLAMA}" serve >/dev/null 2>&1 &
  OLLAMA_PID=$!

  # Wait for the API to be ready
  info "Waiting for Ollama API to be ready…"
  elapsed=0
  until curl -sf "${OLLAMA_BASE}/api/tags" >/dev/null 2>&1; do
    if [[ $elapsed -ge $MAX_WAIT_SECS ]]; then
      error "Ollama did not become ready within ${MAX_WAIT_SECS}s."
      exit 1
    fi
    sleep 1; elapsed=$((elapsed + 1)); echo -n "."
  done
  echo ""
  success "Ollama API ready after ${elapsed}s."
fi

# ── Pull model ────────────────────────────────────────────────
info "Pulling model '${OLLAMA_MODEL}' (cached after first run)…"
OLLAMA_MODELS="${OLLAMA_MODELS}" "${OLLAMA}" pull "${OLLAMA_MODEL}"
success "Model '${OLLAMA_MODEL}' is ready."

# ── Virtual environment ───────────────────────────────────────
if [[ ! -d "${VENV_DIR}" ]]; then
  info "Creating virtual environment in '${VENV_DIR}'…"
  python3 -m venv "${VENV_DIR}"
  success "Virtual environment created."
else
  info "Reusing existing virtual environment '${VENV_DIR}'."
fi

PYTHON="${VENV_DIR}/bin/python"
PIP="${VENV_DIR}/bin/pip"

info "Installing Python dependencies…"
"${PIP}" install -q -r requirements.txt
success "Dependencies installed."

# ── Run the example ───────────────────────────────────────────
echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${BOLD}  DSPy Prompt Evolution Demo  |  model: ${OLLAMA_MODEL}${RESET}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""

OLLAMA_MODEL="${OLLAMA_MODEL}" OLLAMA_BASE_URL="${OLLAMA_BASE}" \
  "${PYTHON}" prompt_evolution.py

# cleanup() stops Ollama automatically on exit
