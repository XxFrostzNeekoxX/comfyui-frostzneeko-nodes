**🌐 Language:**[English](README.md) • Português • Español • 中文 • 日本語 • 한국어



# 🔹 FrostzNeeko Nodes

**All-in-one custom nodes for ComfyUI — built for bulk generation workflows**



---

## 💬 Why I Made This

I run content on **Patreon**, **Pixiv**, **DeviantArt** and other platforms — which means I mass generate AI images every single day. When I first started with ComfyUI, every workflow I found online was a nightmare: **30, 40, sometimes 50+ nodes** just to do basic generation with a face fix. Spaghetti wires everywhere, impossible to debug, and nobody in the community was willing to help simplify things.

So I said screw it and built my own.

These nodes compress entire pipelines into single, clean blocks. What used to take **~40 nodes** now takes **~7** — same quality, same control, zero headache. I made them for myself first, but I know there are other creators out there grinding through the same mess I was. **If I can save you hours of frustration, this was worth it.** Nobody helped me figure this stuff out, so I want to be the person that helps you.

Whether you're doing bulk generation for your Patreon, building a Pixiv gallery, or just want a cleaner workflow — these nodes are for you.

---

## ✨ Highlights

- 🎨 **Cyan neon theme** — all nodes have a custom dark teal look that stands out
- 📄 **Prompt From File** — reads prompts from `.txt` with stateful line modes, resolves wildcards, loads LoRAs inline
- ⚡ **Supreme KSampler** — built-in empty latent, live preview, upscaler, and detailer toggle slots in one beast
- 👁️ **One-node Face Detailer** — replaces 3+ Impact Pack nodes with a single node
- 🔧 **BREAK & bracket support** — `BREAK` keyword and `[de-emphasis]` brackets work everywhere
- 🎛️ **Organized UI** — collapsible widget sections so you can actually find what you need

---

## 📦 Installation

### Option 1: ComfyUI Manager (Recommended)

Search for **FrostzNeeko** in ComfyUI Manager and click Install.

### Option 2: Git Clone

```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/XxFrostzNeekoxX/comfyui-frotszneeko-nodes.git
```

### Option 3: Download ZIP

Download and extract into `ComfyUI/custom_nodes/comfyui-frostzneeko-nodes/`.

After installing, **restart ComfyUI**. All nodes appear under **FrostzNeeko 🔹** in the node menu.

### Dependencies

This pack has **no hard dependencies** on other custom node packs. Everything is self-contained.


| Package         | Required?              | What for                                              |
| --------------- | ---------------------- | ----------------------------------------------------- |
| `ultralytics`   | Only for Face Detailer | YOLO face/body detection models                       |
| `opencv-python` | Optional               | Better mask dilation (falls back to numpy if missing) |


If you use the Face Detailer, install ultralytics:

```bash
pip install ultralytics
```

You'll also need Ultralytics detection models (`.pt` files) in `ComfyUI/models/ultralytics/bbox/` or `ComfyUI/models/ultralytics/segm/`. Any YOLO model works — face detection, person detection, etc. If you already have Impact Pack installed, your existing models work automatically.

---

## 🔹 Nodes

### FN Prompt From File (All-in-One)

The brain of bulk generation workflows. Reads prompts from a `.txt` file and handles everything in one node.


| Feature            | Description                                                                                    |
| ------------------ | ---------------------------------------------------------------------------------------------- |
| **Line Selection** | `increment`, `decrement`, `random`, `random no repetitions`, `fixed`                           |
| **Batch Counter**  | Hidden `count` input is fed by frontend JS and resets on queue                                 |
| **Start Line**     | `line_to_start_from` sets where batch progression begins                                       |
| **Wildcards**      | `__tag__` syntax — reads from a `wildcards/` folder                                            |
| **Inline LoRAs**   | `<lora:name:weight>` tags in your prompt — auto-loaded and applied                             |
| **Checkpoint**     | Optional built-in checkpoint loader — no separate node needed                                  |
| **CLIP Skip**      | Built-in `clip_skip` parameter (default 1, set to 2 for anime models)                          |
| **BREAK**          | Splits prompt into separate 77-token conditioning chunks                                       |
| **No-LoRA CLIP**   | Extra `no_lora_clip` output — clean CLIP without LoRA patches for dual-encode/detail workflows |


