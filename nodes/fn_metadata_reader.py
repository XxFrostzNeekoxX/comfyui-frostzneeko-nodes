"""
FN Metadata Reader
Read metadata from saved images and present a formatted text view.
"""

import os
import re

import numpy as np
from PIL import Image

import folder_paths


class FNMetadataReader:
    def __init__(self):
        self.output_dir = folder_paths.get_temp_directory()
        self.type = "temp"
        self.compress_level = 1

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_path": ("STRING", {"default": "", "multiline": False}),
                "prefer_output_dir": ("BOOLEAN", {"default": True}),
                "path_mode": (["file", "folder"], {"default": "file"}),
                "selection_mode": (["latest", "index"], {"default": "latest"}),
                "image_index": ("INT", {"default": 0, "min": 0, "max": 999999, "step": 1}),
                "output_pretty_metadata": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "metadata_textbox": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "placeholder": "🧾 Metadata will appear here after execution...",
                    },
                ),
            },
        }

    RETURN_TYPES = ()
    RETURN_NAMES = ()
    FUNCTION = "read_metadata"
    OUTPUT_NODE = True
    CATEGORY = "FrostzNeeko 🔹/Image"

    @staticmethod
    def _resolve_path(image_path: str, prefer_output_dir: bool) -> str:
        if not image_path:
            return ""
        if os.path.isabs(image_path):
            return image_path
        if prefer_output_dir:
            return os.path.join(folder_paths.get_output_directory(), image_path)
        return os.path.abspath(image_path)

    @staticmethod
    def _extract_notepad_tail(path: str) -> str:
        try:
            with open(path, "rb") as f:
                data = f.read()
            text = data.decode("utf-8", errors="ignore")
            start = "===== FROSTZNEEKO METADATA (NOTEPAD) ====="
            end = "===== END FROSTZNEEKO METADATA ====="
            i = text.find(start)
            if i == -1:
                return ""
            j = text.find(end, i)
            if j == -1:
                return text[i:].strip()
            return text[i : j + len(end)].strip()
        except Exception:
            return ""

    @staticmethod
    def _list_image_files(folder_path: str):
        exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
        out = []
        try:
            for name in os.listdir(folder_path):
                full = os.path.join(folder_path, name)
                if not os.path.isfile(full):
                    continue
                if os.path.splitext(name)[1].lower() in exts:
                    out.append(full)
        except Exception:
            return []
        return sorted(out, key=lambda p: os.path.getmtime(p), reverse=True)

    @staticmethod
    def _parse_parameters_text(parameters: str):
        """Parse common 'parameters' blocks (A1111 style) into a structured dict."""
        if not isinstance(parameters, str) or not parameters.strip():
            return {"positive": "", "negative": "", "fields": {}, "raw": ""}
        raw = parameters.strip()
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        if not lines:
            return {"positive": "", "negative": "", "fields": {}, "raw": raw}

        # Typical shape:
        # <positive prompt lines>
        # Negative prompt: <text>
        # Steps: 30, Sampler: Euler, CFG scale: 7, Seed: 123, Size: 512x512, ...
        positive = []
        negative = ""
        fields = {}
        in_positive = True

        for i, line in enumerate(lines):
            low = line.lower()
            if low.startswith("negative prompt:"):
                in_positive = False
                negative = line.split(":", 1)[1].strip() if ":" in line else ""
                continue

            # Last metadata line usually starts with "Steps:"
            if re.match(r"^steps\s*:", line, flags=re.IGNORECASE):
                parts = [p.strip() for p in line.split(",") if p.strip()]
                for part in parts:
                    if ":" not in part:
                        continue
                    k, v = part.split(":", 1)
                    fields[k.strip()] = v.strip()
                continue

            # If we are after prompt sections and the line looks like k:v list
            if not in_positive and ":" in line and i >= max(1, len(lines) - 2):
                parts = [p.strip() for p in line.split(",") if p.strip()]
                if any(":" in p for p in parts):
                    for part in parts:
                        if ":" not in part:
                            continue
                        k, v = part.split(":", 1)
                        fields[k.strip()] = v.strip()
                    continue

            if in_positive:
                positive.append(line)

        return {
            "positive": "\n".join(positive).strip(),
            "negative": negative.strip(),
            "fields": fields,
            "raw": raw,
        }

    @staticmethod
    def _compose_normalized_metadata(info, selected_path, fmt, size, mode):
        """Normalize external metadata into FrostzNeeko-style readable block."""
        parameters = info.get("parameters", "")
        parsed = FNMetadataReader._parse_parameters_text(parameters)

        positive = parsed.get("positive", "")
        negative = parsed.get("negative", "")
        fields = parsed.get("fields", {})

        def pick(*keys, default="?"):
            for k in keys:
                if k in fields and str(fields[k]).strip():
                    return str(fields[k]).strip()
            return default

        # Common aliases across tools
        seed = pick("Seed", "seed")
        steps = pick("Steps", "steps")
        cfg = pick("CFG scale", "CFG", "cfg", "cfg scale")
        sampler = pick("Sampler", "sampler")
        scheduler = pick("Schedule type", "Scheduler", "scheduler")
        model = pick("Model", "Model hash", "model")
        clip_skip = pick("Clip skip", "clip_skip", "clip skip")
        size_field = pick("Size", default=size)

        lines = [
            "🧊 FrostzNeeko Metadata (normalized)",
            f"📂 Path: {selected_path}",
            f"🖼️ Format: {fmt} | Size: {size_field} | Mode: {mode}",
            f"🎲 Seed: {seed}",
            f"🪜 Steps: {steps}",
            f"🎛️ CFG: {cfg}",
            f"🧪 Sampler: {sampler}",
            f"🗓️ Scheduler: {scheduler}",
            f"🧠 Model: {model}",
            f"🎚️ Clip Skip: {clip_skip}",
            "",
            "🟢 Positive:",
            positive or "(not found)",
            "",
            "🔴 Negative:",
            negative or "(not found)",
        ]

        # Keep a compact dump of remaining fields for transparency
        shown = {"Seed", "seed", "Steps", "steps", "CFG scale", "CFG", "cfg", "cfg scale", "Sampler", "sampler", "Schedule type", "Scheduler", "scheduler", "Model", "Model hash", "model", "Clip skip", "clip_skip", "clip skip", "Size"}
        leftovers = [(k, v) for k, v in fields.items() if k not in shown]
        if leftovers:
            lines.append("")
            lines.append("📎 Other fields:")
            for k, v in leftovers:
                lines.append(f"- {k}: {v}")

        if isinstance(info.get("prompt"), str) and info.get("prompt").strip():
            lines.append("")
            lines.append("🧾 Raw prompt key: present")
        if isinstance(info.get("workflow"), str) and info.get("workflow").strip():
            lines.append("🔧 Raw workflow key: present")

        return "\n".join(lines)

    def _save_ui_preview(self, pil_img, selected_path):
        arr = np.array(pil_img.convert("RGB"), dtype=np.uint8)
        base = os.path.splitext(os.path.basename(selected_path))[0] or "FNMeta"
        folder, fname, counter, sub, _ = folder_paths.get_save_image_path(
            f"FNMetaReader_{base}",
            self.output_dir,
            arr.shape[1],
            arr.shape[0],
        )
        file = f"{fname}_{counter:05}_.png"
        full_path = os.path.join(folder, file)
        Image.fromarray(arr).save(full_path, compress_level=self.compress_level)
        return [{"filename": file, "subfolder": sub, "type": self.type}]

    def read_metadata(
        self,
        image_path,
        prefer_output_dir=True,
        path_mode="file",
        selection_mode="latest",
        image_index=0,
        output_pretty_metadata=True,
        metadata_textbox="",
    ):
        resolved = self._resolve_path(image_path, prefer_output_dir)
        if not resolved or not os.path.exists(resolved):
            msg = f"❌ File not found: {resolved or image_path}"
            return {"ui": {"text": [msg], "pretty_metadata": [msg], "selected_image_path": [""], "selected_index": [0], "total_images": [0]}, "result": ()}

        selected_path = resolved
        candidates = []
        selected_idx = 0
        if path_mode == "folder":
            if not os.path.isdir(resolved):
                msg = f"❌ Expected a folder path but got: {resolved}"
                return {"ui": {"text": [msg], "pretty_metadata": [msg], "selected_image_path": [""], "selected_index": [0], "total_images": [0]}, "result": ()}
            candidates = self._list_image_files(resolved)
            if not candidates:
                msg = f"⚠️ No image files found in folder: {resolved}"
                return {"ui": {"text": [msg], "pretty_metadata": [msg], "selected_image_path": [""], "selected_index": [0], "total_images": [0]}, "result": ()}
            if selection_mode == "index":
                selected_idx = max(0, min(int(image_index), len(candidates) - 1))
                selected_path = candidates[selected_idx]
            else:
                selected_path = candidates[0]
                selected_idx = 0

        try:
            with Image.open(selected_path) as img:
                info = dict(img.info or {})
                fmt = img.format or "unknown"
                size = f"{img.width}x{img.height}"
                mode = img.mode
                rgb = img.convert("RGB")
        except Exception as exc:
            msg = f"❌ Failed to open image metadata: {exc}"
            return {"ui": {"text": [msg], "pretty_metadata": [msg], "selected_image_path": [""], "selected_index": [0], "total_images": [0]}, "result": ()}

        tail = self._extract_notepad_tail(selected_path)
        pretty_block = info.get("fn_pretty_metadata", "")
        parameters = info.get("parameters", "")

        summary = [
            "🧾 FrostzNeeko Metadata Reader",
            f"📂 Path: {selected_path}",
            f"🖼️ Format: {fmt} | Size: {size} | Mode: {mode}",
            f"🧩 Embedded keys: {', '.join(sorted(info.keys())) if info else 'none'}",
        ]
        if path_mode == "folder":
            summary.append(f"📁 Folder mode: {len(candidates)} image(s) found")
            summary.append(f"🎯 Selection: {selection_mode} (index={selected_idx})")
            preview_names = [os.path.basename(p) for p in candidates[:12]]
            summary.append("🗂️ Recent files:")
            summary.append("\n".join(f"- {n}" for n in preview_names))

        normalized_external = ""
        if not tail and not pretty_block:
            # If image wasn't saved by FNImageSaver, try to normalize common metadata keys.
            if parameters or info.get("prompt") or info.get("workflow"):
                normalized_external = self._compose_normalized_metadata(
                    info, selected_path, fmt, size, mode
                )

        if tail:
            summary.append("")
            summary.append("📘 Notepad tail block found:")
            summary.append(tail)
        elif pretty_block:
            summary.append("")
            summary.append("📘 Pretty metadata (PNG text):")
            summary.append(str(pretty_block))
        elif normalized_external:
            summary.append("")
            summary.append("📘 External metadata detected and normalized:")
            summary.append(normalized_external)
        elif parameters:
            summary.append("")
            summary.append("📘 Parameters:")
            summary.append(str(parameters))
        else:
            summary.append("")
            summary.append("⚠️ No pretty metadata found in this image.")

        if "prompt" in info:
            summary.append("")
            summary.append("🟢 Prompt metadata key found.")
        if "workflow" in info:
            summary.append("🔧 Workflow metadata key found.")

        pretty_text = "\n".join(summary) if output_pretty_metadata else ""
        ui_images = self._save_ui_preview(rgb, selected_path)
        return {
            "ui": {
                "text": [pretty_text or "🧾 Pretty metadata output disabled."],
                "images": ui_images,
                "metadata_textbox": [pretty_text or ""],
                "pretty_metadata": [pretty_text or ""],
                "selected_image_path": [selected_path],
                "selected_index": [int(selected_idx)],
                "total_images": [int(len(candidates)) if path_mode == "folder" else 1],
            },
            "result": (),
        }

