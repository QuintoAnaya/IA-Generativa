"""
DSPy Prompt Evolution Example
==============================
Demonstrates how DSPy optimizes prompts through multiple stages:
  Stage 0 → Baseline (zero-shot, no examples)
  Stage 1 → COPRO (optimizes the instruction string directly)
  Stage 2 → BootstrapFewShot (adds auto-generated examples to the optimized instructions)

Task: Classifying movie review sentiment as Positive / Negative / Mixed.

Run via the runner script (recommended – manages the Ollama container):
    ./run.sh

Or directly if Ollama is already running:
    pip install -r requirements.txt
    python prompt_evolution.py
"""

import os

import dspy
import litellm
from rich.console import Console
from rich.panel import Panel

from display import (
    print_cot_examples,
    print_comparison_table,
    print_prompt_diff,
    print_prompt_snapshot,
    print_stage_header,
)

# ─────────────────────────────────────────────
# 1.  Configure the LM  (Ollama – started by run.sh)
# ─────────────────────────────────────────────

OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
OLLAMA_BASE  = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")


def configure_lm() -> dspy.LM:
    """Connect to the Ollama container launched by run.sh."""
    print(f"🦙  Using Ollama model '{OLLAMA_MODEL}' at {OLLAMA_BASE}")
    return dspy.LM(
        f"ollama_chat/{OLLAMA_MODEL}",
        api_base=OLLAMA_BASE,
        max_tokens=256,
    )


# ─────────────────────────────────────────────
# 2.  DSPy Signature & Module
# ─────────────────────────────────────────────

class SentimentSignature(dspy.Signature):
    """Assess the sentiment of the provided text."""

    review: str = dspy.InputField(
        desc="The text to analyze"
    )
    sentiment: str = dspy.OutputField(
        desc="Sentiment (You MUST output exactly one of: Positive, Negative, Mixed)"
    )
    reasoning: str = dspy.OutputField(
        desc="The reasoning behind your assessment"
    )


class SentimentClassifier(dspy.Module):
    def __init__(self):
        super().__init__()
        self.classify = dspy.ChainOfThought(SentimentSignature)

    def forward(self, review: str):
        result = self.classify(review=review)
        # Normalise output
        raw = result.sentiment.strip()
        for label in ("Positive", "Negative", "Mixed"):
            if label.lower() in raw.lower():
                result.sentiment = label
                break
        return result


# ─────────────────────────────────────────────
# 3.  Dataset
# ─────────────────────────────────────────────