**Outputs:** `MODEL`, `CLIP`, `no_lora_clip`, `VAE`, `CONDITIONING`, `processed_prompt`, `raw_prompt`, `line_number`

💡 Prompt file format

```
masterpiece, best quality, 1girl, red dress, garden, flowers
masterpiece, best quality, 1girl, blue dress, beach, sunset <lora:add_detail:0.8>
masterpiece, best quality, 1boy, suit, office, __expression__
```

Each line is one prompt. Empty lines are skipped. LoRA tags are extracted and applied automatically.



---

### FN Supreme KSampler

The main workhorse. Full KSampler with everything built in — the only sampler node you'll ever need.


| Feature              | Description                                                                        |
| -------------------- | ---------------------------------------------------------------------------------- |
| **Built-in Latent**  | Width/height/batch controls — no `EmptyLatentImage` node needed                    |
| **Live Preview**     | Per-node preview method: `auto`, `latent2rgb`, `taesd`, `vae_decoded_only`, `none` |
| **Upscaler**         | Optional model upscaler (ESRGAN, etc.) — applied after generation                  |
| **Detailer Toggles** | 4 named toggle slots to enable/disable downstream Face Detailers                   |
| **Organized UI**     | Collapsible sections: Sampling, Latent Size, Preview, Upscaler, Detailers          |


**Outputs:** `LATENT`, `IMAGE`, `detail_pipe`

> The `detail_pipe` output connects to FN Face Detailer nodes. Name your detailers (e.g. "Eyes", "Face") and toggle them on/off from the Supreme KSampler without rewiring.

---

### FN Face Detailer

Automatic face/feature detection and inpainting. Replaces the entire Impact Pack pipeline (`UltralyticsDetectorProvider` → `BBOX Detector` → `Detailer`) in **one node**.


| Feature            | Description                                                           |
| ------------------ | --------------------------------------------------------------------- |
| **Detection**      | Threshold, dilation, crop factor, drop size — all configurable        |
| **Sampling**       | Full sampler controls (seed, steps, cfg, sampler, scheduler, denoise) |
| **Inpainting**     | Feather, noise mask, force inpaint, noise mask feather                |
| **Toggle Control** | Name-based enable/disable via `detail_pipe` from KSampler             |
| **Wildcard Spec**  | Optional text prompt override for the detailer pass                   |
| **Preview**        | Built-in preview of the detailed result                               |


**Outputs:** `IMAGE`

> Set the `name` to match a toggle slot in FN KSampler Preview (e.g. "Eyes"). The detailer only runs when its toggle is enabled.

---

### FN CLIP Dual Encode

Two text areas in one node — positive on top, negative on bottom.


| Feature           | Description                                                              |
| ----------------- | ------------------------------------------------------------------------ |
| **Dual Output**   | Positive and negative conditioning from a single node                    |
| **BREAK**         | Supported in both positive and negative prompts                          |
| **[Brackets]**    | `[word]` de-emphasis (÷1.1 weight) — not natively supported by ComfyUI   |
| **Negative CLIP** | Optional separate CLIP input for negative encoding (e.g. LoRA-free CLIP) |


**Outputs:** `positive CONDITIONING`, `negative CONDITIONING`, `CLIP`

---

### FN CLIP Text Encode (Advanced)

Single-text CLIP encoder with extra features.


| Feature              | Description                                            |
| -------------------- | ------------------------------------------------------ |
| **BREAK**            | Splits prompt into separate 77-token chunks            |
| **[Brackets]**       | `[word]` → `(word:0.9091)` de-emphasis conversion      |
| **Standard Weights** | `(word)`, `((word))`, `(word:1.5)` — all work natively |


**Outputs:** `CONDITIONING`

---

### FN Checkpoint Loader

Clean checkpoint loader, consistent with the pack's theme.

