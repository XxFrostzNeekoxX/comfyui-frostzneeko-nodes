"""
FN Image Saver
Save images with custom naming, multiple formats (PNG / JPEG / WebP),
adjustable quality, and a **built-in preview** shown inside the node.
"""

import datetime
import json
import os

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
            },
            "optional": {
                "subfolder": ("STRING", {"default": ""}),
                "number_padding": ("INT", {"default": 3, "min": 1, "max": 8}),
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

    def save_images(
        self,
        images,
        filename_prefix="FrostzNeeko",
        format="png",
        quality=95,
        add_timestamp=True,
        numbering_style="comfy_default",
        subfolder="",
        number_padding=3,
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
                if not args.disable_metadata:
                    metadata = PngInfo()
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
            img.save(os.path.join(full_output_folder, file), **save_kwargs)

            results.append(
                {
                    "filename": file,
                    "subfolder": sub if not subfolder else subfolder,
                    "type": self.type,
                }
            )
            counter += 1
            print(f"[FrostzNeeko] 💾 Saved: {os.path.join(full_output_folder, file)}")

        # Return UI preview AND pass images through
        return {"ui": {"images": results}, "result": (images,)}
