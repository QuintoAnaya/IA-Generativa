#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
#  install_ollama.sh  –  Install Ollama for this project
#
#  macOS  → installs via Homebrew (gives a properly signed CLI binary)
#  Linux  → downloads the standalone binary into .ollama/bin/
#
#  Models are stored in .ollama/models/ (local to this directory).
#
#  Usage:
#    chmod +x install_ollama.sh && ./install_ollama.sh
# ─────────────────────────────────────────────────────────────

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
info()    { echo -e "${CYAN}[install]${RESET} $*"; }
success() { echo -e "${GREEN}[install]${RESET} $*"; }
warn()    { echo -e "${YELLOW}[install]${RESET} $*"; }
error()   { echo -e "${RED}[install] ERROR:${RESET} $*" >&2; exit 1; }

MODELS_DIR=".ollama/models"
BIN_DIR=".ollama/bin"
mkdir -p "${MODELS_DIR}" "${BIN_DIR}"

OS="$(uname -s)"
ARCH="$(uname -m)"
info "Platform: ${OS} / ${ARCH}"

# ─────────────────────────────────────────────────────────────
#  macOS – use Homebrew
#  The Ollama.app binary is bound to its app bundle by its code signature.
#  The Homebrew formula ships a self-contained, properly signed CLI binary.
# ─────────────────────────────────────────────────────────────
if [[ "${OS}" == "Darwin" ]]; then
  if ! command -v brew &>/dev/null; then
    error "Homebrew is not installed.\n  Install it from https://brew.sh and re-run this script."
  fi

  if brew list ollama &>/dev/null 2>&1; then
    VERSION=$(ollama --version 2>/dev/null || echo "unknown")
    warn "Ollama is already installed via Homebrew (${VERSION})."
  else
    info "Installing Ollama via Homebrew…"
    brew install ollama
    success "Ollama installed via Homebrew."
  fi

  OLLAMA_PATH="$(brew --prefix ollama)/bin/ollama"
  # Symlink into .ollama/bin so run.sh always finds it at the same path
  ln -sf "${OLLAMA_PATH}" "${BIN_DIR}/ollama"
  VERSION=$(${OLLAMA_PATH} --version 2>/dev/null || echo "unknown")
  success "Symlinked: ${BIN_DIR}/ollama → ${OLLAMA_PATH} (${VERSION})"

# ─────────────────────────────────────────────────────────────
#  Linux – download standalone binary
# ─────────────────────────────────────────────────────────────
elif [[ "${OS}" == "Linux" ]]; then
  LOCAL_BIN="${BIN_DIR}/ollama"

  if [[ -x "${LOCAL_BIN}" ]]; then
    VERSION=$("${LOCAL_BIN}" --version 2>/dev/null || echo "unknown")
    warn "Ollama already installed at ${LOCAL_BIN} (${VERSION}). Delete it to reinstall."
    exit 0
  fi

  case "${ARCH}" in
    x86_64)  ASSET="ollama-linux-amd64.tgz" ;;
    aarch64) ASSET="ollama-linux-arm64.tgz" ;;
    *)        error "Unsupported Linux architecture: ${ARCH}" ;;
  esac

  RELEASES_URL="https://github.com/ollama/ollama/releases/latest/download"
  TMP_DIR="$(mktemp -d)"
  trap 'rm -rf "${TMP_DIR}"' EXIT

  TGZ="${TMP_DIR}/${ASSET}"
  info "Downloading Ollama for Linux (${ARCH})…"
  curl -fL --progress-bar "${RELEASES_URL}/${ASSET}" -o "${TGZ}"
  tar -xzf "${TGZ}" -C "${TMP_DIR}"
  cp "${TMP_DIR}/bin/ollama" "${LOCAL_BIN}"
  chmod +x "${LOCAL_BIN}"
  VERSION=$("${LOCAL_BIN}" --version 2>/dev/null || echo "unknown")
  success "Ollama installed: ${LOCAL_BIN} (${VERSION})"

else
  error "Unsupported OS: ${OS}. Only macOS and Linux are supported."
fi

echo ""
success "Models will be stored in: ${MODELS_DIR}"
echo -e "  Run the demo:  ${BOLD}./run.sh${RESET}"
echo ""
