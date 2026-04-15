<p align="center">
  <b>🌐 Idioma:</b>
  <a href="../README.md">English</a> •
  <a href="README_pt-BR.md">Português</a> •
  <a href="README_es.md">Español</a> •
  <a href="README_zh-CN.md">中文</a> •
  <a href="README_ja.md">日本語</a> •
  <a href="README_ko.md">한국어</a>
</p>

<p align="center">
  <img src="../img/mascot.png" alt="FrostzNeeko Mascot" width="200"/>
</p>

<h1 align="center">🔹 FrostzNeeko Nodes</h1>

<p align="center">
  <b>Nodos personalizados todo-en-uno para ComfyUI — diseñados para flujos de generación masiva</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/ComfyUI-Custom_Nodes-blue?style=for-the-badge" alt="ComfyUI"/>
  <img src="https://img.shields.io/badge/Licencia-MIT-green?style=for-the-badge" alt="MIT"/>
  <img src="https://img.shields.io/badge/Nodos-7-cyan?style=for-the-badge" alt="7 Nodos"/>
</p>

---

## 💬 Por qué lo creé

Publico contenido en **Patreon**, **Pixiv**, **DeviantArt** y otras plataformas — lo que significa que genero imágenes AI en masa todos los días. Cuando empecé con ComfyUI, cada workflow que encontraba online era una pesadilla: **30, 40, a veces 50+ nodos** solo para hacer una generación básica con fix de rostro. Cables por todos lados, imposible de debuggear, y nadie en la comunidad estaba dispuesto a ayudar a simplificar.

Así que dije al diablo con todo y construí los míos.

Estos nodos comprimen pipelines enteros en bloques únicos y limpios. Lo que antes necesitaba **~40 nodos** ahora necesita **~7** — misma calidad, mismo control, cero dolor de cabeza. Los hice para mí primero, pero sé que hay otros creadores ahí afuera luchando con el mismo caos. **Si puedo ahorrarte horas de frustración, valió la pena.** Nadie me ayudó a descifrar estas cosas, así que quiero ser la persona que te ayude a ti.

Ya sea para generación masiva para tu Patreon, armar una galería en Pixiv, o simplemente tener un workflow más limpio — estos nodos son para ti.

---

## ✨ Destacados

- 🎨 **Tema cyan neón** — todos los nodos tienen un look dark teal personalizado que resalta
- 📄 **Prompt From File** — lee prompts de `.txt` con modos de línea con estado, resuelve wildcards y carga LoRAs inline
- ⚡ **Supreme KSampler** — latent vacío integrado, preview en vivo, upscaler y toggles de detailer en una bestia
- 👁️ **Face Detailer en un nodo** — detección + detalle en un solo nodo
- 🔧 **Soporte BREAK y corchetes** — keyword `BREAK` y `[de-emphasis]` funcionan en todas partes
- 🎛️ **UI organizada** — secciones colapsables para encontrar lo que necesitas

---

## 🆕 Novedades recientes

- Face Detailer: preview de máscara, tiled VAE encode/decode, etapa de refiner y entrada opcional de `SIGMAS`.
- Image Saver: metadata PNG bonita (fecha/hora, seed, sampler, prompts y LoRAs).
- Image Saver: nuevo toggle `save_pretty_metadata` para activar/desactivar ese bloque formateado.

---

## 📦 Instalación

### Opción 1: ComfyUI Manager (Recomendado)
Busca **FrostzNeeko** en ComfyUI Manager y haz clic en Instalar.

### Opción 2: Git Clone
```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/XxFrostzNeekoxX/comfyui-frotszneeko-nodes.git
```

### Opción 3: Descargar ZIP
Descarga y extrae en `ComfyUI/custom_nodes/comfyui-frostzneeko-nodes/`.

Después de instalar, **reinicia ComfyUI**. Todos los nodos aparecen en **FrostzNeeko 🔹** en el menú de nodos.

### Dependencias

Este pack **no tiene dependencias obligatorias** de otros packs de nodos. Todo es independiente.

| Paquete | ¿Necesario? | Para qué |
|---|---|---|
| `ultralytics` | Solo para Face Detailer | Modelos YOLO de detección facial/corporal |
| `opencv-python` | Opcional | Mejor dilatación de máscaras (usa numpy si falta) |

