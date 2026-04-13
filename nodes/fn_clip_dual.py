"""
FN CLIP Dual Encode 🔹
Two text areas — positive on top, negative on bottom — with BREAK support
and [square bracket] de-emphasis for both. Outputs two CONDITIONING slots.

Weight handling follows ComfyUI's standard:
    (word)      → weight × 1.1   (native tokeniser)
    ((word))    → weight × 1.21  (native tokeniser)
    (word:1.5)  → weight 1.5     (native tokeniser)
    [word]      → weight ÷ 1.1   (converted to (word:0.9091) by this node)
    BREAK       → new 77-token conditioning chunk
"""

import re

# We reuse the bracket converter from FNClipAdvanced
from .fn_clip_advanced import FNClipAdvanced


class FNClipDualEncode:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip": ("CLIP",),
                "positive": (
                    "STRING",
                    {"multiline": True, "dynamicPrompts": True, "default": ""},
                ),
                "negative": (
                    "STRING",
                    {"multiline": True, "dynamicPrompts": True, "default": ""},
                ),
            },
            "optional": {
                "negative_clip": ("CLIP",),
            },
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "CLIP")
    RETURN_NAMES = ("positive", "negative", "clip")
    FUNCTION = "encode"
    CATEGORY = "FrotszNeeko 🔹/Conditioning"

    # ── encode a single text with [bracket] conversion + BREAK ───────
    @staticmethod
    def _encode_text(clip, text):
        if clip is None:
            raise RuntimeError(
                "[FrotszNeeko] CLIP input is None — your checkpoint may "
                "not contain a valid CLIP / text encoder model."
            )

        # Convert [bracket] de-emphasis (not handled by ComfyUI natively)
        text = FNClipAdvanced.convert_brackets(text)

        # Split by BREAK
        segments = re.split(r"\s*\bBREAK\b\s*", text)
        segments = [s.strip() for s in segments if s.strip()]
        if not segments:
            segments = [""]

        # Tokenize first segment (native tokeniser handles weight syntax)
        tokens = clip.tokenize(segments[0])

        # Extend token groups with BREAK segments
        for segment in segments[1:]:
            seg_tokens = clip.tokenize(segment)
            for key in tokens:
                if key in seg_tokens:
                    tokens[key].extend(seg_tokens[key])

        # Encode using the current ComfyUI scheduled API
        conditioning = clip.encode_from_tokens_scheduled(tokens)
        return conditioning

    # ── main ─────────────────────────────────────────────────────────
    def encode(self, clip, positive, negative, negative_clip=None):
        neg_clip = negative_clip if negative_clip is not None else clip
        pos_cond = self._encode_text(clip, positive)
        neg_cond = self._encode_text(neg_clip, negative)
        return (pos_cond, neg_cond, clip)
