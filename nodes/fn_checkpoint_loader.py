"""
FN Checkpoint Loader
Loads a Stable Diffusion checkpoint (.safetensors / .ckpt) and
returns MODEL, CLIP, and VAE — the three essentials for any workflow.
"""

import comfy.sd
import folder_paths


class FNCheckpointLoader:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "ckpt_name": (folder_paths.get_filename_list("checkpoints"),),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "VAE")
    RETURN_NAMES = ("model", "clip", "vae")
    FUNCTION = "load_checkpoint"
    CATEGORY = "FrotszNeeko 🔹/Loaders"

    def load_checkpoint(self, ckpt_name):
        ckpt_path = folder_paths.get_full_path("checkpoints", ckpt_name)
        if ckpt_path is None:
            raise FileNotFoundError(
                f"[FrotszNeeko] Checkpoint not found: {ckpt_name}"
            )

        out = comfy.sd.load_checkpoint_guess_config(
            ckpt_path,
            output_vae=True,
            output_clip=True,
            embedding_directory=folder_paths.get_folder_paths("embeddings"),
        )

        model, clip, vae = out[:3]
        print(f"[FrotszNeeko] ✅ Loaded checkpoint: {ckpt_name}")

        return (model, clip, vae)
