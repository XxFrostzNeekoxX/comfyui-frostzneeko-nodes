"""
Shared utility functions for face detection and detailing.
Own implementation inspired by standard ComfyUI detection workflows:

  - YOLO inference for bbox / segmentation detection
  - Crop region calculation with configurable crop_factor
  - Mask construction in crop-region coordinates (post-crop)
  - Gaussian blur feathering for smooth paste-back
  - Sigma-based sampling with proper denoise step handling

Key details:
  • bbox from YOLO is (x1, y1, x2, y2) in xyxy format
  • segm masks handle aspect ratio mismatch between yolo output and original
  • dilation uses cv2.dilate with kernel (not simple pixel expansion)
  • crop_region is always [x1, y1, x2, y2] and crops with [y1:y2, x1:x2]
"""

import os
from collections import namedtuple

import numpy as np
import torch
import torch.nn.functional as F

import math

import comfy.sample
import comfy.samplers
import comfy.utils
import folder_paths

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import torchvision
except ImportError:
    torchvision = None

try:
    import latent_preview as _lp
except ImportError:
    try:
        from comfy import latent_preview as _lp
    except ImportError:
        _lp = None

# ── SEG namedtuple (matches Impact Pack exactly) ─────────────────────
SEG = namedtuple(
    "SEG",
    ["cropped_image", "cropped_mask", "confidence", "crop_region", "bbox", "label", "control_net_wrapper"],
    defaults=[None],
)

# ── Ensure ultralytics model dirs are registered ─────────────────────
_models_dir = folder_paths.models_dir
for _sub, _key in [
    (os.path.join("ultralytics", "bbox"), "ultralytics_bbox"),
    (os.path.join("ultralytics", "segm"), "ultralytics_segm"),
]:
    _full = os.path.join(_models_dir, _sub)
    os.makedirs(_full, exist_ok=True)
    if _key not in folder_paths.folder_names_and_paths:
        folder_paths.folder_names_and_paths[_key] = (
            [_full],
            folder_paths.supported_pt_extensions,
        )


# ── Detector model helpers ───────────────────────────────────────────

_detector_cache: dict = {}


def get_detector_model_list() -> list[str]:
    out: list[str] = []
    for key in ("ultralytics_bbox", "ultralytics_segm"):
        try:
            out.extend(folder_paths.get_filename_list(key))
        except Exception:
            pass
    return sorted(set(out)) or ["none"]


def load_detector(name: str):
    if name in _detector_cache:
        return _detector_cache[name]

    try:
        from ultralytics import YOLO
    except ImportError:
        raise ImportError(
            "[FrostzNeeko] 'ultralytics' not installed.  pip install ultralytics"
        )

    path = None
    for key in ("ultralytics_bbox", "ultralytics_segm"):
        try:
            p = folder_paths.get_full_path(key, name)
            if p and os.path.isfile(p):
                path = p
                break
        except Exception:
            continue

    if path is None:
        raise FileNotFoundError(f"[FrostzNeeko] Detector not found: {name}")

    model = YOLO(path)
    _detector_cache[name] = model
    print(f"[FrostzNeeko] ✅ Loaded detector: {name}")
    return model


# ── PIL ↔ tensor helpers ─────────────────────────────────────────────

