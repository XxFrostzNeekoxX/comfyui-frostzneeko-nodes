"""
FN Image Saver
Save images with custom naming, multiple formats (PNG / JPEG / WebP),
adjustable quality, and a **built-in preview** shown inside the node.
"""

import datetime
import json
import os
import re

import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

import folder_paths
from comfy.cli_args import args


class FNImageSaver:

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "filename_prefix": ("STRING", {"default": "FrostzNeeko"}),
                "format": (["png", "jpeg", "webp"],),
                "quality": ("INT", {"default": 95, "min": 1, "max": 100}),
                "add_timestamp": ("BOOLEAN", {"default": True}),
                "numbering_style": (["comfy_default", "prefix_number"], {"default": "comfy_default"}),
                "save_pretty_metadata": ("BOOLEAN", {"default": True}),
                "append_notepad_metadata_tail": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "subfolder": ("STRING", {"default": ""}),
                "number_padding": ("INT", {"default": 3, "min": 1, "max": 8}),
                "positive_prompt": ("STRING", {"default": "", "multiline": True}),
                "negative_prompt": ("STRING", {"default": "", "multiline": True}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "FrostzNeeko 🔹/Image"

    @staticmethod
    def _find_first_node_by_types(prompt_obj, type_names):
        if not isinstance(prompt_obj, dict):
            return None
        for _, node in prompt_obj.items():
            if not isinstance(node, dict):
                continue
            if node.get("class_type") in type_names:
                return node
        return None

    @staticmethod
    def _extract_loras_from_text(text):
        if not isinstance(text, str):
            return []
        return re.findall(r"<lora:([^:>]+):([^>]+)>", text, flags=re.IGNORECASE)

    @staticmethod
    def _lookup_prompt_node(prompt_obj, node_id):
        if not isinstance(prompt_obj, dict):
            return None
        sid = str(node_id)
        if sid in prompt_obj:
            return prompt_obj[sid]
        try:
            iid = int(node_id)
            k = str(iid)
            if k in prompt_obj:
                return prompt_obj[k]
        except (TypeError, ValueError):
            pass
        return None

    @staticmethod
    def _find_workflow_node(extra_pnginfo, node_id):
        if not extra_pnginfo or not isinstance(extra_pnginfo, dict):
            return None
        wf = extra_pnginfo.get("workflow")
        if isinstance(wf, str):
            try:
                wf = json.loads(wf)
            except (json.JSONDecodeError, TypeError):
                wf = None
        if not isinstance(wf, dict):
            return None
        nodes = wf.get("nodes")
        if not isinstance(nodes, list):
            return None
        for n in nodes:
            if not isinstance(n, dict):
                continue
            nid = n.get("id")
            if nid == node_id or str(nid) == str(node_id):
                return n
        return None

    @staticmethod
    def _workflow_widget_string(workflow_node, widget_name):
        """Map a widget name to its value in LiteGraph `widgets_values` (incl. leading batch slot)."""
        if not isinstance(workflow_node, dict):
            return ""
        wv = workflow_node.get("widgets_values")
        inputs = workflow_node.get("inputs")
        if not isinstance(wv, list) or not isinstance(inputs, list):
            return ""
        widget_slot = -1
        n = 0
        for inp in inputs:
            if not isinstance(inp, dict):
                continue
            w = inp.get("widget")
            if not isinstance(w, dict):
                continue
            if w.get("name") == widget_name:
                widget_slot = n
                break
            n += 1
        if widget_slot < 0:
            return ""
        for idx in (widget_slot, widget_slot + 1):
            if idx < len(wv) and isinstance(wv[idx], str) and wv[idx].strip():
                return wv[idx].strip()
        return ""

    def _resolve_linked_text(self, prompt_obj, value, extra_pnginfo, depth=0, visited=None):
        """Turn ComfyUI prompt references [node_id, output_index] into a string when possible."""
        if visited is None:
            visited = set()
        if depth > 24:
            return ""
        if isinstance(value, str):
            return value.strip()
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            return ""
        try:
            src_id = int(value[0])
            out_idx = int(value[1])
        except (TypeError, ValueError):
            return ""
        key = (src_id, out_idx)
        if key in visited:
            return ""
        visited.add(key)
        node = self._lookup_prompt_node(prompt_obj, src_id)
        if not isinstance(node, dict):
            return ""
        ctype = node.get("class_type")
        inputs = node.get("inputs") if isinstance(node.get("inputs"), dict) else {}
        if ctype == "CLIPTextEncode":
            return self._resolve_linked_text(
                prompt_obj, inputs.get("text"), extra_pnginfo, depth + 1, visited
            )
        if ctype == "FNPromptFromFile":
            if out_idx in (5, 6):
                cp = inputs.get("current_prompt")
                if isinstance(cp, str) and cp.strip():
                    return cp.strip()
                wf_node = self._find_workflow_node(extra_pnginfo, src_id)
                if isinstance(wf_node, dict):
                    s = self._workflow_widget_string(wf_node, "current_prompt")
                    if s:
                        return s
            return ""
        if ctype == "PrimitiveString":
            v = inputs.get("value", "")
            if isinstance(v, str) and v.strip():
                return v.strip()
            return self._resolve_linked_text(
                prompt_obj, v, extra_pnginfo, depth + 1, visited
            )
        for k in ("text", "string", "value"):
            v = inputs.get(k)
            if v is not None and v is not value:
                r = self._resolve_linked_text(
                    prompt_obj, v, extra_pnginfo, depth + 1, visited
                )
                if r:
                    return r
        return ""

    def _build_pretty_metadata(self, prompt_obj, extra_pnginfo, positive_override="", negative_override=""):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        positive_txt = ""
        negative_txt = ""
        seed = "?"
        steps = "?"
        cfg = "?"
        sampler = "?"
        scheduler = "?"
        model_name = "?"
        clip_skip = "?"
        loras = []

        if isinstance(positive_override, str) and positive_override.strip():
            positive_txt = positive_override.strip()
            loras.extend(self._extract_loras_from_text(positive_txt))
        if isinstance(negative_override, str) and negative_override.strip():
            negative_txt = negative_override.strip()

        pf = self._find_first_node_by_types(prompt_obj, {"FNPromptFromFile"})
        kd = self._find_first_node_by_types(prompt_obj, {"FNKSamplerPreview", "KSampler", "KSamplerAdvanced"})
        cd = self._find_first_node_by_types(
            prompt_obj, {"FNClipDualEncode", "FNCLIPDualEncode", "CLIPTextEncode"}
        )
        ck = self._find_first_node_by_types(prompt_obj, {"CheckpointLoaderSimple", "FNCheckpointLoader"})

        if isinstance(pf, dict):
            inp = pf.get("inputs", {})
            clip_skip = inp.get("clip_skip", clip_skip)
            ckpt_pf = inp.get("checkpoint_name", inp.get("ckpt_name", ""))
            if isinstance(ckpt_pf, str) and ckpt_pf.strip():
                model_name = ckpt_pf
            p2 = inp.get("processed_prompt", "")
            if isinstance(p2, str) and p2.strip():
                positive_txt = p2
            p3 = inp.get("raw_prompt", "")
            if isinstance(p3, str) and p3.strip() and not positive_txt:
                positive_txt = p3

        if isinstance(cd, dict):
            inp = cd.get("inputs", {})
            ctype = cd.get("class_type")
            if ctype == "CLIPTextEncode":
                pos = inp.get("text", "")
                neg = ""
            else:
                pos = inp.get("positive", "")
                neg = inp.get("negative", "")
            if not positive_txt:
                if isinstance(pos, str) and pos.strip():
                    positive_txt = pos
                else:
                    resolved = self._resolve_linked_text(prompt_obj, pos, extra_pnginfo)
                    if resolved:
                        positive_txt = resolved
                if positive_txt:
                    loras.extend(self._extract_loras_from_text(positive_txt))
            if not negative_txt:
                if isinstance(neg, str) and neg.strip():
                    negative_txt = neg
                else:
                    resolved_n = self._resolve_linked_text(prompt_obj, neg, extra_pnginfo)
                    if resolved_n:
                        negative_txt = resolved_n

        if isinstance(kd, dict):
            inp = kd.get("inputs", {})
            seed = inp.get("seed", seed)
            steps = inp.get("steps", steps)
            cfg = inp.get("cfg", cfg)
            sampler = inp.get("sampler_name", sampler)
            scheduler = inp.get("scheduler", scheduler)

        if isinstance(ck, dict):
            inp = ck.get("inputs", {})
            model_name = inp.get("ckpt_name", model_name)

        # global fallback scan through all node text inputs
        if isinstance(prompt_obj, dict):
            for _, node in prompt_obj.items():
                if not isinstance(node, dict):
                    continue
                inputs = node.get("inputs", {})
                if not isinstance(inputs, dict):
                    continue
                for key, val in inputs.items():
                    if not isinstance(val, str):
                        continue
                    if key.lower() in {"text", "prompt", "positive"} and not positive_txt:
                        positive_txt = val
                    if key.lower() in {"negative", "negative_prompt"} and not negative_txt:
                        negative_txt = val
                    loras.extend(self._extract_loras_from_text(val))

        lora_lines = []
        seen = set()
        for name, weight in loras:
            key = (name.strip(), str(weight).strip())
            if key in seen:
                continue
            seen.add(key)
            lora_lines.append(f"- `{key[0]}` ({key[1]})")
        if not lora_lines:
            lora_lines.append("- none")

        pretty = (
            f"🧊 FrostzNeeko Metadata\n"
            f"📅 Generated: {now}\n"
            f"🎲 Seed: {seed}\n"
            f"🪜 Steps: {steps}\n"
            f"🎛️ CFG: {cfg}\n"
            f"🧪 Sampler: {sampler}\n"
            f"🗓️ Scheduler: {scheduler}\n"
            f"🧠 Model: {model_name}\n"
            f"🎚️ Clip Skip: {clip_skip}\n\n"
            f"✨ LoRAs:\n" + "\n".join(lora_lines) + "\n\n"
            f"🟢 Positive:\n{positive_txt}\n\n"
            f"🔴 Negative:\n{negative_txt}"
        )

        parameters = (
            f"Seed: {seed}, Steps: {steps}, CFG: {cfg}, Sampler: {sampler}, "
            f"Scheduler: {scheduler}, Clip skip: {clip_skip}, Model: {model_name}"
        )
        return pretty, parameters

    def save_images(
        self,
        images,
        filename_prefix="FrostzNeeko",
        format="png",
        quality=95,
        add_timestamp=True,
        numbering_style="comfy_default",
        save_pretty_metadata=True,
        append_notepad_metadata_tail=True,
        subfolder="",
        number_padding=3,
        positive_prompt="",
        negative_prompt="",
        prompt=None,
        extra_pnginfo=None,
    ):
        prefix = filename_prefix
        if add_timestamp:
            prefix += "_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        out_dir = self.output_dir
        if subfolder:
            out_dir = os.path.join(out_dir, subfolder)
            os.makedirs(out_dir, exist_ok=True)

        (
            full_output_folder,
            filename,
            counter,
            sub,
            prefix,
        ) = folder_paths.get_save_image_path(
            prefix, out_dir, images[0].shape[1], images[0].shape[0]
        )

        results = []

        for batch_idx in range(images.shape[0]):
            img_np = 255.0 * images[batch_idx].cpu().numpy()
            img = Image.fromarray(np.clip(img_np, 0, 255).astype(np.uint8))

            ext = format
            save_kwargs: dict = {}

            if format == "png":
                metadata = None
                pretty_meta = None
                if not args.disable_metadata:
                    metadata = PngInfo()
                    if save_pretty_metadata:
                        pretty_meta, parameters_meta = self._build_pretty_metadata(
                            prompt,
                            extra_pnginfo,
                            positive_override=positive_prompt,
                            negative_override=negative_prompt,
                        )
                        metadata.add_text("fn_pretty_metadata", pretty_meta)
                        metadata.add_text("parameters", parameters_meta)
                    if prompt is not None:
                        metadata.add_text("prompt", json.dumps(prompt))
                    if extra_pnginfo is not None:
                        for key in extra_pnginfo:
                            metadata.add_text(key, json.dumps(extra_pnginfo[key]))
                save_kwargs = {
                    "pnginfo": metadata,
                    "compress_level": self.compress_level,
                }

            elif format == "jpeg":
                if img.mode == "RGBA":
                    img = img.convert("RGB")
                save_kwargs = {"quality": quality}
                ext = "jpg"

            elif format == "webp":
                save_kwargs = {"quality": quality}

            if numbering_style == "prefix_number":
                file = f"{filename}_{counter:0{number_padding}d}.{ext}"
            else:
                file = f"{filename}_{counter:05}_.{ext}"
            file_path = os.path.join(full_output_folder, file)
            img.save(file_path, **save_kwargs)

            # Optional plain-text tail for easy Notepad viewing.
            # PNG readers ignore trailing bytes after IEND.
            if (
                format == "png"
                and append_notepad_metadata_tail
                and save_pretty_metadata
                and pretty_meta
            ):
                tail = (
                    "\n\n===== FROSTZNEEKO METADATA (NOTEPAD) =====\n"
                    + pretty_meta
                    + "\n===== END FROSTZNEEKO METADATA =====\n"
                )
                with open(file_path, "ab") as f:
                    f.write(tail.encode("utf-8", errors="ignore"))

            results.append(
                {
                    "filename": file,
                    "subfolder": sub if not subfolder else subfolder,
                    "type": self.type,
                }
            )
            counter += 1
            print(f"[FrostzNeeko] 💾 Saved: {file_path}")

        # Return UI preview AND pass images through
        return {"ui": {"images": results}, "result": (images,)}
