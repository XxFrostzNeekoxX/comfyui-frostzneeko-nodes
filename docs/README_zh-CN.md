<p align="center">
  <b>🌐 语言:</b>
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
  <b>ComfyUI 一体化自定义节点 — 专为批量生成工作流设计</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/ComfyUI-自定义节点-blue?style=for-the-badge" alt="ComfyUI"/>
  <img src="https://img.shields.io/badge/许可证-MIT-green?style=for-the-badge" alt="MIT"/>
  <img src="https://img.shields.io/badge/节点-7-cyan?style=for-the-badge" alt="7 节点"/>
</p>

---

## 💬 为什么我做了这个

我在 **Patreon**、**Pixiv**、**DeviantArt** 等平台发布内容 — 这意味着我每天都在大量生成AI图像。当我刚开始用ComfyUI的时候，网上找到的每个工作流都是噬梦： **30、40、有时甚至50+个节点** 只为了做一个基本的生成加人脸修复。到处都是乱七八糟的连线，无法调试，而且社区里没人愿意帮忙简化。

所以我说管他的，自己建了。

这些节点将整个管线压缩成单个干净的块。以前需要 **~40个节点** 现在只需 **~7个** — 同样的质量，同样的控制，零头痛。我先为自己做的，但我知道外面还有其他创作者在同样的混乱中挣扎。**如果我能省下你几个小时的挂折，就值了。** 没人帮我搞懂这些东西，所以我想成为帮助你的那个人。

无论你是为Patreon做批量生成、建立Pixiv画廊、还是只想要一个更干净的工作流 — 这些节点就是为你做的。

---

## ✨ 亮点

- 🎨 **青色霓虹主题** — 所有节点都有自定义深青色外观，在工作流中一目了然
- 📄 **文件提示词** — 从 `.txt` 读取提示词，使用有状态行模式，解析通配符并内联加载 LoRA
- ⚡ **Supreme KSampler** — 内置空白潜空间、实时预览、放大器和细节器开关，一个节点搞定一切
- 👁️ **单节点面部细节器** — 一个节点完成检测 + 细化
- 🔧 **BREAK 和方括号支持** — `BREAK` 关键词和 `[降权]` 方括号全局可用
- 🎛️ **有组织的界面** — 可折叠的组件区域，轻松找到所需设置

---

## 🆕 最近更新

- Face Detailer：新增蒙版预览、tiled VAE encode/decode、refiner 阶段和可选 `SIGMAS` 输入。
- Image Saver：新增美观 PNG 元数据（时间、seed、sampler、prompt、LoRA）。
- Image Saver：新增 `save_pretty_metadata` 开关，可按需关闭该格式化元数据。

---

## 📦 安装

### 方式一：ComfyUI Manager（推荐）
在 ComfyUI Manager 中搜索 **FrostzNeeko** 并点击安装。

### 方式二：Git Clone
```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/XxFrostzNeekoxX/comfyui-frotszneeko-nodes.git
```

### 方式三：下载 ZIP
下载并解压到 `ComfyUI/custom_nodes/comfyui-frostzneeko-nodes/`。

安装后，**重启 ComfyUI**。所有节点出现在节点菜单的 **FrostzNeeko 🔹** 下。

### 依赖

本节点包**不依赖**其他自定义节点包。一切都是独立的。

| 包 | 是否需要？ | 用途 |
|---|---|---|
| `ultralytics` | 仅面部细节器需要 | YOLO 面部/身体检测模型 |
| `opencv-python` | 可选 | 更好的蒙版膨胀（缺失时回退到 numpy） |

如果使用面部细节器，请安装 ultralytics：
```bash
pip install ultralytics
```

你还需要 Ultralytics 检测模型（`.pt` 文件）放在 `ComfyUI/models/ultralytics/bbox/` 或 `ComfyUI/models/ultralytics/segm/` 中。任何 YOLO 模型都可以。

---

## 🔹 节点

### FN Prompt From File（一体化）

批量生成工作流的核心。从 `.txt` 文件读取提示词，一个节点搞定一切。

| 功能 | 描述 |
|---|---|
| **行选择** | `increment`、`decrement`、`random`、`random no repetitions`、`fixed` |
| **批次计数** | 隐藏的 `count` 由前端 JS 自动提供，并在新队列时重置 |
| **起始行** | `line_to_start_from` 用于设置从哪一行开始 |
| **通配符** | `__tag__` 语法 — 从 `wildcards/` 文件夹读取 |
| **内联 LoRA** | 提示词中的 `<lora:名称:权重>` 标签 — 自动加载和应用 |
| **检查点** | 可选的内置检查点加载器 — 无需单独节点 |
| **CLIP Skip** | 内置 `clip_skip` 参数（默认1，动漫模型设为2） |
| **BREAK** | 将提示词分割为独立的77令牌条件块 |
| **无 LoRA CLIP** | 额外的 `no_lora_clip` 输出 — 无 LoRA 补丁的干净 CLIP |

**输出：** `MODEL`、`CLIP`、`no_lora_clip`、`VAE`、`CONDITIONING`、`processed_prompt`、`raw_prompt`、`line_number`

---

### FN Supreme KSampler

主力工具。完整的KSampler，内置一切 — 你唯一需要的采样器节点。

| 功能 | 描述 |
|---|---|
| **内置潜空间** | 宽度/高度/批次控制 — 无需 `EmptyLatentImage` 节点 |
| **实时预览** | 每节点预览方式：`auto`、`latent2rgb`、`taesd`、`vae_decoded_only`、`none` |
| **放大器** | 可选模型放大器（ESRGAN 等） — 生成后应用 |
| **细节器开关** | 4个命名开关槽，启用/禁用下游面部细节器 |
| **有组织的界面** | 可折叠区域：采样、潜空间大小、预览、放大器、细节器 |

**输出：** `LATENT`、`IMAGE`、`detail_pipe`

---

### FN Face Detailer

自动面部检测和重绘，全部在**一个节点**内完成。

**输出：** `IMAGE`、`mask_preview`

---

### FN CLIP Dual Encode

一个节点两个文本区域 — 正面在上，负面在下。

**输出：** `positive CONDITIONING`、`negative CONDITIONING`、`CLIP`

---

### FN CLIP Text Encode（高级）

带额外功能的单文本 CLIP 编码器。

**输出：** `CONDITIONING`

---

### FN Checkpoint Loader

简洁的检查点加载器，与节点包主题一致。

**输出：** `MODEL`、`CLIP`、`VAE`

---

### FN Image Saver

保存图像，完全控制格式和命名。支持 PNG、JPEG 和 WebP，并支持可选美观元数据（`save_pretty_metadata`）。

---

## 🔌 典型工作流

```
FN Prompt From File → FN CLIP Dual Encode → FN Supreme KSampler → FN Face Detailer → FN Image Saver
```

**~12个节点 → 5个节点。** 相同结果，更简洁的工作流。

> 📁 查看 `workflows/` 文件夹，获取可以直接导入ComfyUI的工作流模板。

---

## 📄 许可证

MIT — 随便用。

---

<p align="center">
  <img src="../img/mascot.png" alt="FrostzNeeko" width="80"/>
  <br/>
  <sub>用 ❤️ 制作 by FrostzNeeko</sub>
</p>
