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
  <img src="../img/mascot.png" alt="FrotszNeeko Mascot" width="200"/>
</p>

<h1 align="center">🔹 FrotszNeeko Nodes</h1>

<p align="center">
  <b>ComfyUI 一体化自定义节点 — 专为批量生成工作流设计</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/ComfyUI-自定义节点-blue?style=for-the-badge" alt="ComfyUI"/>
  <img src="https://img.shields.io/badge/许可证-MIT-green?style=for-the-badge" alt="MIT"/>
  <img src="https://img.shields.io/badge/节点-7-cyan?style=for-the-badge" alt="7 节点"/>
</p>

---

我大量生成AI内容，厌倦了30多个节点做简单事情的混乱工作流。因此我构建了这些一体化节点来保持整洁和高效 — 从 **~40个节点缩减到~7个**，同时保持完全控制。如果你进行批量生成，这些节点会为你节省大量时间。

## ✨ 亮点

- 🎨 **青色霓虹主题** — 所有节点都有自定义深青色外观，在工作流中一目了然
- 📄 **文件提示词** — 从 `.txt` 读取提示词，自动循环，解析通配符，内联加载 LoRA
- ⚡ **一体化 KSampler** — 内置空白潜空间、实时预览、放大器和细节器开关
- 👁️ **单节点面部细节器** — 用一个节点替代 3+ 个 Impact Pack 节点
- 🔧 **BREAK 和方括号支持** — `BREAK` 关键词和 `[降权]` 方括号全局可用
- 🎛️ **有组织的界面** — 可折叠的组件区域，轻松找到所需设置

---

## 📦 安装

### 方式一：ComfyUI Manager（推荐）
在 ComfyUI Manager 中搜索 **FrotszNeeko** 并点击安装。

### 方式二：Git Clone
```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/XxFrostzNeekoxX/comfyui-frotszneeko-nodes.git
```

### 方式三：下载 ZIP
下载并解压到 `ComfyUI/custom_nodes/comfyui-frotszneeko-nodes/`。

安装后，**重启 ComfyUI**。所有节点出现在节点菜单的 **FrotszNeeko 🔹** 下。

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

你还需要 Ultralytics 检测模型（`.pt` 文件）放在 `ComfyUI/models/ultralytics/bbox/` 或 `ComfyUI/models/ultralytics/segm/` 中。任何 YOLO 模型都可以。如果已安装 Impact Pack，现有模型会自动生效。

---

## 🔹 节点

### FN Prompt From File（一体化）

批量生成工作流的核心。从 `.txt` 文件读取提示词，一个节点搞定一切。

| 功能 | 描述 |
|---|---|
| **行选择** | `auto_cycle`（每次运行推进），`sequential`（基于种子），`random`，`ping_pong` |
| **自动循环** | 每次运行 = 按顺序下一行。新队列总是从第1行开始 |
| **通配符** | `__tag__` 语法 — 从 `wildcards/` 文件夹读取 |
| **内联 LoRA** | 提示词中的 `<lora:名称:权重>` 标签 — 自动加载和应用 |
| **检查点** | 可选的内置检查点加载器 — 无需单独节点 |
| **CLIP Skip** | 内置 `clip_skip` 参数（默认1，动漫模型设为2） |
| **BREAK** | 将提示词分割为独立的77令牌条件块 |
| **细节器 CLIP** | 额外的 `detailer_clip` 输出 — 无 LoRA 补丁的干净 CLIP |

**输出：** `MODEL`、`CLIP`、`detailer_clip`、`VAE`、`CONDITIONING`、`processed_prompt`、`raw_prompt`、`line_number`

---

### FN KSampler Preview

主力工具。带有额外功能的完整 KSampler。

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

自动面部检测和重绘。用**一个节点**替代整个 Impact Pack 管线。

**输出：** `IMAGE`

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

保存图像，完全控制格式和命名。支持 PNG、JPEG 和 WebP。

---

## 🔌 典型工作流

```
FN Prompt From File → FN CLIP Dual Encode → FN KSampler Preview → FN Face Detailer → FN Image Saver
```

**~12个节点 → 5个节点。** 相同结果，更简洁的工作流。

---

## 📄 许可证

MIT — 随便用。

---

<p align="center">
  <img src="../img/mascot.png" alt="FrotszNeeko" width="80"/>
  <br/>
  <sub>用 ❤️ 制作 by FrotszNeeko</sub>
</p>
