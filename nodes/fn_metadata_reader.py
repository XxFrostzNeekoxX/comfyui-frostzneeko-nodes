"""
FN Metadata Reader
Read metadata from saved images and present a formatted text view.
"""

import json
import os

from PIL import Image

import folder_paths


class FNMetadataReader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_path": ("STRING", {"default": "", "multiline": False}),
                "prefer_output_dir": ("BOOLEAN", {"default": True}),
                "path_mode": (["file", "folder"], {"default": "file"}),
                "selection_mode": (["latest", "index"], {"default": "latest"}),
                "image_index": ("INT", {"default": 0, "min": 0, "max": 999999, "step": 1}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("pretty_metadata", "raw_metadata_json")
    FUNCTION = "read_metadata"
    OUTPUT_NODE = False
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
    def _safe_json(value):
        try:
            return json.dumps(value, ensure_ascii=False, indent=2)
        except Exception:
            return str(value)

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

    def read_metadata(
        self,
        image_path,
        prefer_output_dir=True,
        path_mode="file",
        selection_mode="latest",
        image_index=0,
    ):
        resolved = self._resolve_path(image_path, prefer_output_dir)
        if not resolved or not os.path.exists(resolved):
            msg = f"❌ File not found: {resolved or image_path}"
            return {"ui": {"text": [msg]}, "result": (msg, "{}")}

        selected_path = resolved
        candidates = []
        if path_mode == "folder":
            if not os.path.isdir(resolved):
                msg = f"❌ Expected a folder path but got: {resolved}"
                return {"ui": {"text": [msg]}, "result": (msg, "{}")}
            candidates = self._list_image_files(resolved)
            if not candidates:
                msg = f"⚠️ No image files found in folder: {resolved}"
                return {"ui": {"text": [msg]}, "result": (msg, "{}")}
            if selection_mode == "index":
                idx = max(0, min(int(image_index), len(candidates) - 1))
                selected_path = candidates[idx]
            else:
                selected_path = candidates[0]

        try:
            with Image.open(selected_path) as img:
                info = dict(img.info or {})
                fmt = img.format or "unknown"
                size = f"{img.width}x{img.height}"
                mode = img.mode
        except Exception as exc:
            msg = f"❌ Failed to open image metadata: {exc}"
            return {"ui": {"text": [msg]}, "result": (msg, "{}")}

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
            summary.append(f"🎯 Selection: {selection_mode} (index={image_index})")
            preview_names = [os.path.basename(p) for p in candidates[:12]]
            summary.append("🗂️ Recent files:")
            summary.append("\n".join(f"- {n}" for n in preview_names))

        if tail:
            summary.append("")
            summary.append("📘 Notepad tail block found:")
            summary.append(tail)
        elif pretty_block:
            summary.append("")
            summary.append("📘 Pretty metadata (PNG text):")
            summary.append(str(pretty_block))
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

        pretty_text = "\n".join(summary)
        raw_json = self._safe_json(
            {
                "path": selected_path,
                "path_mode": path_mode,
                "selection_mode": selection_mode,
                "image_index": image_index,
                "folder_candidates": candidates[:100],
                "image_info": info,
                "notepad_tail": tail,
            }
        )
        return {"ui": {"text": [pretty_text]}, "result": (pretty_text, raw_json)}

