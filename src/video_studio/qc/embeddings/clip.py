"""CLIP text/image pair via fastembed's ONNX models — zero new dependencies.

`Qdrant/clip-ViT-B-32-text` (0.25 GB) and `Qdrant/clip-ViT-B-32-vision`
(0.34 GB) share one 512-d space and both L2-normalize their output, so
cosine similarity is a plain dot product. First use downloads the models to
the fastembed cache.

fastembed's ImageEmbedding accepts paths or PIL Images — NOT numpy arrays —
so cv2 BGR frames go through `PIL.Image.fromarray(frame[:, :, ::-1])`.
"""

from __future__ import annotations

from typing import Any

import numpy as np

TEXT_MODEL = "Qdrant/clip-ViT-B-32-text"
VISION_MODEL = "Qdrant/clip-ViT-B-32-vision"
DIM = 512


class ClipPair:
    """Lazy holder for the matched text+vision encoders."""

    def __init__(self) -> None:
        from fastembed import ImageEmbedding, TextEmbedding

        self._text = TextEmbedding(TEXT_MODEL)
        self._vision = ImageEmbedding(VISION_MODEL)

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """(n, 512) L2-normalized. CLIP truncates at 77 tokens — long scene
        prompts lose their tail, which is fine for gist matching."""
        return np.array([list(map(float, v)) for v in self._text.embed(texts)])

    def embed_bgr_frames(self, frames: list[Any]) -> np.ndarray:
        """(n, 512) L2-normalized from cv2 BGR ndarrays."""
        from PIL import Image

        images = [Image.fromarray(f[:, :, ::-1]) for f in frames]
        return np.array([list(map(float, v)) for v in self._vision.embed(images)])
