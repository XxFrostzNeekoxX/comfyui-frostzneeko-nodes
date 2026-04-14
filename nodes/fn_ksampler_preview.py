"""
FN KSampler Preview 🔹
Full KSampler with:
  • Built-in empty latent (width / height / batch — no EmptyLatentImage needed)
  • Per-node preview method selector (auto / latent2rgb / taesd / vae_decoded_only / none)
    → Forces the preview method BEFORE sampling so you see live denoising progress
    → Restores the global setting after sampling finishes
  • Optional model upscaler
  • Named toggle slots for downstream FN Face Detailer nodes

┌──────────────────────────────────────────────────────────────────────┐
│  Preview = LIVE denoising progress (step by step) + final raw gen   │
│  IMAGE output = upscaled image (if enabled) or raw                  │
│  detail_pipe  = toggle states for downstream FN Face Detailers      │
└──────────────────────────────────────────────────────────────────────┘
"""

import json
import os
import random

import numpy as np
import torch
from PIL import Image
from PIL.PngImagePlugin import PngInfo

import comfy.sample
import comfy.samplers
import comfy.utils
from comfy.cli_args import args

try:
    import comfy.model_management as model_management
except ImportError:
    model_management = None

try:
    import latent_preview as _latent_preview_module
except ImportError:
    try:
        from comfy import latent_preview as _latent_preview_module
    except ImportError:
        _latent_preview_module = None

try:
    from spandrel import ModelLoader as _SpandrelLoader
except ImportError:
    _SpandrelLoader = None

import folder_paths

# ── Preview method helpers (inspired by Efficiency Nodes approach) ───
# These let us force a specific preview method per-node, then restore.

def _get_current_preview_method():
    """Read the current global preview method."""
    return args.preview_method


def _force_preview_method(method_str: str):
    """
    Temporarily override the global preview method.
    Accepts: 'auto', 'latent2rgb', 'taesd', 'none', 'vae_decoded_only'
    """
    if _latent_preview_module is None:
        return

    lpm = _latent_preview_module.LatentPreviewMethod

    mapping = {
        "auto":             lpm.Auto,
        "latent2rgb":       lpm.Latent2RGB,
        "taesd":            lpm.TAESD,
        "none":             lpm.NoPreviews,
        "vae_decoded_only": lpm.NoPreviews,   # we handle this ourselves
    }

    args.preview_method = mapping.get(method_str, lpm.Auto)


def _restore_preview_method(original):
    """Put back the original global preview method."""
    args.preview_method = original


# ── upscale model cache ─────────────────────────────────────────────
_upscale_cache: dict = {}


def _load_upscale_model(name: str):
    """Load and cache an upscale model via spandrel."""
    if name in _upscale_cache:
        return _upscale_cache[name]

    if _SpandrelLoader is None:
        raise ImportError(
            "[FrostzNeeko] 'spandrel' library is required for upscaling.  "
            "It should be bundled with ComfyUI."
        )

    path = folder_paths.get_full_path("upscale_models", name)
    if path is None:
        raise FileNotFoundError(f"[FrostzNeeko] Upscale model not found: {name}")

    sd = comfy.utils.load_torch_file(path, safe_load=True)

    # Handle ESRGAN module prefix
    if "module.layers.0.residual_group.body.0.rdb1.conv1.weight" in sd:
        sd = comfy.utils.state_dict_prefix_replace(sd, {"module.": ""})

    up_model = _SpandrelLoader().load_from_state_dict(sd).eval()
    _upscale_cache[name] = up_model
    print(f"[FrostzNeeko] ✅ Loaded upscale model: {name}")
    return up_model


def _apply_upscale(up_model, image: torch.Tensor) -> torch.Tensor:
    """Upscale ``image`` [B,H,W,C] using a spandrel model. Tiled for VRAM safety."""
    device = model_management.get_torch_device()

    memory_required = model_management.module_size(up_model.model)
    memory_required += (
        (512 * 512 * 3)
        * image.element_size()
        * max(up_model.scale, 1.0)
        * 384.0
    )
    memory_required += image.nelement() * image.element_size()
    model_management.free_memory(memory_required, device)

    up_model.to(device)
    in_img = image.movedim(-1, -3).to(device)  # [B, C, H, W]

    tile = 512
    overlap = 32
    oom = True

    while oom:
        try:
            steps = in_img.shape[0] * comfy.utils.get_tiled_scale_steps(
                in_img.shape[3], in_img.shape[2],
                tile_x=tile, tile_y=tile, overlap=overlap,
            )
            pbar = comfy.utils.ProgressBar(steps)
            s = comfy.utils.tiled_scale(
                in_img,
                lambda a: up_model(a),
                tile_x=tile,
                tile_y=tile,
                overlap=overlap,
                upscale_amount=up_model.scale,
                pbar=pbar,
            )
            oom = False
        except model_management.OOM_EXCEPTION:
            tile //= 2
            if tile < 128:
                raise

    up_model.to("cpu")
    return torch.clamp(s.movedim(-3, -1), min=0, max=1.0)