Si usas el Face Detailer, instala ultralytics:
```bash
pip install ultralytics
```

También necesitas modelos Ultralytics (`.pt`) en `ComfyUI/models/ultralytics/bbox/` o `ComfyUI/models/ultralytics/segm/`. Cualquier modelo YOLO funciona.

---

## 🔹 Nodos

### FN Prompt From File (All-in-One)

El cerebro de los workflows de generación masiva. Lee prompts de un archivo `.txt` y maneja todo en un nodo.

| Característica | Descripción |
|---|---|
| **Selección de Línea** | `increment`, `decrement`, `random`, `random no repetitions`, `fixed` |
| **Contador de Lote** | `count` oculto, alimentado por JS y reiniciado al enviar una nueva cola |
| **Línea Inicial** | `line_to_start_from` define desde qué línea comienza la progresión |
| **Wildcards** | Sintaxis `__tag__` — lee de una carpeta `wildcards/` |
| **LoRAs Inline** | Tags `<lora:nombre:peso>` en tu prompt — cargadas y aplicadas automáticamente |
| **Checkpoint** | Cargador de checkpoint integrado opcional — sin nodo separado |
| **CLIP Skip** | Parámetro `clip_skip` integrado (predeterminado 1, usa 2 para modelos anime) |
| **BREAK** | Divide el prompt en chunks de conditioning de 77 tokens |
| **CLIP sin LoRA** | Salida extra `no_lora_clip` — CLIP limpio sin parches de LoRA |

**Salidas:** `MODEL`, `CLIP`, `no_lora_clip`, `VAE`, `CONDITIONING`, `processed_prompt`, `raw_prompt`, `line_number`

---

### FN Supreme KSampler

El caballo de batalla. KSampler completo con todo integrado — el único nodo de sampler que necesitarás.

| Característica | Descripción |
|---|---|
| **Latent Integrado** | Controles de ancho/alto/batch — sin necesidad de nodo `EmptyLatentImage` |
| **Preview en Vivo** | Método de preview por nodo: `auto`, `latent2rgb`, `taesd`, `vae_decoded_only`, `none` |
| **Upscaler** | Upscaler de modelo opcional (ESRGAN, etc.) — aplicado después de generación |
| **Toggles de Detailer** | 4 slots nombrados para activar/desactivar Face Detailers downstream |
| **UI Organizada** | Secciones colapsables: Sampling, Tamaño Latent, Preview, Upscaler, Detailers |

**Salidas:** `LATENT`, `IMAGE`, `detail_pipe`

---

### FN Face Detailer

Detección e inpainting automático de rostros en **un solo nodo**.

**Salidas:** `IMAGE`, `mask_preview`

---

### FN CLIP Dual Encode

Dos áreas de texto en un nodo — positivo arriba, negativo abajo.

**Salidas:** `positive CONDITIONING`, `negative CONDITIONING`, `CLIP`

---

### FN CLIP Text Encode (Advanced)

Encoder CLIP de texto único con características extra.

**Salidas:** `CONDITIONING`

---

### FN Checkpoint Loader

Cargador de checkpoint limpio, consistente con el tema del pack.

**Salidas:** `MODEL`, `CLIP`, `VAE`

---

### FN Image Saver

Guarda imágenes con control total de formato y nomenclatura. Soporta PNG, JPEG y WebP, con metadata bonita opcional (`save_pretty_metadata`).

---

## 🔌 Workflow Típico

```
FN Prompt From File → FN CLIP Dual Encode → FN Supreme KSampler → FN Face Detailer → FN Image Saver
```

**~12 nodos → 5 nodos.** Mismos resultados, workflow más limpio.

> 📁 Revisa la carpeta `workflows/` para templates de workflow listos para importar directamente en ComfyUI.

---

## 📄 Licencia

MIT — haz lo que quieras con esto.

---

<p align="center">
  <img src="../img/mascot.png" alt="FrostzNeeko" width="80"/>
  <br/>
  <sub>Hecho con ❤️ por FrostzNeeko</sub>
</p>