EXAMPLES_RAW = [
    # ── Positive ──────────────────────────────────────────────────────────────
    ("An absolute masterpiece. The direction was breathtaking and the acting superb.", "Positive"),
    ("One of the best films I have ever seen. A timeless classic.", "Positive"),
    ("Funny, heartwarming and perfectly paced. An instant favourite.", "Positive"),
    ("Absolutely thrilling from beginning to end. I loved every second.", "Positive"),
    ("A hidden gem – smart, touching, and beautifully acted.", "Positive"),
    ("Funny, sharp, and full of energy. Exactly what cinema needs.", "Positive"),
    ("Pure joy from start to finish. Don't miss it.", "Positive"),
    ("A genuinely moving experience that left me speechless.", "Positive"),
    ("The performances are outstanding across the board.", "Positive"),
    ("Clever, funny, and surprisingly deep. A triumph.", "Positive"),
    ("Every frame is a work of art. Stunning from start to finish.", "Positive"),
    ("I laughed, I cried, and I left the cinema feeling uplifted.", "Positive"),
    ("A rare film that is both intelligent and enormously entertaining.", "Positive"),
    ("Superb storytelling backed by a flawless ensemble cast.", "Positive"),
    ("The screenplay crackles with wit and originality.", "Positive"),
    ("One of those rare films you want to watch again immediately.", "Positive"),
    ("An emotional rollercoaster executed with remarkable precision.", "Positive"),
    ("The director has created something truly unforgettable.", "Positive"),
    ("Beautifully shot, brilliantly acted, and deeply moving.", "Positive"),
    ("A joyful celebration of cinema at its very best.", "Positive"),
    ("Instantly quotable and absolutely hilarious throughout.", "Positive"),
    ("The chemistry between the leads is electric and captivating.", "Positive"),
    ("A bold, ambitious film that absolutely delivers on every promise.", "Positive"),
    ("Gripping from the very first scene to the very last.", "Positive"),
    ("Hands down the best film of the year. A masterclass in filmmaking.", "Positive"),
    ("Charming, witty, and full of heart. A genuine crowd-pleaser.", "Positive"),
    ("The score alone is worth the price of admission.", "Positive"),
    ("Beautifully paced and utterly engrossing throughout.", "Positive"),
    ("A knockout. Intelligent, funny, and emotionally resonant.", "Positive"),
    ("This film sets a new benchmark for its genre.", "Positive"),
    ("I was on the edge of my seat the entire time.", "Positive"),
    ("Warm, wise, and wonderfully performed. A breath of fresh air.", "Positive"),
    ("Exceptional in every single department. A must-see.", "Positive"),
    ("The storytelling is confident, inventive, and deeply satisfying.", "Positive"),
    ("A dazzling spectacle with real emotional depth underneath.", "Positive"),
    ("Every performance is pitch-perfect. An extraordinary ensemble piece.", "Positive"),
    ("Funny and moving in equal measure. A perfect balance.", "Positive"),
    ("The kind of film that restores your faith in cinema.", "Positive"),
    ("Absolutely riveting. I could not take my eyes off the screen.", "Positive"),
    ("A stunning achievement that deserves every award it receives.", "Positive"),

    # ── Negative ──────────────────────────────────────────────────────────────
    ("Boring from start to finish. I nearly fell asleep in the first act.", "Negative"),
    ("Terrible script, wooden performances, a complete waste of two hours.", "Negative"),
    ("The plot made no sense and the ending was infuriating.", "Negative"),
    ("A formulaic cash-grab with zero originality.", "Negative"),
    ("The worst thing I have seen all year – incoherent and dull.", "Negative"),
    ("Loud, brash and irritating. Gave me a headache.", "Negative"),
    ("Painfully slow with characters I couldn't care less about.", "Negative"),
    ("A meandering mess that wastes a talented cast.", "Negative"),
    ("Laughably bad from start to finish. Avoid at all costs.", "Negative"),
    ("The dialogue is cringe-worthy and the pacing is atrocious.", "Negative"),
    ("Two hours of my life I will never get back.", "Negative"),
    ("A shallow, soulless exercise in franchise film-making.", "Negative"),
    ("The special effects cannot disguise how hollow this film truly is.", "Negative"),
    ("Predictable, derivative, and deeply uninspiring.", "Negative"),
    ("The acting is so wooden you could sand a floor with it.", "Negative"),
    ("An insult to the audience's intelligence from the very first minute.", "Negative"),
    ("Poorly written, poorly directed, and poorly executed.", "Negative"),
    ("The story collapses entirely by the second act.", "Negative"),
    ("A spectacular misfire that squanders every ounce of potential.", "Negative"),
    ("One of the most tedious films I have endured in years.", "Negative"),
    ("Derivative, lazy, and utterly forgettable.", "Negative"),
    ("Chaotic and incoherent in equal measure.", "Negative"),
    ("The humour falls flat on every single occasion.", "Negative"),
    ("A bloated and self-indulgent piece of work that never finds its footing.", "Negative"),
    ("Aggressively mediocre with no redeeming qualities whatsoever.", "Negative"),
    ("A joyless exercise in tedium. Avoid.", "Negative"),
    ("The film has absolutely nothing interesting to say.", "Negative"),
    ("Stilted, lifeless, and boring. A real disappointment.", "Negative"),
    ("The twist ending is not clever; it is simply absurd.", "Negative"),
    ("Genuinely unwatchable. One of the worst films in recent memory.", "Negative"),
    ("Every attempt at humour lands with an audible thud.", "Negative"),
    ("Shockingly bad for a film with this budget and this cast.", "Negative"),
    ("Dull, drab, and devoid of any creative spark.", "Negative"),
    ("The screenplay is a cut-and-paste job that brings nothing new.", "Negative"),
    ("So painfully slow it feels twice as long as it actually is.", "Negative"),
    ("Completely charmless and impossible to engage with.", "Negative"),
    ("A bloated, over-long mess that mistakes noise for excitement.", "Negative"),
    ("Exhaustingly bad. I genuinely struggled to sit through it.", "Negative"),
    ("The direction is amateurish and the editing is a disaster.", "Negative"),
    ("Terrible in almost every conceivable way.", "Negative"),

    # ── Mixed ─────────────────────────────────────────────────────────────────
    ("Great special effects but the story was disappointingly thin.", "Mixed"),
    ("Visually stunning but emotionally hollow – style over substance.", "Mixed"),
    ("The lead actor shines, but the supporting cast drags it down considerably.", "Mixed"),
    ("Beautiful cinematography; pity the dialogue was so clunky.", "Mixed"),
    ("Some truly brilliant scenes surrounded by a meandering middle act.", "Mixed"),
    ("A genuinely moving story undercut by cheap CGI.", "Mixed"),
    ("The first half is excellent; the second half loses its way completely.", "Mixed"),
    ("Strong performances cannot save a script that is too thin.", "Mixed"),
    ("Visually inventive but narratively incoherent.", "Mixed"),
    ("The director shows great promise, even if the film itself is flawed.", "Mixed"),
    ("An interesting premise squandered by a by-the-numbers execution.", "Mixed"),
    ("The music is extraordinary; everything else is painfully average.", "Mixed"),
    ("Entertaining in patches but far too long and unfocused overall.", "Mixed"),
    ("A great first act gives way to a deeply unsatisfying conclusion.", "Mixed"),
    ("There are flashes of brilliance here, but they are too infrequent.", "Mixed"),
    ("The action sequences are spectacular; the quieter scenes fall flat.", "Mixed"),
    ("Starts brilliantly and then loses confidence in its own ideas.", "Mixed"),
    ("A decent film hampered by an unnecessarily complex plot.", "Mixed"),
    ("Some wonderful moments, but the tonal inconsistency is jarring.", "Mixed"),
    ("Half masterpiece, half misfire – a deeply frustrating experience.", "Mixed"),
    ("The world-building is superb but the characters remain one-dimensional.", "Mixed"),
    ("A charming love story undermined by a predictable and lazy ending.", "Mixed"),
    ("Technically impressive but emotionally distant.", "Mixed"),
    ("The comedy works brilliantly; the dramatic scenes feel forced.", "Mixed"),
    ("An ambitious film that only partially achieves its lofty goals.", "Mixed"),
    ("Gorgeous to look at, but the substance does not match the style.", "Mixed"),
    ("A well-intentioned film that stumbles in its third act.", "Mixed"),
    ("Inspired casting choices cannot overcome a flat and unimaginative script.", "Mixed"),
    ("The first two hours are gripping; the finale is deeply disappointing.", "Mixed"),
    ("Admirable ambition, inconsistent execution.", "Mixed"),
    ("The central relationship is compelling; the subplots are entirely surplus.", "Mixed"),
    ("A fine performance at the centre of an otherwise unremarkable film.", "Mixed"),
    ("Bold ideas that are not fully developed or satisfyingly resolved.", "Mixed"),
    ("Funny and irreverent when it works; tedious and repetitive when it does not.", "Mixed"),
    ("Moments of genuine magic surrounded by stretches of mediocrity.", "Mixed"),
    ("A strong opening act gives way to an increasingly muddled third hour.", "Mixed"),
    ("Its heart is in the right place even if the execution is uneven.", "Mixed"),
    ("The satire is sharp and incisive; the romance subplot is entirely superfluous.", "Mixed"),
    ("Genuinely thrilling in parts, frustratingly predictable in others.", "Mixed"),
    ("A film of two halves – one excellent, one disappointingly ordinary.", "Mixed"),
]


