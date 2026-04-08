# DSPy Prompt Evolution Demo

A self-contained example showing how [DSPy](https://dspy.ai) automatically
optimizes prompts through **three progressive stages**, making the prompt
evolution visible at each step.

## What it demonstrates

| Stage | Optimizer | What changes |
|-------|-----------|-------------|
| **0** | None (zero-shot) | Baseline — no examples in the prompt |
| **1** | `BootstrapFewShot` | DSPy bootstraps few-shot demos from training traces |
| **2** | `BootstrapFewShotWithRandomSearch` | Best candidate program selected across multiple runs |

**Task:** Classify movie review sentiment as `Positive`, `Negative`, or `Mixed`.

## Prerequisites

| Tool | Version |
|------|---------|
| **Python** | ≥ 3.10 |
| **curl** + **unzip** | for `install_ollama.sh` |

No Docker, no API keys, no system-wide installs required.

## Quick start

```bash
# 1 – Make scripts executable (first time only)
chmod +x install_ollama.sh run.sh

# 2 – Download the Ollama binary into .ollama/bin/
./install_ollama.sh

# 3 – Run the demo (starts Ollama, pulls model, runs DSPy, stops Ollama)
./run.sh
```

To use a different model:

```bash
OLLAMA_MODEL=mistral ./run.sh
```

## GPU support

| Platform | GPU acceleration |
|----------|-----------------|
| macOS (Apple Silicon) | ✅ Metal — automatic, no config needed |
| Linux + NVIDIA | ✅ CUDA — automatic if drivers are installed |
| Linux + AMD | ✅ ROCm — automatic if drivers are installed |

## Project structure

```
DSPy/
├── install_ollama.sh    # Downloads Ollama binary → .ollama/bin/
├── run.sh               # Starts Ollama, runs demo, stops Ollama
├── prompt_evolution.py  # DSPy optimization logic (stages 0 → 1 → 2)
├── requirements.txt     # Python dependencies (dspy, rich)
├── .ollama/
│   ├── bin/ollama       # Created by install_ollama.sh
│   └── models/          # Downloaded models (cached)
└── README.md
```

## How it works

```
./install_ollama.sh
  └── downloads .ollama/bin/ollama  (macOS universal or Linux amd64/arm64)

./run.sh
  ├── starts  .ollama/bin/ollama serve  (Metal / CUDA / CPU)
  ├── pulls   llama3.2 model into .ollama/models/
  ├── creates .venv + installs dspy, rich
  ├── runs    prompt_evolution.py
  └── stops   ollama serve on exit (even on Ctrl-C)
```
