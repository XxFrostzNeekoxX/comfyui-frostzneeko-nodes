"""
FN Face Detailer 🔹
All-in-one face/feature detailer that performs detection + detailing in a single node.

All in one node with options for:
  guide_size, guide_size_for, max_size, seed, steps, cfg, sampler,
  scheduler, denoise, feather, noise_mask, force_inpaint, cycle,
  noise_mask_feather, drop_size, dilation, threshold, crop_factor

Plus toggle control via detail_pipe from FN KSampler Preview.
"""

import json
import os
import random

import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

import comfy.samplers
import folder_paths
from comfy.cli_args import args

from .fn_detail_utils import get_detector_model_list, run_face_detail


class FNFaceDetailer:

    def __init__(self):
        self.output_dir = folder_paths.get_temp_directory()
        self.type = "temp"
        self.prefix_append = "_fnfd_" + "".join(
            random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(5)
        )
        self.compress_level = 1

    @classmethod
    def INPUT_TYPES(cls):
        models = get_detector_model_list()
        return {
            "required": {
                "image": ("IMAGE",),
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "vae": ("VAE",),
                "positive": ("CONDITIONING",),
                "negative": ("CONDITIONING",),
                "detector_model": (models,),
                "name": (
                    "STRING",
                    {"default": "Face Detailer", "multiline": False},
                ),
                # ── detection ────────────────────────────────────
                "threshold": (
                    "FLOAT",
                    {"default": 0.5, "min": 0.05, "max": 1.0, "step": 0.05},
                ),
                "dilation": (
                    "INT",
                    {"default": 10, "min": -512, "max": 512, "step": 1},
                ),
                "crop_factor": (
                    "FLOAT",
                    {"default": 3.0, "min": 1.0, "max": 10.0, "step": 0.1},
                ),
                "drop_size": (
                    "INT",
                    {"default": 10, "min": 1, "max": 512, "step": 1},
                ),
                # ── guide size ───────────────────────────────────
                "guide_size": (
                    "INT",
                    {"default": 512, "min": 64, "max": 4096, "step": 8},
                ),
                "guide_size_for": (["bbox", "crop"],),
                "max_size": (
                    "INT",
                    {"default": 1024, "min": 64, "max": 4096, "step": 8},
                ),
                # ── sampling ─────────────────────────────────────
                "seed": (
                    "INT",
                    {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF},
                ),
                "steps": ("INT", {"default": 30, "min": 1, "max": 10000}),
                "cfg": (
                    "FLOAT",
                    {"default": 5.5, "min": 0.0, "max": 100.0, "step": 0.1},
                ),
                "sampler_name": (comfy.samplers.KSampler.SAMPLERS,),
                "scheduler": (comfy.samplers.KSampler.SCHEDULERS,),
                "denoise": (
                    "FLOAT",
                    {"default": 0.60, "min": 0.0, "max": 1.0, "step": 0.05},
                ),
                # ── masking / inpaint ────────────────────────────
                "feather": (
                    "INT",
                    {"default": 5, "min": 0, "max": 100, "step": 1},
                ),
                "noise_mask": (["enabled", "disabled"],),
                "force_inpaint": (["enabled", "disabled"],),
                "noise_mask_feather": (
                    "INT",
                    {"default": 20, "min": 0, "max": 100, "step": 1},
                ),
                # ── cycle ────────────────────────────────────────
                "cycle": (
                    "INT",
                    {"default": 1, "min": 1, "max": 10, "step": 1},
                ),
                "mask_preview": (["disabled", "enabled"],),
                "tiled_encode": (["disabled", "enabled"],),
                "tiled_decode": (["disabled", "enabled"],),
            },
            "optional": {
                "detail_pipe": ("FN_DETAIL_PIPE",),
                "refiner_model": ("MODEL",),
                "refiner_positive": ("CONDITIONING",),
                "refiner_negative": ("CONDITIONING",),
                "refiner_ratio": (
                    "FLOAT",
                    {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01},
                ),
                # wildcard spec for the detail prompt
                "wildcard_spec": (
                    "STRING",
                    {"default": "", "multiline": True},
                ),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("IMAGE", "IMAGE")
    RETURN_NAMES = ("image", "mask_preview")
    FUNCTION = "detail"
    OUTPUT_NODE = True
    CATEGORY = "FrostzNeeko 🔹/Detailer"

    # ─────────────────────────────────────────────────────────────────
    def detail(
        self,
        image,
        model,
        clip,
        vae,
        positive,
        negative,
        detector_model,
        name,
        threshold,
        dilation,
        crop_factor,
        drop_size,
        guide_size,
        guide_size_for,
        max_size,
        seed,
        steps,
        cfg,
        sampler_name,
        scheduler,
        denoise,
        feather,
        noise_mask,
        force_inpaint,
        noise_mask_feather,
        cycle,
        mask_preview,
        tiled_encode,
        tiled_decode,
        detail_pipe=None,
        refiner_model=None,
        refiner_positive=None,
        refiner_negative=None,
        refiner_ratio=0.0,
        wildcard_spec="",
        prompt=None,
        extra_pnginfo=None,
    ):
        display_name = name.strip() if name else "Face Detailer"

        # ── check toggle from KSampler ───────────────────────────────
        if detail_pipe is not None:
            toggles = detail_pipe.get("toggles", {})
            if display_name in toggles and not toggles[display_name]:
                print(
                    f"[FrostzNeeko] ⏭️  '{display_name}' is DISABLED — passing through"
                )
                empty_mask = image[:, :, :, :1] * 0.0
                preview = self._save_preview(image, prompt, extra_pnginfo, prefix_base="FNDetailer")
                if mask_preview == "enabled":
                    preview += self._save_preview(empty_mask, prompt, extra_pnginfo, prefix_base="FNDetailerMask")
                return {"ui": {"images": preview}, "result": (image, empty_mask)}
            elif display_name in toggles and toggles[display_name]:
                print(
                    f"[FrostzNeeko] 🎯 '{display_name}' is ENABLED via toggle"
                )
            else:
                print(
                    f"[FrostzNeeko] ℹ️  '{display_name}' not in toggle list — running"
                )

        # ── handle wildcard spec conditioning ────────────────────────
        detail_positive = positive
        if wildcard_spec and wildcard_spec.strip():
            try:
                tokens = clip.tokenize(wildcard_spec.strip())
                detail_positive = clip.encode_from_tokens_scheduled(tokens)
                print(
                    f"[FrostzNeeko] 📝 Using wildcard spec: "
                    f"{wildcard_spec.strip()[:60]}…"
                )
            except Exception as exc:
                print(f"[FrostzNeeko] ⚠️  Wildcard spec encode failed: {exc}")

        # ── run the detail pass ──────────────────────────────────────
        print(f"[FrostzNeeko] 🎯 '{display_name}' — running detail pass")

        result = run_face_detail(
            image,
            model,
            vae,
            detail_positive,
            negative,
            detector_model,
            seed=seed,
            steps=steps,
            cfg=cfg,
            sampler_name=sampler_name,
            scheduler=scheduler,
            denoise=denoise,
            threshold=threshold,
            dilation=dilation,
            crop_factor=crop_factor,
            feather=feather,
            guide_size=guide_size,
            guide_size_for=guide_size_for,
            max_size=max_size,
            noise_mask_enabled=(noise_mask == "enabled"),
            force_inpaint=(force_inpaint == "enabled"),
            cycle=cycle,
            noise_mask_feather=noise_mask_feather,
            drop_size=drop_size,
            return_mask_preview=(mask_preview == "enabled"),
            tiled_encode=(tiled_encode == "enabled"),
            tiled_decode=(tiled_decode == "enabled"),
            refiner_ratio=refiner_ratio,
            refiner_model=refiner_model,
            refiner_positive=refiner_positive,
            refiner_negative=refiner_negative,
        )

        if mask_preview == "enabled":
            detailed, mask_img = result
            preview = self._save_preview(detailed, prompt, extra_pnginfo, prefix_base="FNDetailer")
            preview += self._save_preview(mask_img, prompt, extra_pnginfo, prefix_base="FNDetailerMask")
            return {"ui": {"images": preview}, "result": (detailed, mask_img)}

        detailed = result
        empty_mask = image[:, :, :, :1] * 0.0
        preview = self._save_preview(detailed, prompt, extra_pnginfo, prefix_base="FNDetailer")
        return {"ui": {"images": preview}, "result": (detailed, empty_mask)}

    # ── preview helper ───────────────────────────────────────────────
    def _save_preview(self, images, prompt, extra_pnginfo, prefix_base="FNDetailer"):
        prefix = prefix_base + self.prefix_append
        folder, fname, counter, subfolder, _ = folder_paths.get_save_image_path(
            prefix,
            self.output_dir,
            images.shape[2],
            images.shape[1],
        )

        results = []
        for idx in range(images.shape[0]):
            arr = (255.0 * images[idx].cpu().numpy()).clip(0, 255).astype(np.uint8)
            if arr.ndim == 3 and arr.shape[2] == 1:
                arr = np.repeat(arr, 3, axis=2)
            img = Image.fromarray(arr)

            meta = None
            if not args.disable_metadata:
                meta = PngInfo()
                if prompt is not None:
                    meta.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo is not None:
                    for k in extra_pnginfo:
                        meta.add_text(k, json.dumps(extra_pnginfo[k]))

            file = f"{fname}_{counter:05}_.png"
            img.save(
                os.path.join(folder, file),
                pnginfo=meta,
                compress_level=self.compress_level,
            )
            results.append(
                {"filename": file, "subfolder": subfolder, "type": self.type}
            )
            counter += 1

        return results
