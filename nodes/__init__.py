"""
FrostzNeeko Nodes — nodes package init
Imports all node classes and builds the ComfyUI registration mappings.
"""

from .fn_prompt_from_file import FNPromptFromFile
from .fn_clip_dual import FNClipDualEncode
from .fn_clip_advanced import FNClipAdvanced
from .fn_checkpoint_loader import FNCheckpointLoader
from .fn_ksampler_preview import FNKSamplerPreview
from .fn_face_detailer import FNFaceDetailer
from .fn_image_saver import FNImageSaver


NODE_CLASS_MAPPINGS = {
    "FNPromptFromFile": FNPromptFromFile,
    "FNClipDualEncode": FNClipDualEncode,
    "FNClipAdvanced": FNClipAdvanced,
    "FNCheckpointLoader": FNCheckpointLoader,
    "FNKSamplerPreview": FNKSamplerPreview,
    "FNFaceDetailer": FNFaceDetailer,
    "FNImageSaver": FNImageSaver,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FNPromptFromFile": "FN Prompt From File (All-in-One) 🔹",
    "FNClipDualEncode": "FN CLIP Dual Encode 🔹",
    "FNClipAdvanced": "FN CLIP Text Encode (Advanced) 🔹",
    "FNCheckpointLoader": "FN Checkpoint Loader 🔹",
    "FNKSamplerPreview": "FN Supreme KSampler 🔹",
    "FNFaceDetailer": "FN Face Detailer 🔹",
    "FNImageSaver": "FN Image Saver 🔹",
}
