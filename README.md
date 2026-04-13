<p align="center">
  <img src="img/mascot.png" alt="FrotszNeeko Mascot" width="200"/>
</p>

<h1 align="center">🔹 FrotszNeeko Nodes</h1>

<p align="center">
  <b>All-in-one custom nodes for ComfyUI — built for bulk generation workflows</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/ComfyUI-Custom_Nodes-blue?style=for-the-badge" alt="ComfyUI"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT"/>
  <img src="https://img.shields.io/badge/Nodes-7-cyan?style=for-the-badge" alt="7 Nodes"/>
</p>

---

I mass generate AI content and got tired of messy workflows with 30+ nodes doing simple things. So I built these all-in-one nodes to keep things clean and fast — going from **~40 nodes down to ~7** while keeping full control. If you're doing bulk generation, these should save you a lot of time.

## ✨ Highlights

- 🎨 **Cyan neon theme** — all nodes have a custom dark teal look that stands out
- 📄 **Prompt From File** — reads prompts from `.txt`, auto-cycles through them, resolves wildcards, loads LoRAs inline
- ⚡ **All-in-one KSampler** — built-in empty latent, live preview, upscaler, and detailer toggle slots
- 👁️ **One-node Face Detailer** — replaces 3+ Impact Pack nodes with a single node
- 🔧 **BREAK & bracket support** — `BREAK` keyword and `[de-emphasis]` brackets work everywhere
- 🎛️ **Organized UI** — collapsible widget sections so you can actually find what you need

---

## 📦 Installation

### Option 1: ComfyUI Manager (Recommended)
Search for **FrotszNeeko** in ComfyUI Manager and click Install.

### Option 2: Git Clone
```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/FrotszNeeko/comfyui-frotszneeko-nodes.git
```

### Option 3: Download ZIP
Download and extract into `ComfyUI/custom_nodes/comfyui-frotszneeko-nodes/`.

After installing, **restart ComfyUI**. All nodes appear under **FrotszNeeko 🔹** in the node menu.

### Dependencies

This pack has **no hard dependencies** on other custom node packs. Everything is self-contained.

| Package | Required? | What for |
|---|---|---|
| `ultralytics` | Only for Face Detailer | YOLO face/body detection models |
| `opencv-python` | Optional | Better mask dilation (falls back to numpy if missing) |

If you use the Face Detailer, install ultralytics:
```bash
pip install ultralytics
```

You'll also need Ultralytics detection models (`.pt` files) in `ComfyUI/models/ultralytics/bbox/` or `ComfyUI/models/ultralytics/segm/`. Any YOLO model works — face detection, person detection, etc. If you already have Impact Pack installed, your existing models work automatically.

---

## 🔹 Nodes

### FN Prompt From File (All-in-One)

The brain of bulk generation workflows. Reads prompts from a `.txt` file and handles everything in one node.

| Feature | Description |
|---|---|
| **Line Selection** | `auto_cycle` (advances each run), `sequential` (seed-based), `random`, `ping_pong` |
| **Auto-Cycle** | Each run = next line in order. New queue always starts from line 1 |
| **Wildcards** | `__tag__` syntax — reads from a `wildcards/` folder |
| **Inline LoRAs** | `<lora:name:weight>` tags in your prompt — auto-loaded and applied |
| **Checkpoint** | Optional built-in checkpoint loader — no separate node needed |
| **CLIP Skip** | Built-in `clip_skip` parameter (default 1, set to 2 for anime models) |
| **BREAK** | Splits prompt into separate 77-token conditioning chunks |
| **Detailer CLIP** | Extra `detailer_clip` output — clean CLIP without LoRA patches for Face Detailer |

**Outputs:** `MODEL`, `CLIP`, `detailer_clip`, `VAE`, `CONDITIONING`, `processed_prompt`, `raw_prompt`, `line_number`

<details>
<summary>💡 Prompt file format</summary>

```
masterpiece, best quality, 1girl, red dress, garden, flowers
masterpiece, best quality, 1girl, blue dress, beach, sunset <lora:add_detail:0.8>
masterpiece, best quality, 1boy, suit, office, __expression__
```

Each line is one prompt. Empty lines are skipped. LoRA tags are extracted and applied automatically.
</details>

---

### FN KSampler Preview

The main workhorse. Full KSampler with extras built in.

| Feature | Description |
|---|---|
| **Built-in Latent** | Width/height/batch controls — no `EmptyLatentImage` node needed |
| **Live Preview** | Per-node preview method: `auto`, `latent2rgb`, `taesd`, `vae_decoded_only`, `none` |
| **Upscaler** | Optional model upscaler (ESRGAN, etc.) — applied after generation |
| **Detailer Toggles** | 4 named toggle slots to enable/disable downstream Face Detailers |
| **Organized UI** | Collapsible sections: Sampling, Latent Size, Preview, Upscaler, Detailers |

**Outputs:** `LATENT`, `IMAGE`, `detail_pipe`

> The `detail_pipe` output connects to FN Face Detailer nodes. Name your detailers (e.g. "Eyes", "Face") and toggle them on/off from the KSampler without rewiring.

---

### FN Face Detailer

Automatic face/feature detection and inpainting. Replaces the entire Impact Pack pipeline (`UltralyticsDetectorProvider` → `BBOX Detector` → `Detailer`) in **one node**.