**Outputs:** `MODEL`, `CLIP`, `VAE`

---

### FN Image Saver

Saves images with full control over format and naming.


| Feature             | Description                                                               |
| ------------------- | ------------------------------------------------------------------------- |
| **Formats**         | PNG, JPEG, WebP                                                           |
| **Quality**         | Adjustable quality slider (1-100)                                         |
| **Naming**          | Custom prefix + optional timestamp                                        |
| **Numbering Style** | `comfy_default` or `prefix_number` (`teto_001`) with configurable padding |
| **Subfolder**       | Custom output subfolder                                                   |
| **Metadata**        | Full workflow metadata embedded (PNG)                                     |
| **Preview**         | Built-in preview of saved images                                          |
| **Passthrough**     | `IMAGE` output for chaining                                               |


---

## 🔌 Typical Workflow

A complete generation + face detail pipeline with just **5 nodes**:

```
FN Prompt From File → FN CLIP Dual Encode → FN Supreme KSampler → FN Face Detailer → FN Image Saver
```


| Node                | Replaces                                                                                |
| ------------------- | --------------------------------------------------------------------------------------- |
| FN Prompt From File | Load Line From File + Extract LoRA + Lora Loader + CLIPSetLastLayer + Checkpoint Loader |
| FN CLIP Dual Encode | 2× CLIPTextEncode                                                                       |
| FN Supreme KSampler | EmptyLatentImage + KSampler + PreviewImage                                              |
| FN Face Detailer    | UltralyticsProvider + BBOX Detector + SEGS Merge + DetailerForEach                      |
| FN Image Saver      | SaveImage                                                                               |


**~12 nodes → 5 nodes.** Same results, cleaner workflow.

> 📁 Check the `workflows/` folder for ready-to-use workflow templates you can import directly into ComfyUI.

---

## ⚙️ Weight Syntax Reference

All CLIP encoding nodes in this pack support:


| Syntax       | Effect             | Example                 |
| ------------ | ------------------ | ----------------------- |
| `(word)`     | Weight × 1.1       | `(masterpiece)` → 1.1   |
| `((word))`   | Weight × 1.21      | `((detailed))` → 1.21   |
| `(word:1.5)` | Explicit weight    | `(eyes:1.4)` → 1.4      |
| `[word]`     | Weight ÷ 1.1       | `[blurry]` → 0.909      |
| `BREAK`      | New 77-token chunk | `prompt1 BREAK prompt2` |


> **Note:** `(word)` and `(word:weight)` are handled by ComfyUI's native tokenizer. `[brackets]` and `BREAK` are added by this node pack.

---

## 🎨 Theme

All nodes use a custom **cyan neon** dark theme that's easy to spot in your workflow:

- **Title bar:** Dark teal (`#00363A`)
- **Body:** Deep dark (`#0C1B1E`)
- **Accent:** Cyan highlights

---

## ❓ FAQ

**Do these nodes produce the same results as standard ComfyUI nodes?**

Yes. The sampling and CLIP encoding logic is identical to ComfyUI's built-in nodes. Same seed + same parameters = same output. We use `comfy.sample.sample()` and `clip.encode_from_tokens_scheduled()` directly — no custom math.



**Do I need Impact Pack installed?**

**No.** The Face Detailer is fully self-contained — it reimplements the entire detection and detailing pipeline internally. You just need the `ultralytics` pip package and YOLO model files (`.pt`). If you already have Impact Pack installed, the same model files will work automatically.



**What's the `no_lora_clip` output on Prompt From File?**

It's a clean CLIP model **without LoRA patches**. Some workflows encode the negative prompt with an unpatched CLIP for better results. Connect it to the `negative_clip` input on FN CLIP Dual Encode if you want this behavior.



**How does line progression work in Prompt From File now?**

It uses stateful progression with `increment`, `decrement`, `random`, `random no repetitions`, and `fixed`. The hidden `count` input is auto-fed by frontend JS and resets when a new queue is submitted.



---

## 📄 License

MIT — do whatever you want with it.

---

  
Made with ❤️ by FrostzNeeko