def make_examples():
    return [
        dspy.Example(review=rev, sentiment=lbl).with_inputs("review")
        for rev, lbl in EXAMPLES_RAW
    ]


# ─────────────────────────────────────────────
# 4.  Metric
# ─────────────────────────────────────────────

def sentiment_metric(example: dspy.Example, prediction, trace=None) -> float:
    """1.0 if the predicted label matches the gold label exactly, else 0.0."""
    pred_label = prediction.sentiment.strip()
    gold_label = example.sentiment.strip()
    return 1.0 if pred_label.lower() == gold_label.lower() else 0.0


# ─────────────────────────────────────────────
# 4b. Evaluation helper
# ─────────────────────────────────────────────

def evaluate_program(program: dspy.Module, dataset: list, label: str, console: Console) -> float:
    evaluator = dspy.Evaluate(
        devset=dataset,
        metric=sentiment_metric,
        num_threads=1,
        display_progress=False,
        display_table=0,
    )
    score = evaluator(program)
    if hasattr(score, "score"):
        raw = float(score.score)       # EvaluationResult → 0–100
    elif isinstance(score, tuple):
        raw = float(score[0])          # (score, results) tuple
    else:
        raw = float(score)
    normalised = raw / 100.0 if raw > 1.0 else raw
    console.print(f"  📊  [{label}] Accuracy: [bold green]{normalised:.1%}[/bold green] on {len(dataset)} examples")
    return normalised


