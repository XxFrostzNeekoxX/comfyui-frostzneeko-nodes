"""
FN Metadata Reader
Read metadata from saved images and present a formatted text view.
"""

import os

from PIL import Image



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
                "output_pretty_metadata": ("BOOLEAN", {"default": True}),
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

    def read_metadata(
        self,
        image_path,
        prefer_output_dir=True,
        path_mode="file",
        selection_mode="latest",
        image_index=0,
        output_pretty_metadata=True,
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

        pretty_text = "\n".join(summary) if output_pretty_metadata else ""
        return {
            "ui": {
                "text": [pretty_text or "🧾 Pretty metadata output disabled."],
                "pretty_metadata": [pretty_text or ""],
                "selected_image_path": [selected_path],
                "selected_index": [int(selected_idx)],
                "total_images": [int(len(candidates)) if path_mode == "folder" else 1],
            },
            "result": (),
        }

