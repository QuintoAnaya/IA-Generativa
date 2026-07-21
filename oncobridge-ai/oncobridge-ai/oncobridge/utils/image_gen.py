"""
Generacion local de la referencia visual sintetica del Componente 2.

Se usa Stable Diffusion a traves de `diffusers`, alimentado con los campos
`meddiffusion_prompt` y `meddiffusion_negative_prompt` que ya trae cada entrada
del ground truth.

Sobre la eleccion del modelo: el enunciado menciona 3D MedDiffusion, cuyo
repositorio oficial declara un requerimiento minimo de 40 GB de VRAM para
inferencia. Ese hardware no estaba disponible durante el desarrollo, de modo que
se utilizo Stable Diffusion 1.5, que corre en GPUs de consumo. Es un modelo
generalista y no un generador de imagen medica validado: la imagen resultante es
una ilustracion del patron descripto, no una reconstruccion radiologica fiel.

Estrategia de ejecucion, de mayor a menor calidad segun el hardware disponible:
  1. GPU CUDA, si `torch` la detecta.
  2. CPU con menos pasos de inferencia, si no hay GPU. Es lento (varios minutos)
     pero produce una imagen real.
  3. Esquema anatomico vectorial generado con Pillow, si `torch`/`diffusers` no
     estan instalados. Mantiene el pipeline ejecutable en cualquier maquina, con
     la limitacion indicada de forma explicita en la propia imagen y en el JSON.
"""

from __future__ import annotations

import hashlib
import textwrap
from pathlib import Path

DEFAULT_MODEL = "runwayml/stable-diffusion-v1-5"
_PIPELINE_CACHE = {}

_SAFETY_PREFIX = (
    "Synthetic educational radiology-style reference illustration. "
    "Grayscale medical imaging appearance. No text, no labels, no annotations, "
    "no watermarks, no patient identifiers. "
)
_BASE_NEGATIVE = "text, watermark, letters, numbers, annotations, patient identifier, color photograph, cartoon"


def _resolve_device(requested: str) -> str:
    try:
        import torch
    except ImportError:
        return "unavailable"
    if requested == "cpu":
        return "cpu"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _load_pipeline(device: str, model_id: str):
    key = (model_id, device)
    if key in _PIPELINE_CACHE:
        return _PIPELINE_CACHE[key]
    import torch
    from diffusers import StableDiffusionPipeline

    dtype = torch.float16 if device == "cuda" else torch.float32
    pipeline = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=dtype)
    pipeline.enable_attention_slicing()
    if device == "cuda":
        total_vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024 ** 3
        if total_vram_gb < 8:
            # Mantiene el modelo en RAM y sube los modulos a la GPU por turnos.
            # Es mas lento, pero permite ejecutar en placas de 4-6 GB.
            pipeline.enable_sequential_cpu_offload()
        else:
            pipeline.to(device)
    else:
        pipeline.to("cpu")
    _PIPELINE_CACHE[key] = pipeline
    return pipeline


def _schematic_fallback(prompt: str, body_region: str, priority_zones: list, out_path: Path):
    """Esquema anatomico simple, para entornos sin torch/diffusers instalados."""
    from PIL import Image, ImageDraw

    size = (512, 512)
    img = Image.new("RGB", size, (12, 14, 18))
    draw = ImageDraw.Draw(img)

    draw.ellipse([(96, 116), (416, 436)], outline=(150, 158, 170), width=2)
    draw.ellipse([(150, 176), (362, 376)], outline=(96, 104, 118), width=1)
    draw.ellipse([(232, 236), (300, 316)], outline=(214, 222, 232), width=2)
    draw.line([(256, 116), (256, 436)], fill=(52, 58, 68), width=1)
    draw.line([(96, 276), (416, 276)], fill=(52, 58, 68), width=1)

    draw.rectangle([(0, 0), (size[0], 34)], fill=(96, 34, 34))
    draw.text((12, 11), "ESQUEMA SINTETICO - NO ES UNA IMAGEN MEDICA", fill=(245, 245, 245))

    y = 452
    draw.text((12, y), f"Region: {body_region[:56]}", fill=(186, 194, 206))
    zones = ", ".join(priority_zones[:2]) if priority_zones else "no especificadas"
    for line in textwrap.wrap(f"Zonas prioritarias: {zones}", width=68)[:2]:
        y += 15
        draw.text((12, y), line, fill=(140, 148, 160))

    img.save(out_path)


def generate_reference(prompt: str, negative_prompt: str, out_dir: str,
                       body_region: str = "", priority_zones=None,
                       device: str = "auto", steps: int = 30,
                       seed: int = 20260721, model_id: str = DEFAULT_MODEL) -> dict:
    """Genera la referencia visual y devuelve la metadata de como se produjo."""
    priority_zones = priority_zones or []
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(f"{prompt}|{seed}".encode("utf-8")).hexdigest()[:10]
    out_path = Path(out_dir) / f"reference_{key}.png"

    full_prompt = _SAFETY_PREFIX + prompt
    full_negative = (negative_prompt + ", " + _BASE_NEGATIVE).strip(", ")

    resolved = _resolve_device(device)
    if resolved in ("cuda", "cpu"):
        try:
            import torch

            pipeline = _load_pipeline(resolved, model_id)
            inference_steps = steps if resolved == "cuda" else max(8, steps // 3)
            generator = torch.Generator(device="cpu" if resolved == "cpu" else resolved).manual_seed(seed)
            image = pipeline(
                prompt=full_prompt,
                negative_prompt=full_negative,
                num_inference_steps=inference_steps,
                guidance_scale=7.5,
                generator=generator,
                height=512,
                width=512,
            ).images[0]
            image.save(out_path)
            return {
                "image_path": str(out_path),
                "model": f"local:{model_id}",
                "device": resolved,
                "prompt": full_prompt,
                "negative_prompt": full_negative,
                "limitation": (
                    "Ilustracion sintetica generada con un modelo de difusion generalista. "
                    "No corresponde al paciente ni constituye una imagen radiologica validada."
                ),
            }
        except Exception as error:
            last_error = str(error)[:160]
    else:
        last_error = "torch/diffusers no instalados"

    _schematic_fallback(full_prompt, body_region, priority_zones, out_path)
    return {
        "image_path": str(out_path),
        "model": "esquema-vectorial (Pillow)",
        "device": "cpu",
        "prompt": full_prompt,
        "negative_prompt": full_negative,
        "limitation": (
            "No se ejecuto el modelo de difusion en este entorno "
            f"({last_error}). Se produjo un esquema anatomico orientativo que indica region y "
            "zonas prioritarias, sin valor radiologico."
        ),
    }