| Feature | Description |
|---|---|
| **Detection** | Threshold, dilation, crop factor, drop size — all configurable |
| **Sampling** | Full sampler controls (seed, steps, cfg, sampler, scheduler, denoise) |
| **Inpainting** | Feather, noise mask, force inpaint, noise mask feather |
| **Toggle Control** | Name-based enable/disable via `detail_pipe` from KSampler |
| **Wildcard Spec** | Optional text prompt override for the detailer pass |
| **Preview** | Built-in preview of the detailed result |

**Outputs:** `IMAGE`

> Set the `name` to match a toggle slot in FN KSampler Preview (e.g. "Eyes"). The detailer only runs when its toggle is enabled.

---

### FN CLIP Dual Encode

Two text areas in one node — positive on top, negative on bottom.

| Feature | Description |
|---|---|
| **Dual Output** | Positive and negative conditioning from a single node |
| **BREAK** | Supported in both positive and negative prompts |
| **[Brackets]** | `[word]` de-emphasis (÷1.1 weight) — not natively supported by ComfyUI |
| **Negative CLIP** | Optional separate CLIP input for negative encoding (e.g. LoRA-free CLIP) |

**Outputs:** `positive CONDITIONING`, `negative CONDITIONING`, `CLIP`

---

### FN CLIP Text Encode (Advanced)

Single-text CLIP encoder with extra features.

| Feature | Description |
|---|---|
| **BREAK** | Splits prompt into separate 77-token chunks |
| **[Brackets]** | `[word]` → `(word:0.9091)` de-emphasis conversion |
| **Standard Weights** | `(word)`, `((word))`, `(word:1.5)` — all work natively |

**Outputs:** `CONDITIONING`

---

### FN Checkpoint Loader

Clean checkpoint loader, consistent with the pack's theme.

**Outputs:** `MODEL`, `CLIP`, `VAE`

---

### FN Image Saver

Saves images with full control over format and naming.

| Feature | Description |
|---|---|
| **Formats** | PNG, JPEG, WebP |
| **Quality** | Adjustable quality slider (1-100) |
| **Naming** | Custom prefix + optional timestamp |
| **Subfolder** | Custom output subfolder |
| **Metadata** | Full workflow metadata embedded (PNG) |
| **Preview** | Built-in preview of saved images |
| **Passthrough** | `IMAGE` output for chaining |

---

## 🔌 Typical Workflow

A complete generation + face detail pipeline with just **5 nodes**:

```
FN Prompt From File → FN CLIP Dual Encode → FN KSampler Preview → FN Face Detailer → FN Image Saver
```

| Node | Replaces |
|---|---|
| FN Prompt From File | Load Line From File + Extract LoRA + Lora Loader + CLIPSetLastLayer + Checkpoint Loader |
| FN CLIP Dual Encode | 2× CLIPTextEncode |
| FN KSampler Preview | EmptyLatentImage + KSampler + PreviewImage |
| FN Face Detailer | UltralyticsProvider + BBOX Detector + SEGS Merge + DetailerForEach |
| FN Image Saver | SaveImage |

**~12 nodes → 5 nodes.** Same results, cleaner workflow.

---

## ⚙️ Weight Syntax Reference

All CLIP encoding nodes in this pack support:

| Syntax | Effect | Example |
|---|---|---|
| `(word)` | Weight × 1.1 | `(masterpiece)` → 1.1 |
| `((word))` | Weight × 1.21 | `((detailed))` → 1.21 |
| `(word:1.5)` | Explicit weight | `(eyes:1.4)` → 1.4 |
| `[word]` | Weight ÷ 1.1 | `[blurry]` → 0.909 |
| `BREAK` | New 77-token chunk | `prompt1 BREAK prompt2` |

> **Note:** `(word)` and `(word:weight)` are handled by ComfyUI's native tokenizer. `[brackets]` and `BREAK` are added by this node pack.

---

## 🎨 Theme

All nodes use a custom **cyan neon** dark theme that's easy to spot in your workflow:

- **Title bar:** Dark teal (`#00363A`)
- **Body:** Deep dark (`#0C1B1E`)
- **Accent:** Cyan highlights

---

## ❓ FAQ

<details>
<summary><b>Do these nodes produce the same results as standard ComfyUI nodes?</b></summary>

Yes. The sampling and CLIP encoding logic is identical to ComfyUI's built-in nodes. Same seed + same parameters = same output. We use `comfy.sample.sample()` and `clip.encode_from_tokens_scheduled()` directly — no custom math.
</details>

<details>
<summary><b>Do I need Impact Pack installed?</b></summary>

**No.** The Face Detailer is fully self-contained — it reimplements the entire detection and detailing pipeline internally. You just need the `ultralytics` pip package and YOLO model files (`.pt`). If you already have Impact Pack installed, the same model files will work automatically.
</details>

<details>
<summary><b>What's the `detailer_clip` output on Prompt From File?</b></summary>

It's a clean CLIP model **without LoRA patches**. Some workflows encode the negative prompt with an unpatched CLIP for better results. Connect it to the `negative_clip` input on FN CLIP Dual Encode if you want this behavior.
</details>

<details>
<summary><b>What's <code>auto_cycle</code> mode?</b></summary>

Every run in a batch uses the next line: run 1 = line 1, run 2 = line 2, run 3 = line 3, then loops back. When you start a **new queue** (cancel all and re-queue, or after a batch finishes), it always resets to **line 1**. If you cancel just one run mid-batch, the next queued run picks the next line normally.
</details>

---

## 📄 License

MIT — do whatever you want with it.

---

<p align="center">
  <img src="img/mascot.png" alt="FrotszNeeko" width="80"/>
  <br/>
  <sub>Made with ❤️ by FrotszNeeko</sub>
</p>