# ═════════════════════════════════════════════════════════════════════


class FNKSamplerPreview:

    def __init__(self):
        self.output_dir = folder_paths.get_temp_directory()
        self.type = "temp"
        self.prefix_append = "_fnksp_" + "".join(
            random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(5)
        )
        self.compress_level = 1

    @classmethod
    def INPUT_TYPES(cls):
        # upscale models
        up_models = folder_paths.get_filename_list("upscale_models")
        up_list = ["none"] + up_models

        return {
            "required": {
                "model": ("MODEL",),
                "vae": ("VAE",),
                "seed": (
                    "INT",
                    {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF},
                ),
                "steps": ("INT", {"default": 20, "min": 1, "max": 10000}),
                "cfg": (
                    "FLOAT",
                    {"default": 7.0, "min": 0.0, "max": 100.0,
                     "step": 0.1, "round": 0.01},
                ),
                "sampler_name": (comfy.samplers.KSampler.SAMPLERS,),
                "scheduler": (comfy.samplers.KSampler.SCHEDULERS,),
                "positive": ("CONDITIONING",),
                "negative": ("CONDITIONING",),
                "denoise": (
                    "FLOAT",
                    {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01},
                ),
                # ── built-in latent size ─────────────────────────────
                "width": (
                    "INT",
                    {"default": 1024, "min": 64, "max": 8192, "step": 8},
                ),
                "height": (
                    "INT",
                    {"default": 1024, "min": 64, "max": 8192, "step": 8},
                ),
                "batch_size": (
                    "INT",
                    {"default": 1, "min": 1, "max": 64},
                ),
                # ── per-node preview control ─────────────────────────
                "preview_method": (
                    ["auto", "latent2rgb", "taesd", "vae_decoded_only", "none"],
                    {"default": "auto"},
                ),
            },
            "optional": {
                # ── external latent (overrides width/height) ─────────
                "latent_image": ("LATENT",),
                # ── upscaler ─────────────────────────────────────────
                "upscale_model_name": (up_list, {"default": "none"}),
                # ── detailer toggle slots ────────────────────────────
                "detailer_1_name": ("STRING", {"default": ""}),
                "detailer_1_enabled": ("BOOLEAN", {"default": False}),
                "detailer_2_name": ("STRING", {"default": ""}),
                "detailer_2_enabled": ("BOOLEAN", {"default": False}),
                "detailer_3_name": ("STRING", {"default": ""}),
                "detailer_3_enabled": ("BOOLEAN", {"default": False}),
                "detailer_4_name": ("STRING", {"default": ""}),
                "detailer_4_enabled": ("BOOLEAN", {"default": False}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("LATENT", "IMAGE", "FN_DETAIL_PIPE")
    RETURN_NAMES = ("latent", "image", "detail_pipe")
    FUNCTION = "sample_and_preview"
    OUTPUT_NODE = True
    CATEGORY = "FrostzNeeko 🔹/Sampling"

    # ─────────────────────────────────────────────────────────────────
    def sample_and_preview(
        self,
        model,
        vae,
        seed,
        steps,
        cfg,
        sampler_name,
        scheduler,
        positive,
        negative,
        denoise=1.0,
        # built-in latent
        width=1024,
        height=1024,
        batch_size=1,
        # preview
        preview_method="auto",
        # optional latent override
        latent_image=None,
        # upscaler
        upscale_model_name="none",
        # toggles
        detailer_1_name="",
        detailer_1_enabled=False,
        detailer_2_name="",
        detailer_2_enabled=False,
        detailer_3_name="",
        detailer_3_enabled=False,
        detailer_4_name="",
        detailer_4_enabled=False,
        # hidden
        prompt=None,
        extra_pnginfo=None,
    ):
        # ══════════════  BUILD / USE LATENT  ═════════════════════════
        if latent_image is not None:
            latent = latent_image.copy()
        else:
            # Generate empty latent from width/height/batch_size
            latent = {
                "samples": torch.zeros(
                    [batch_size, 4, height // 8, width // 8],
                    device=comfy.model_management.intermediate_device(),
                )
            }

        latent_samples = latent["samples"]

        if hasattr(comfy.sample, "fix_empty_latent_channels"):
            latent_samples = comfy.sample.fix_empty_latent_channels(
                model, latent_samples
            )

        batch_inds = latent.get("batch_index", None)
        noise = comfy.sample.prepare_noise(latent_samples, seed, batch_inds)
        noise_mask = latent.get("noise_mask", None)

        # ══════════  FORCE PREVIEW METHOD (before sampling)  ═════════
        saved_preview_method = _get_current_preview_method()
        _force_preview_method(preview_method)

        try:
            # Build the live callback now (AFTER we forced the method)
            callback = None
            if _latent_preview_module is not None and preview_method != "none":
                try:
                    callback = _latent_preview_module.prepare_callback(model, steps)
                except Exception:
                    pass

            disable_pbar = not comfy.utils.PROGRESS_BAR_ENABLED

            # ══════════════════════════  SAMPLING  ═══════════════════════
            # Match common_ksampler() exactly — pass every parameter it does
            samples = comfy.sample.sample(
                model, noise, steps, cfg,
                sampler_name, scheduler,
                positive, negative, latent_samples,
                denoise=denoise,
                disable_noise=False,
                start_step=None,
                last_step=None,
                force_full_denoise=False,
                noise_mask=noise_mask,
                callback=callback,
                disable_pbar=disable_pbar,
                seed=seed,
            )
        finally:
            # ══════════  RESTORE PREVIEW METHOD (always)  ════════════
            _restore_preview_method(saved_preview_method)

        out_latent = latent.copy()
        out_latent["samples"] = samples

        # ══════════════════════════  DECODE  ═════════════════════════
        decoded = vae.decode(samples)

        # ════════════════  SAVE PREVIEW (final raw)  ═════════════════
        # For "vae_decoded_only" we skip the live preview but still show
        # the final decoded image, which gives a nice result view.
        preview_ui: dict = {"images": []}
        if preview_method != "none":
            prefix = "FNPreview" + self.prefix_append
            folder, fname, counter, subfolder, _ = folder_paths.get_save_image_path(
                prefix, self.output_dir, decoded.shape[2], decoded.shape[1],
            )

            results = []
            for idx in range(decoded.shape[0]):
                arr = (255.0 * decoded[idx].cpu().numpy()).clip(0, 255).astype(np.uint8)
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

            preview_ui = {"images": results}

        # ══════════════════════  UPSCALE  ════════════════════════════
        output_image = decoded

        if upscale_model_name and upscale_model_name != "none":
            print(f"[FrostzNeeko] 🔎 Upscaling with {upscale_model_name}…")
            up_model = _load_upscale_model(upscale_model_name)
            output_image = _apply_upscale(up_model, decoded)
            print(
                f"[FrostzNeeko] ✅ Upscaled: "
                f"{decoded.shape[2]}×{decoded.shape[1]} → "
                f"{output_image.shape[2]}×{output_image.shape[1]}"
            )

        # ══════════════════  BUILD DETAIL PIPE  ══════════════════════
        toggles: dict[str, bool] = {}
        for name, enabled in [
            (detailer_1_name, detailer_1_enabled),
            (detailer_2_name, detailer_2_enabled),
            (detailer_3_name, detailer_3_enabled),
            (detailer_4_name, detailer_4_enabled),
        ]:
            if name and name.strip():
                toggles[name.strip()] = bool(enabled)

        detail_pipe = {"toggles": toggles}

        if toggles:
            enabled_list = [n for n, v in toggles.items() if v]
            disabled_list = [n for n, v in toggles.items() if not v]
            if enabled_list:
                print(f"[FrostzNeeko] 🎯 Detailers ON:  {', '.join(enabled_list)}")
            if disabled_list:
                print(f"[FrostzNeeko] ⏭️  Detailers OFF: {', '.join(disabled_list)}")

        return {
            "ui": preview_ui,
            "result": (out_latent, output_image, detail_pipe),
        }
