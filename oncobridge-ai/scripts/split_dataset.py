"""
Particion estratificada 70/30 del dataset de evaluacion.

Los umbrales de decision se calibran unicamente sobre la particion de
entrenamiento; la de prueba se reserva para la medicion final. Sin esta
separacion, los umbrales quedarian ajustados sobre los mismos casos con los que
despues se reporta el desempeno, y las metricas resultantes estarian sesgadas
hacia arriba.

La particion es estratificada por categoria (TP, TN, FP, FN, COMPLEX) para que
ambos subconjuntos mantengan la composicion del dataset original, y usa una
semilla fija para que sea reproducible.

Genera manifiestos con punteros a los casos; no copia ni modifica los originales.

Uso:
    python scripts/split_dataset.py
"""

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

SEED = 20260721
TRAIN_RATIO = 0.70


def main(dataset_dir="data/eval_dataset", out_dir="data_splits"):
    dataset_dir = Path(dataset_dir)
    index = json.loads((dataset_dir / "index.json").read_text(encoding="utf-8"))

    by_category = defaultdict(list)
    for case in index["cases"]:
        by_category[case["category"]].append(case["case_id"])

    rng = random.Random(SEED)
    train_ids, test_ids = [], []
    for category in sorted(by_category):
        ids = sorted(by_category[category])
        rng.shuffle(ids)
        cut = round(len(ids) * TRAIN_RATIO)
        train_ids.extend(ids[:cut])
        test_ids.extend(ids[cut:])

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    for name, ids in (("train_cases.json", train_ids), ("test_cases.json", test_ids)):
        payload = {
            "seed": SEED,
            "train_ratio": TRAIN_RATIO,
            "n_cases": len(ids),
            "case_ids": sorted(ids),
        }
        (Path(out_dir) / name).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    print(f"Particion generada con semilla {SEED}")
    print(f"  train: {len(train_ids)} casos -> {out_dir}/train_cases.json")
    print(f"  test:  {len(test_ids)} casos -> {out_dir}/test_cases.json")
    for category in sorted(by_category):
        n_train = sum(1 for i in train_ids if i in by_category[category])
        n_test = sum(1 for i in test_ids if i in by_category[category])
        print(f"  {category:8s} train={n_train:3d}  test={n_test:3d}")


if __name__ == "__main__":
    main()
