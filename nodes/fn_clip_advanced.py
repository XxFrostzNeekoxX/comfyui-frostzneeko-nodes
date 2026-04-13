"""
FN CLIP Text Encode (Advanced)
CLIP encoder with BREAK keyword support and [square bracket] de-emphasis.

ComfyUI's tokeniser already handles the standard A1111 emphasis natively:
    (word)      → weight × 1.1
    ((word))    → weight × 1.21
    (word:1.5)  → weight 1.5

This node adds:
    [word]      → weight ÷ 1.1  (≈0.909)  — NOT supported natively
    BREAK       → splits prompt into separate 77-token conditioning chunks
"""

import re


class FNClipAdvanced:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip": ("CLIP",),
                "text": ("STRING", {"multiline": True, "dynamicPrompts": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("CONDITIONING",)
    RETURN_NAMES = ("conditioning",)
    FUNCTION = "encode"
    CATEGORY = "FrotszNeeko 🔹/Conditioning"

    # ── Square-bracket de-emphasis ────────────────────────────────────
    # ComfyUI's tokeniser handles (parentheses) but NOT [brackets].
    # We convert [word] → (word:0.9091) before passing to tokenize().

    @staticmethod
    def _find_matching_bracket(text, start):
        """Return index of the matching ']', or -1."""
        depth = 1
        i = start
        while i < len(text):
            if text[i] == "[":
                depth += 1
            elif text[i] == "]":
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return -1

    @classmethod
    def convert_brackets(cls, text):
        """
        Convert [word] de-emphasis to (word:0.9091).
        Handles nesting: [[word]] → ((word:0.9091):0.9091)
        Leaves everything else untouched for the native tokeniser.
        """
        result = ""
        i = 0
        while i < len(text):
            if text[i] == "[" and i + 1 < len(text):
                close = cls._find_matching_bracket(text, i + 1)
                if close == -1:
                    result += text[i]
                    i += 1
                    continue

                inner = text[i + 1 : close]
                processed = cls.convert_brackets(inner)
                result += f"({processed}:0.9091)"
                i = close + 1
            else:
                result += text[i]
                i += 1

        return result

    # ── Main encode ──────────────────────────────────────────────────

    def encode(self, clip, text):
        if clip is None:
            raise RuntimeError(
                "[FrotszNeeko] CLIP input is None — your checkpoint may "
                "not contain a valid CLIP / text encoder model."
            )

        # 1. Convert [bracket] de-emphasis (not handled by ComfyUI)
        text = self.convert_brackets(text)

        # 2. Split by BREAK keyword
        segments = re.split(r"\s*\bBREAK\b\s*", text)
        segments = [s.strip() for s in segments if s.strip()]
        if not segments:
            segments = [""]

        # 3. Tokenize first segment
        #    clip.tokenize() handles (word:weight) emphasis natively
        tokens = clip.tokenize(segments[0])

        # 4. Tokenize & merge remaining segments (BREAK behaviour)
        #    Each BREAK starts a new 77-token chunk that is concatenated
        #    along the token axis, exactly like A1111.
        for segment in segments[1:]:
            seg_tokens = clip.tokenize(segment)
            for key in tokens:
                if key in seg_tokens:
                    tokens[key].extend(seg_tokens[key])

        # 5. Encode using the current ComfyUI scheduled API
        conditioning = clip.encode_from_tokens_scheduled(tokens)

        return (conditioning,)
