"""
FN Prompt From File (All-in-One) 🔹
Reads prompts from a .txt file line by line, processes wildcards,
loads LoRAs from inline tags, and encodes with CLIP — all in one node.

Optionally loads a checkpoint internally so you don't need a separate
Checkpoint Loader node connected.

Each line in the file is one prompt. Line selection is driven by the
seed value:
  • sequential: seed % num_lines  (use control_after_generate to advance)
  • random:     Random(seed).randint(...)
  • ping_pong:  seed-based ping-pong oscillation

This means if you cancel a run and re-queue, the SAME line is used
(because seed didn't change). Only when seed advances does the line change.

Display widgets:
  • current_prompt → the clean prompt text (no lora tags, wildcards resolved)
  • active_loras_wildcards → loras applied + wildcards resolved
"""

import os
import re
import random

import folder_paths
import comfy.sd
import comfy.utils


# Module-level state — survives ComfyUI cache resets and cancels
_auto_state = {}  # {node_unique_id: {"counter": int, "prev_remaining": int}}


class FNPromptFromFile:

    @classmethod
    def INPUT_TYPES(cls):
        ckpt_list = ["none"] + folder_paths.get_filename_list("checkpoints")

        return {
            "required": {
                "file_path": (
                    "STRING",
                    {"default": "prompts.txt", "multiline": False},
                ),
                "mode": (["auto_cycle", "sequential", "random", "ping_pong"],),
                "seed": (
                    "INT",
                    {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF},
                ),
                "reset": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "ckpt_name": (ckpt_list, {"default": "none"}),
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "clip_skip": (
                    "INT",
                    {"default": 1, "min": 1, "max": 12, "step": 1},
                ),
                "wildcard_dir": (
                    "STRING",
                    {"default": "", "multiline": False},
                ),
                # Display-only widgets (updated via UI return)
                "current_prompt": (
                    "STRING",
                    {"default": "", "multiline": True,
                     "placeholder": "📝 Current prompt will appear here after execution..."},
                ),
                "active_loras_wildcards": (
                    "STRING",
                    {"default": "", "multiline": True,
                     "placeholder": "🔗 LoRAs & Wildcards will appear here..."},
                ),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("MODEL", "CLIP", "CLIP", "VAE", "CONDITIONING", "STRING", "STRING", "INT")
    RETURN_NAMES = (
        "model",
        "clip",
        "detailer_clip",
        "vae",
        "conditioning",
        "processed_prompt",
        "raw_prompt",
        "line_number",
    )
    FUNCTION = "process"
    OUTPUT_NODE = True
    CATEGORY = "FrotszNeeko 🔹/Prompt"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")  # Always re-execute

    # ── Wildcard processing ──────────────────────────────────────────

    @staticmethod
    def _resolve_wildcard_dir(wildcard_dir):
        """Fall back to the bundled wildcards/ folder if none specified."""
        if wildcard_dir and os.path.isdir(wildcard_dir):
            return wildcard_dir
        fallback = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "wildcards",
        )
        return fallback if os.path.isdir(fallback) else None

    @staticmethod
    def process_wildcards(text, wildcard_dir, seed):
        """
        Replace ``__name__`` with a random line from ``wildcards/name.txt``.
        Returns (result_text, list_of_replacements).
        Each replacement is ("__name__", "chosen_value").
        """
        if not wildcard_dir:
            return text, []

        rng = random.Random(seed)
        result = text
        replacements = []

        for _ in range(10):  # guard against infinite recursion
            matches = re.findall(r"__([A-Za-z0-9_]+)__", result)
            if not matches:
                break
            for name in matches:
                wc_path = os.path.join(wildcard_dir, f"{name}.txt")
                if os.path.isfile(wc_path):
                    with open(wc_path, "r", encoding="utf-8") as fh:
                        lines = [
                            l.strip()
                            for l in fh
                            if l.strip() and not l.startswith("#")
                        ]
                    replacement = rng.choice(lines) if lines else name
                else:
                    print(f"[FrotszNeeko] ⚠️  Wildcard file not found: {wc_path}")
                    replacement = name
                replacements.append((f"__{name}__", replacement))
                result = result.replace(f"__{name}__", replacement, 1)

        return result, replacements

    # ── LoRA tag parsing + loading ───────────────────────────────────

    _LORA_RE = re.compile(r"<lora:([^:>]+):([^>]+)>", re.IGNORECASE)

    @staticmethod
    def _find_lora_file(name, lora_list):
        """Fuzzy-match a LoRA name against the list known to ComfyUI."""
        if name in lora_list:
            return name
        for ext in (".safetensors", ".pt", ".bin", ".ckpt"):
            candidate = name + ext
            if candidate in lora_list:
                return candidate
        # Case-insensitive basename match
        lo = name.lower()
        for f in lora_list:
            if os.path.splitext(os.path.basename(f))[0].lower() == lo:
                return f
        return None

    @classmethod
    def parse_and_load_loras(cls, text, model, clip):
        """
        Return (clean_text, patched_model, patched_clip, lora_info_list).
        lora_info_list = [(name, weight, success_bool), ...]
        """
        matches = cls._LORA_RE.findall(text)
        clean = cls._LORA_RE.sub("", text)
        clean = re.sub(r"\s{2,}", " ", clean).strip().strip(",").strip()

        cur_model, cur_clip = model, clip
        lora_list = folder_paths.get_filename_list("loras")
        lora_info = []

        for lora_name, weight_str in matches:
            try:
                weight = float(weight_str)
            except ValueError:
                weight = 1.0

            lora_file = cls._find_lora_file(lora_name, lora_list)
            if lora_file is None:
                print(f"[FrotszNeeko] ⚠️  LoRA not found: {lora_name}")
                lora_info.append((lora_name, weight, False))
                continue
            try:
                path = folder_paths.get_full_path("loras", lora_file)
                lora = comfy.utils.load_torch_file(path, safe_load=True)
                cur_model, cur_clip = comfy.sd.load_lora_for_models(
                    cur_model, cur_clip, lora, weight, weight
                )
                print(f"[FrotszNeeko] ✅ Loaded LoRA: {lora_name} (w={weight})")
                lora_info.append((lora_name, weight, True))
            except Exception as exc:
                print(f"[FrotszNeeko] ❌ Failed to load LoRA '{lora_name}': {exc}")
                lora_info.append((lora_name, weight, False))

        return clean, cur_model, cur_clip, lora_info

    # ── Checkpoint loading ───────────────────────────────────────────

    _ckpt_cache: dict = {}

    @classmethod
    def _load_checkpoint(cls, ckpt_name):
        """Load checkpoint and cache it."""
        if ckpt_name in cls._ckpt_cache:
            return cls._ckpt_cache[ckpt_name]

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
        ckpt_model = out[0]
        ckpt_clip = out[1]
        ckpt_vae = out[2]

        cls._ckpt_cache[ckpt_name] = (ckpt_model, ckpt_clip, ckpt_vae)
        print(f"[FrotszNeeko] ✅ Loaded checkpoint: {ckpt_name}")
        return (ckpt_model, ckpt_clip, ckpt_vae)

    # ── Line selection ────────────────────────────────────────────────

    @staticmethod
    def _pick_line(lines, mode, seed, uid="default"):
        """
        Pick a line index based on mode and seed.

        auto_cycle:  Advances one line per run (0, 1, 2, 0, 1, 2, ...).
                     Resets to line 1 when a new batch is queued.
        sequential:  seed % num_lines (seed-driven)
        random:      Random(seed).randint(...)
        ping_pong:   seed-based ping-pong oscillation
        """
        n = len(lines)
        if n == 0:
            return 0, ""

        if mode == "auto_cycle":
            if uid not in _auto_state:
                _auto_state[uid] = {"counter": 0, "prev_remaining": 0}
            st = _auto_state[uid]
            idx = st["counter"] % n
            st["counter"] += 1
            print(f"[FrotszNeeko] 📄 Auto-cycle: line {idx + 1}/{n}")
        elif mode == "sequential":
            idx = seed % n
        elif mode == "random":
            rng = random.Random(seed)
            idx = rng.randint(0, n - 1)
        elif mode == "ping_pong":
            # Ping-pong: 0,1,2,...,n-1,n-2,...,1,0,1,2,...
            cycle = max(1, (n - 1) * 2)
            pos = seed % cycle
            if pos < n:
                idx = pos
            else:
                idx = cycle - pos
        else:
            idx = seed % n

        return idx, lines[idx]

    # ── Main entry point ─────────────────────────────────────────────

    def process(
        self,
        file_path,
        mode,
        seed,
        reset=False,
        control_after_generate="randomize",
        ckpt_name="none",
        model=None,
        clip=None,
        clip_skip=1,
        wildcard_dir="",
        current_prompt="",
        active_loras_wildcards="",
        **kwargs
    ):
        # ── resolve model / clip / vae ────────────────────────────────
        vae = None

        if ckpt_name and ckpt_name != "none":
            ckpt_model, ckpt_clip, ckpt_vae = self._load_checkpoint(ckpt_name)
            model = ckpt_model
            clip = ckpt_clip
            vae = ckpt_vae

        if model is None or clip is None:
            raise ValueError(
                "[FrotszNeeko] No model/clip available. "
                "Connect MODEL + CLIP inputs or select a checkpoint."
            )

        # 1. Handle auto_cycle batch detection ----------------------------
        if mode == "auto_cycle":
            uid = kwargs.get("unique_id", "default")
            if uid not in _auto_state:
                _auto_state[uid] = {"counter": 0, "prev_remaining": 0}
            st = _auto_state[uid]

            # Detect new batch via ComfyUI's prompt queue
            try:
                from server import PromptServer
                remaining = PromptServer.instance.prompt_queue.get_tasks_remaining()
            except Exception:
                remaining = -1

            if remaining >= 0:
                if remaining >= st["prev_remaining"]:
                    # Queue grew or same size → new batch → reset to line 1
                    st["counter"] = 0
                    print("[FrotszNeeko] 🔄 New batch detected — starting from line 1")
                st["prev_remaining"] = remaining

            # Manual reset override
            if reset:
                st["counter"] = 0

        # 2. Read lines -----------------------------------------------
        raw_prompt = ""
        line_num = 0

        if not os.path.isfile(file_path):
            print(f"[FrotszNeeko] ❌ File not found: {file_path}")
        else:
            with open(file_path, "r", encoding="utf-8") as fh:
                lines = [l.strip() for l in fh if l.strip()]

            if lines:
                line_num, raw_prompt = self._pick_line(lines, mode, seed, uid=kwargs.get("unique_id", "default"))
                if mode == "auto_cycle":
                    print(f"[FrotszNeeko] 🔄 Auto-cycle: line {line_num + 1}/{len(lines)}")

        # 2. Wildcards -------------------------------------------------
        full = raw_prompt
        wc_dir = self._resolve_wildcard_dir(wildcard_dir)
        full, wildcard_replacements = self.process_wildcards(full, wc_dir, seed)

        # 3. LoRAs -----------------------------------------------------
        #    Save base clip BEFORE LoRA patching for detailer output
        base_clip = clip
        clean_prompt, cur_model, cur_clip, lora_info = self.parse_and_load_loras(
            full, model, clip
        )

        # 4. CLIP Skip --------------------------------------------------
        if clip_skip > 1:
            cur_clip = cur_clip.clone()
            cur_clip.clip_layer(-(clip_skip))
            # Apply clip_skip to detailer clip too
            base_clip = base_clip.clone()
            base_clip.clip_layer(-(clip_skip))
            print(f"[FrotszNeeko] 🔧 CLIP Skip: -{clip_skip}")

        # 5. CLIP encode (with BREAK + [bracket] support) ----------------
        from .fn_clip_advanced import FNClipAdvanced
        encode_text = FNClipAdvanced.convert_brackets(clean_prompt)

        segments = re.split(r"\s*\bBREAK\b\s*", encode_text)
        segments = [s.strip() for s in segments if s.strip()]
        if not segments:
            segments = [""]

        tokens = cur_clip.tokenize(segments[0])
        for segment in segments[1:]:
            seg_tokens = cur_clip.tokenize(segment)
            for key in tokens:
                if key in seg_tokens:
                    tokens[key].extend(seg_tokens[key])

        conditioning = cur_clip.encode_from_tokens_scheduled(tokens)

        # 6. Build display texts for the UI ----------------------------

        # current_prompt: clean text (no lora tags, wildcards resolved)
        display_prompt = clean_prompt

        # active_loras_wildcards: both loras and wildcards info
        display_lines = []

        # LoRAs section
        if lora_info:
            display_lines.append("── LoRAs ──")
            for name, weight, ok in lora_info:
                status = "✅" if ok else "❌"
                display_lines.append(f"{status} {name} (w={weight})")
        else:
            display_lines.append("── LoRAs ──")
            display_lines.append("  (none in this prompt)")

        # Wildcards section
        if wildcard_replacements:
            display_lines.append("")
            display_lines.append("── Wildcards ──")
            for tag, value in wildcard_replacements:
                display_lines.append(f"🎲 {tag} → {value}")

        display_loras_wc = "\n".join(display_lines)

        print(f"[FrotszNeeko] 📄 Line {line_num}: {clean_prompt[:100]}…")
        if lora_info:
            loaded = sum(1 for _, _, ok in lora_info if ok)
            total = len(lora_info)
            print(f"[FrotszNeeko] 🔗 LoRAs: {loaded}/{total} applied to model")
        if wildcard_replacements:
            print(f"[FrotszNeeko] 🎲 Wildcards: {len(wildcard_replacements)} resolved")

        return {
            "ui": {
                "current_prompt": (display_prompt,),
                "active_loras_wildcards": (display_loras_wc,),
            },
            "result": (cur_model, cur_clip, base_clip, vae, conditioning, clean_prompt, raw_prompt, line_num),
        }