# ─────────────────────────────────────────────
# 5.  Prompt Snapshot utility
# ─────────────────────────────────────────────

def extract_prompt_snapshot(program: dspy.Module) -> dict:
    """Extract instructions and demos from each predictor for diffing."""
    snapshots = {}
    for name, predictor in program.named_predictors():
        demos = getattr(predictor, "demos", []) or []
        instructions = (
            predictor.signature.instructions
            if hasattr(predictor.signature, "instructions")
            else "(auto)"
        )
        snapshots[name] = {
            "instructions": instructions,
            "num_demos": len(demos),
            "demos": demos[:3],
        }
    return snapshots


# ─────────────────────────────────────────────
# 6.  Main orchestration
# ─────────────────────────────────────────────

def main():
    console = Console()

    # ── Banner ────────────────────────────────
    console.print()
    console.print(
        Panel.fit(
            "[bold white]DSPy Prompt Optimization – Evolution Demo[/bold white]\n"
            "[dim]Showing how DSPy transforms a zero-shot prompt\n"
            "into an optimized few-shot prompt through training.[/dim]",
            border_style="bright_blue",
            padding=(1, 4),
        )
    )

    # ── LM Setup ─────────────────────────────
    lm = configure_lm()
    dspy.configure(lm=lm)
    litellm.drop_params = True  # Required for COPRO/MIPRO with Ollama (ignores 'n' param)

    # ── Dataset Split ─────────────────────────
    all_examples = make_examples()
    trainset = all_examples[:100]   # 100 for training
    devset   = all_examples[100:]   # 20  for evaluation

    console.print(f"\n📚  Dataset: {len(all_examples)} examples — "
                  f"[cyan]{len(trainset)} train[/cyan] / "
                  f"[green]{len(devset)} dev[/green]")

    stages_summary = []

    # ══════════════════════════════════════════
    # STAGE 0 – Baseline (zero-shot)
    # ══════════════════════════════════════════
    print_stage_header(console, 0, "Baseline (Zero-Shot — No Optimization)")
    baseline = SentimentClassifier()
    snap0 = extract_prompt_snapshot(baseline)
    print_prompt_snapshot(console, 0, "Stage 0 · Zero-Shot Baseline", snap0)

    console.print("\n  Running evaluation…")
    score0 = evaluate_program(baseline, devset, "Baseline", console)
    num_demos0 = sum(s["num_demos"] for s in snap0.values())
    stages_summary.append({"optimizer": "None (zero-shot)", "score": score0, "num_demos": num_demos0})

    # ══════════════════════════════════════════
    # STAGE 1 – COPRO (Instruction Optimization)
    # ══════════════════════════════════════════
    print_stage_header(console, 1, "COPRO — Instruction Optimization")
    console.print(
        "  [dim]COPRO explicitly optimizes the instruction string itself by generating\n"
        "  new variations and selecting the best performer on the dev set.\n"
        "  (It keeps the prompt zero-shot but improves the core instructions)[/dim]\n"
    )

    from dspy.teleprompt import COPRO

    optimizer1 = COPRO(
        metric=sentiment_metric,
        breadth=3,
        depth=1,
        verbose=False,
    )
    console.print("  ⚙️   Compiling with COPRO (mode: breadth=3, depth=1)…")
    # COPRO uses trainset for evaluation during search. We limit to 40 to evaluate better without taking forever.
    optimized1 = optimizer1.compile(
        SentimentClassifier(),
        trainset=trainset[:40],
        eval_kwargs={"num_threads": 1, "display_progress": False},
    )

    snap1 = extract_prompt_snapshot(optimized1)
    print_prompt_snapshot(console, 1, "Stage 1 · COPRO", snap1)

    console.print("\n  Running evaluation…")
    score1 = evaluate_program(optimized1, devset, "COPRO", console)
    num_demos1 = sum(s["num_demos"] for s in snap1.values())
    stages_summary.append({"optimizer": "COPRO", "score": score1, "num_demos": num_demos1})

    # ══════════════════════════════════════════
    # STAGE 2 – BootstrapFewShot (Auto Few-Shot Examples)
    # ══════════════════════════════════════════
    print_stage_header(console, 2, "BootstrapFewShot — Adding Examples to Optimized Instructions")
    console.print(
        "  [dim]BootstrapFewShot takes the optimized instructions from Stage 1,\n"
        "  runs them on training examples, filters successful traces, and injects them as demos.[/dim]\n"
    )

    from dspy.teleprompt import BootstrapFewShot

    optimizer2 = BootstrapFewShot(
        metric=sentiment_metric,
        max_bootstrapped_demos=3,
        max_labeled_demos=3,
        max_rounds=1,
    )
    console.print("  ⚙️   Compiling with BootstrapFewShot…")
    # We pass 'optimized1' as the student, so it keeps the COPRO instructions and adds demos!
    optimized2 = optimizer2.compile(optimized1, trainset=trainset)

    snap2 = extract_prompt_snapshot(optimized2)
    print_prompt_snapshot(console, 2, "Stage 2 · BootstrapFewShot", snap2)

    console.print("\n  Running evaluation…")
    score2 = evaluate_program(optimized2, devset, "BootstrapFewShot", console)
    num_demos2 = sum(s["num_demos"] for s in snap2.values())
    stages_summary.append(
        {"optimizer": "BootstrapFewShot", "score": score2, "num_demos": num_demos2}
    )

    # ── Chain of Thought live examples ──────────────────────
    print_cot_examples(console, optimized2, lm)

    # ── Prompt diff ───────────────────────────────────────────
    print_prompt_diff(console, snap0, snap2)

    # ══════════════════════════════════════════
    # SUMMARY TABLE (Moved to end for better visibility)
    # ══════════════════════════════════════════
    print_comparison_table(console, stages_summary)

    # ── Save the best program ─────────────────
    best_path = "best_program.json"
    optimized2.save(best_path)
    console.print(f"\n💾  Best program saved to [bold]{best_path}[/bold]")
    console.print(
        "\n[bold green]✅  Done![/bold green] "
        "The prompt evolved across 3 stages as DSPy bootstrapped and selected the best demonstrations.\n"
    )


if __name__ == "__main__":
    main()
