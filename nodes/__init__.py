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
from .fn_metadata_reader import FNMetadataReader


NODE_CLASS_MAPPINGS = {
    "FNPromptFromFile": FNPromptFromFile,
    "FNClipDualEncode": FNClipDualEncode,
    "FNClipAdvanced": FNClipAdvanced,
    "FNCheckpointLoader": FNCheckpointLoader,
    "FNKSamplerPreview": FNKSamplerPreview,
    "FNFaceDetailer": FNFaceDetailer,
    "FNImageSaver": FNImageSaver,
    "FNMetadataReader": FNMetadataReader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FNPromptFromFile": "FN Prompt From File (All-in-One) \U0001f539",
    "FNClipDualEncode": "FN CLIP Dual Encode \U0001f539",
    "FNClipAdvanced": "FN CLIP Text Encode (Advanced) \U0001f539",
    "FNCheckpointLoader": "FN Checkpoint Loader \U0001f539",
    "FNKSamplerPreview": "FN Supreme KSampler \U0001f539",
    "FNFaceDetailer": "FN Face Detailer \U0001f539",
    "FNImageSaver": "FN Image Saver \U0001f539",
    "FNMetadataReader": "FN Metadata Reader \U0001f539",
}