def _tensor_to_pil(image_tensor):
    """Convert [1,H,W,C] or [H,W,C] tensor to PIL Image (RGB)."""
    from PIL import Image
    if image_tensor.ndim == 4:
        image_tensor = image_tensor.squeeze(0)
    arr = np.clip(255.0 * image_tensor.cpu().numpy(), 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


# ── YOLO inference (matching Impact Pack subcore.py) ─────────────────

def _inference_bbox(model, pil_image, confidence=0.3):
    """
    Run YOLO bbox detection on a PIL image.
    Returns: [labels, bboxes, segms, confidences]
      - bboxes: numpy arrays [x1, y1, x2, y2]
      - segms: boolean masks (rectangular, from bbox)
    Matches Impact Pack's inference_bbox exactly.
    """
    pred = model(pil_image, conf=confidence, verbose=False)

    bboxes = pred[0].boxes.xyxy.cpu().numpy()
    cv2_image = np.array(pil_image)
    if len(cv2_image.shape) == 3:
        cv2_gray = cv2_image[:, :, :1].squeeze(-1)  # Quick grayscale
    else:
        cv2_gray = cv2_image

    segms = []
    for x0, y0, x1, y1 in bboxes:
        mask = np.zeros(cv2_gray.shape[:2], np.uint8)
        if cv2 is not None:
            cv2.rectangle(mask, (int(x0), int(y0)), (int(x1), int(y1)), 255, -1)
        else:
            mask[int(y0):int(y1), int(x0):int(x1)] = 255
        segms.append(mask.astype(bool))

    n = bboxes.shape[0]
    if n == 0:
        return [[], [], [], []]

    results = [[], [], [], []]
    for i in range(n):
        results[0].append(pred[0].names[int(pred[0].boxes[i].cls.item())])
        results[1].append(bboxes[i])
        results[2].append(segms[i])
        results[3].append(pred[0].boxes[i].conf.cpu().numpy().item())

    return results


def _inference_segm(model, pil_image, confidence=0.3):
    """
    Run YOLO segmentation detection on a PIL image.
    Returns: [labels, bboxes, segms, confidences]
      - segms: float32 masks at original image resolution
    Matches Impact Pack's inference_segm exactly, including aspect ratio gap handling.
    """
    pred = model(pil_image, conf=confidence, verbose=False)

    bboxes = pred[0].boxes.xyxy.cpu().numpy()
    n = bboxes.shape[0]
    if n == 0:
        return [[], [], [], []]

    # masks.data may be None when n == 0
    segms_raw = pred[0].masks.data.cpu().numpy()

    h_segms = segms_raw.shape[1]
    w_segms = segms_raw.shape[2]
    h_orig = pil_image.size[1]  # PIL: (w, h)
    w_orig = pil_image.size[0]
    ratio_segms = h_segms / w_segms
    ratio_orig = h_orig / w_orig

    # Handle aspect ratio mismatch (exactly like Impact Pack)
    if ratio_segms == ratio_orig:
        h_gap = 0
        w_gap = 0
    elif ratio_segms > ratio_orig:
        h_gap = int((ratio_segms - ratio_orig) * h_segms)
        w_gap = 0
    else:
        h_gap = 0
        ratio_segms_inv = w_segms / h_segms
        ratio_orig_inv = w_orig / h_orig
        w_gap = int((ratio_segms_inv - ratio_orig_inv) * w_segms)

    results = [[], [], [], []]
    for i in range(n):
        results[0].append(pred[0].names[int(pred[0].boxes[i].cls.item())])
        results[1].append(bboxes[i])

        mask = torch.from_numpy(segms_raw[i])
        mask = mask[h_gap:mask.shape[0] - h_gap, w_gap:mask.shape[1] - w_gap]

        scaled_mask = F.interpolate(
            mask.unsqueeze(0).unsqueeze(0),
            size=(h_orig, w_orig),
            mode="bilinear",
            align_corners=False,
        )
        scaled_mask = scaled_mask.squeeze().squeeze()

        results[2].append(scaled_mask.numpy())
        results[3].append(pred[0].boxes[i].conf.cpu().numpy().item())

    return results


# ── Segmask creation (matching Impact Pack subcore.py) ───────────────

def _create_segmasks(results):
    """
    Convert detection results to [(bbox, mask_float32, confidence), ...]
    """
    bboxes = results[1]
    segms = results[2]
    confidences = results[3]

    out = []
    for i in range(len(segms)):
        item = (bboxes[i], segms[i].astype(np.float32), confidences[i])
        out.append(item)
    return out


# ── Mask dilation (matching Impact Pack subpack utils.py) ────────────

def _dilate_masks(segmasks, dilation_factor):
    """Dilate masks using cv2 kernel (matching Impact Pack exactly)."""
    if dilation_factor == 0:
        return segmasks

    dilated = []
    kernel = np.ones((abs(dilation_factor), abs(dilation_factor)), np.uint8)

    for i in range(len(segmasks)):
        mask = segmasks[i][1]

        # Ensure mask is uint8 for cv2
        if mask.dtype != np.uint8:
            mask_u8 = (mask * 255).clip(0, 255).astype(np.uint8)
        else:
            mask_u8 = mask

        if cv2 is not None:
            if dilation_factor > 0:
                dilated_mask = cv2.dilate(mask_u8, kernel, iterations=1)
            else:
                dilated_mask = cv2.erode(mask_u8, kernel, iterations=1)
            # Convert back to float32
            dilated_mask = dilated_mask.astype(np.float32) / 255.0
        else:
            # Fallback without cv2: use our simple approach
            dilated_mask = mask

        item = (segmasks[i][0], dilated_mask, segmasks[i][2])
        dilated.append(item)

    return dilated


def _dilate_single_mask(mask_f32, dilation_factor):
    """Dilate or erode a single float32 mask. Returns float32."""
    if dilation_factor == 0:
        return mask_f32

    kernel = np.ones((abs(dilation_factor), abs(dilation_factor)), np.uint8)
    mask_u8 = (mask_f32 * 255).clip(0, 255).astype(np.uint8)

    if cv2 is not None:
        if dilation_factor > 0:
            result = cv2.dilate(mask_u8, kernel, iterations=1)
        else:
            result = cv2.erode(mask_u8, kernel, iterations=1)
        return result.astype(np.float32) / 255.0
    else:
        return mask_f32


# ── Crop helpers (matching Impact Pack subpack utils.py) ─────────────

def _normalize_region(limit, startp, size):
    """Matches Impact Pack exactly."""
    if startp < 0:
        new_endp = min(limit, size)
        new_startp = 0
    elif startp + size > limit:
        new_startp = max(0, limit - size)
        new_endp = limit
    else:
        new_startp = startp
        new_endp = min(limit, startp + size)
    return int(new_startp), int(new_endp)


def _make_crop_region(w, h, bbox, crop_factor):
    """
    Compute crop region from bbox using crop_factor.
    bbox = (y1, x1, y2, x2) — Impact Pack format
    Returns: [x1, y1, x2, y2] as crop_region
    Matches Impact Pack exactly.
    """
    x1 = bbox[0]
    y1 = bbox[1]
    x2 = bbox[2]
    y2 = bbox[3]

    bbox_w = x2 - x1
    bbox_h = y2 - y1

    crop_w = bbox_w * crop_factor
    crop_h = bbox_h * crop_factor

    kernel_x = x1 + bbox_w / 2
    kernel_y = y1 + bbox_h / 2

    new_x1 = int(kernel_x - crop_w / 2)
    new_y1 = int(kernel_y - crop_h / 2)

    new_x1, new_x2 = _normalize_region(w, new_x1, crop_w)
    new_y1, new_y2 = _normalize_region(h, new_y1, crop_h)

    return [new_x1, new_y1, new_x2, new_y2]


def _crop_ndarray2(npimg, crop_region):
    """Crop a 2D numpy array with crop_region [x1, y1, x2, y2]."""
    x1, y1, x2, y2 = crop_region
    return npimg[y1:y2, x1:x2]


def _crop_tensor4(image, crop_region):
    """Crop a 4D tensor [N,H,W,C] with crop_region [x1, y1, x2, y2]."""
    x1, y1, x2, y2 = crop_region
    return image[:, y1:y2, x1:x2, :]


# ── Mask helpers (matching Impact Pack core.py / utils.py) ───────────

def _tensor_gaussian_blur_mask(mask, kernel_size, sigma=10.0):
    """
    Matching Impact Pack's tensor_gaussian_blur_mask exactly.
    input:  2D or 3D tensor mask
    output: [N, H, W, 1] NHWC mask with gaussian blur applied
    """
    if isinstance(mask, np.ndarray):
        mask = torch.from_numpy(mask)

    if mask.ndim == 2:
        mask = mask[None, ..., None]      # → [1, H, W, 1]
    elif mask.ndim == 3:
        mask = mask[..., None]            # → [N, H, W, 1]

    if kernel_size <= 0:
        return mask

    ks = kernel_size * 2 + 1

    shortest = min(mask.shape[1], mask.shape[2])
    if shortest <= ks:
        ks = int(shortest / 2)
        if ks % 2 == 0:
            ks += 1
        if ks < 3:
            return mask

    if torchvision is not None:
        m = mask[:, None, ..., 0]   # [N, 1, H, W]
        blurred = torchvision.transforms.GaussianBlur(kernel_size=ks, sigma=sigma)(m)
        return blurred[:, 0, ..., None]  # → [N, H, W, 1]
    else:
        m = mask.permute(0, 3, 1, 2)  # → [N, 1, H, W]
        r = kernel_size
        for _ in range(3):
            k = r * 2 + 1
            padded = F.pad(m, [r, r, r, r], mode="replicate")
            m = F.avg_pool2d(padded, kernel_size=k, stride=1, padding=0)
        return m.permute(0, 2, 3, 1)  # → [N, H, W, 1]


def _tensor_paste(image, patch, left_top, mask):
    """
    Matching Impact Pack's tensor_paste:
    Pastes patch onto image at (x, y) using mask for blending.
    image: [1, H, W, C]  (modified in-place)
    patch: [1, h, w, C]
    mask:  [1, h, w, 1]
    """
    x, y = left_top
    _, h1, w1, _ = image.shape
    _, h2, w2, _ = patch.shape

    w = min(w1, x + w2) - x
    h = min(h1, y + h2) - y

    if w <= 0 or h <= 0:
        return

    mask_r = mask[:, :h, :w, :]
    region1 = image[:, y:y+h, x:x+w, :]
    region2 = patch[:, :h, :w, :]

    image[:, y:y+h, x:x+w, :] = (1 - mask_r) * region1 + mask_r * region2


def _tensor_resize(image, w, h):
    """Resize [N,H,W,C] image using bilinear interpolation."""
    img = image.permute(0, 3, 1, 2)  # NCHW
    img = F.interpolate(img, size=(h, w), mode="bilinear", align_corners=False)
    return img.permute(0, 2, 3, 1)   # NHWC


def _resize_mask(mask, size):
    """Resize mask to (h, w). Input: [H,W] or [N,H,W]. Output: [N,H,W]."""
    if mask.ndim == 2:
        mask = mask.unsqueeze(0)
    m = mask.unsqueeze(1)  # [N,1,H,W]
    m = F.interpolate(m, size=size, mode="bilinear", align_corners=False)
    return m.squeeze(1)     # [N,H,W]


# ── SEGS detection (matching Impact Pack UltraBBoxDetector / UltraSegmDetector) ──

def _detect_segs(detector, image_tensor, threshold, dilation, crop_factor, drop_size=10, use_segm=False):
    """
    Full Impact Pack detection pipeline:
    1. Convert tensor to PIL
    2. Run inference (bbox or segm)
    3. Create segmasks
    4. Apply dilation
    5. Build SEG objects with crop_region + cropped_image + cropped_mask

    Returns: (shape, [SEG, ...])
    """
    pil_image = _tensor_to_pil(image_tensor)

    # Choose inference method
    if use_segm:
        detected_results = _inference_segm(detector, pil_image, threshold)
    else:
        detected_results = _inference_bbox(detector, pil_image, threshold)

    segmasks = _create_segmasks(detected_results)

    items = []
    h = image_tensor.shape[1]
    w = image_tensor.shape[2]

    for idx, (segmask_data, label) in enumerate(zip(segmasks, detected_results[0])):
        item_bbox = segmask_data[0]  # xyxy from YOLO
        confidence = segmask_data[2]

        x1, y1, x2, y2 = int(item_bbox[0]), int(item_bbox[1]), int(item_bbox[2]), int(item_bbox[3])

        if (x2 - x1) > drop_size and (y2 - y1) > drop_size:
            crop_region = _make_crop_region(w, h, item_bbox, crop_factor)
            cr_x1, cr_y1, cr_x2, cr_y2 = crop_region

            # Crop the image to the crop region
            cropped_image = _crop_tensor4(image_tensor, crop_region)

            # Build mask in crop-region coordinates (not from full image)
            # This ensures the mask aligns perfectly with the cropped image
            crop_h = cr_y2 - cr_y1
            crop_w = cr_x2 - cr_x1
            cropped_mask = np.zeros((crop_h, crop_w), dtype=np.float32)

            # Place the bbox rectangle relative to the crop region
            rel_y1 = max(0, y1 - cr_y1)
            rel_y2 = min(crop_h, y2 - cr_y1)
            rel_x1 = max(0, x1 - cr_x1)
            rel_x2 = min(crop_w, x2 - cr_x1)
            cropped_mask[rel_y1:rel_y2, rel_x1:rel_x2] = 1.0

            # Apply dilation to the cropped mask
            if dilation != 0:
                cropped_mask = _dilate_single_mask(cropped_mask, dilation)

            item = SEG(cropped_image, cropped_mask, confidence, crop_region, item_bbox, label, None)
            items.append(item)

    shape = (h, w)
    return shape, items


# ── enhance_detail (matching Impact Pack core.py) ────────────────────

def _enhance_detail(
    cropped_image,          # [1, crop_h, crop_w, C]  (the cropped region)
    model, vae,
    guide_size, guide_size_for_bbox, max_size,
    bbox,                   # (x1, y1, x2, y2) from YOLO xyxy
    seed, steps, cfg,
    sampler_name, scheduler,
    positive, negative,
    denoise,
    noise_mask,             # 2D or 3D mask, or None
    force_inpaint,
    noise_mask_feather=0,
    cycle=1,
):
    """
    Mirrors Impact Pack's core.enhance_detail():
    1. Determine upscale factor from guide_size
    2. Upscale the cropped image
    3. Encode to latent
    4. Apply noise_mask (feathered) to latent
    5. Sample
    6. Decode
    7. Downscale back to original crop size
    """

    if noise_mask is not None:
        noise_mask = _tensor_gaussian_blur_mask(noise_mask, noise_mask_feather)
        noise_mask = noise_mask.squeeze(3)  # → [1, H, W] or [H, W]

    h = cropped_image.shape[1]
    w = cropped_image.shape[2]

    bbox_w = bbox[2] - bbox[0]
    bbox_h = bbox[3] - bbox[1]

    # Calculate upscale factor
    if guide_size_for_bbox:
        upscale = guide_size / min(bbox_w, bbox_h) if min(bbox_w, bbox_h) > 0 else 1.0
    else:
        upscale = guide_size / min(w, h) if min(w, h) > 0 else 1.0

    new_w = int(w * upscale)
    new_h = int(h * upscale)

    if new_w > max_size or new_h > max_size:
        upscale *= max_size / max(new_w, new_h)
        new_w = int(w * upscale)
        new_h = int(h * upscale)

    if not force_inpaint:
        if upscale <= 1.0 or new_w == 0 or new_h == 0:
            print(f"[FrostzNeeko] ℹ️  skip (upscale={upscale:.2f})")
            return None
    else:
        if upscale <= 1.0 or new_w == 0 or new_h == 0:
            upscale = 1.0
            new_w = w
            new_h = h

    # Round to multiples of 8
    new_w = max(8, ((new_w + 7) // 8) * 8)
    new_h = max(8, ((new_h + 7) // 8) * 8)

    print(f"[FrostzNeeko]    upscale ({bbox_w:.0f}x{bbox_h:.0f}) | crop {w}x{h} × {upscale:.2f} → {new_w}x{new_h}")

    # Upscale the cropped image
    upscaled = _tensor_resize(cropped_image, new_w, new_h)

    # Encode to latent
    latent = vae.encode(upscaled[:, :, :, :3])

    if hasattr(comfy.sample, "fix_empty_latent_channels"):
        latent = comfy.sample.fix_empty_latent_channels(model, latent)

    # Build latent dict with noise_mask
    latent_dict = {"samples": latent}
    if noise_mask is not None:
        if noise_mask.ndim == 2:
            nm = noise_mask.unsqueeze(0)
        else:
            nm = noise_mask
        nm_resized = _resize_mask(nm, (new_h, new_w))
        latent_dict["noise_mask"] = nm_resized

    # Compute sigmas with proper denoise step calculation
    # When denoise < 1.0, we need more total sigmas and only sample a subset
    total_steps = math.floor(steps / denoise) if denoise > 0 and denoise < 1.0 else steps
    start_step = total_steps - steps

    model_sampling = model.get_model_object("model_sampling")
    full_sigmas = comfy.samplers.calculate_sigmas(model_sampling, scheduler, total_steps)

    # Slice sigmas for our denoise range
    sigmas = full_sigmas[start_step:]

    # Build sampler object
    sampler_obj = comfy.samplers.sampler_object(sampler_name)

    # Sample with cycles
    for c in range(cycle):
        noise = comfy.sample.prepare_noise(latent_dict["samples"], seed + c)

        cb = None
        if _lp is not None:
            try:
                cb = _lp.prepare_callback(model, len(sigmas) - 1)
            except Exception:
                pass

        latent_dict["samples"] = comfy.sample.sample_custom(
            model, noise, cfg, sampler_obj, sigmas,
            positive, negative, latent_dict["samples"],
            noise_mask=latent_dict.get("noise_mask"),
            callback=cb,
            disable_pbar=not comfy.utils.PROGRESS_BAR_ENABLED,
            seed=seed + c,
        )

    # Decode
    refined = vae.decode(latent_dict["samples"])

    if len(refined.shape) == 5:
        refined = refined.squeeze(0)

    # Downscale back to original crop size
    refined = _tensor_resize(refined, w, h).cpu()

    return refined


# ── Core face-detail pass ────────────────────────────────────────────

def run_face_detail(
    image: torch.Tensor,
    model, vae, positive, negative,
    detector_model_name: str,
    seed: int, steps: int, cfg: float,
    sampler_name: str, scheduler: str,
    denoise: float = 0.4,
    threshold: float = 0.5,
    dilation: int = 10,
    crop_factor: float = 3.0,
    feather: int = 5,
    guide_size: int = 512,
    guide_size_for: str = "bbox",
    max_size: int = 1024,
    noise_mask_enabled: bool = True,
    force_inpaint: bool = True,
    cycle: int = 1,
    noise_mask_feather: int = 20,
    drop_size: int = 10,
) -> torch.Tensor:
    """
    Detect regions and detail them using the exact Impact Pack pipeline:
      detect_segs → enhance_detail → tensor_paste
    """

    detector = load_detector(detector_model_name)
    image = image.clone()

    guide_size_for_bbox = (guide_size_for == "bbox")

    # Determine if model is bbox or segm type
    # Impact Pack checks model type; we'll try segm first, fall back to bbox
    has_segm = hasattr(detector, 'model') and hasattr(detector.model, 'task') and detector.model.task == 'segment'
    if not has_segm:
        # Also check by model name
        has_segm = 'segm' in detector_model_name.lower() or 'seg' in detector_model_name.lower()

    for b in range(image.shape[0]):
        single_image = image[b:b+1]

        # Detect using Impact Pack pipeline
        shape, segs = _detect_segs(
            detector, single_image, threshold, dilation, crop_factor,
            drop_size=drop_size, use_segm=has_segm,
        )

        if not segs:
            print(f"[FrostzNeeko] ℹ️  No detections in batch {b}")
            continue

        mode_label = "segm" if has_segm else "bbox"
        print(f"[FrostzNeeko] 🔍 {len(segs)} detection(s) [{mode_label}] in batch {b}")

        for i, seg in enumerate(segs):
            crop_region = seg.crop_region
            cr_x1, cr_y1, cr_x2, cr_y2 = crop_region

            # seg.cropped_image is already cropped to crop_region
            cropped_image = seg.cropped_image.clone()

            # seg.cropped_mask is the detection mask cropped to crop_region
            cropped_mask_np = seg.cropped_mask

            # Prepare noise mask (if enabled)
            noise_mask_for_detail = torch.from_numpy(cropped_mask_np).float() if noise_mask_enabled else None

            # Prepare paste mask: cropped_mask blurred with feather
            paste_mask_t = torch.from_numpy(cropped_mask_np).float()
            paste_mask = _tensor_gaussian_blur_mask(paste_mask_t, feather)
            # paste_mask is now [1, H, W, 1]

            # enhance_detail
            # bbox for upscale calculation: use the seg.bbox (YOLO xyxy)
            enhanced = _enhance_detail(
                cropped_image, model, vae,
                guide_size, guide_size_for_bbox, max_size,
                seg.bbox, seed + i, steps, cfg,
                sampler_name, scheduler,
                positive, negative,
                denoise,
                noise_mask_for_detail,
                force_inpaint,
                noise_mask_feather=noise_mask_feather,
                cycle=cycle,
            )

            if enhanced is None:
                continue

            # Paste back using Impact Pack's tensor_paste approach
            _tensor_paste(
                image[b:b+1],
                enhanced,
                (cr_x1, cr_y1),
                paste_mask,
            )

            conf_val = float(np.asarray(seg.confidence).flat[0])
            print(f"[FrostzNeeko]    ✅ Detection {i + 1} [{mode_label}] detailed (conf={conf_val:.2f})")

    return image
