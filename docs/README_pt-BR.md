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
  <b>Nodes customizados tudo-em-um para ComfyUI — feitos para workflows de geração em massa</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/ComfyUI-Custom_Nodes-blue?style=for-the-badge" alt="ComfyUI"/>
  <img src="https://img.shields.io/badge/Licença-MIT-green?style=for-the-badge" alt="MIT"/>
  <img src="https://img.shields.io/badge/Nodes-7-cyan?style=for-the-badge" alt="7 Nodes"/>
</p>

---

## 💬 Por que eu criei isso

Eu posto conteúdo no **Patreon**, **Pixiv**, **DeviantArt** e outras plataformas — o que significa que eu gero imagens AI em massa todo santo dia. Quando eu comecei a usar ComfyUI, todo workflow que eu achava online era um pesadelo: **30, 40, às vezes 50+ nodes** só pra fazer uma geração básica com fix de rosto. Fios de espaguete pra todo lado, impossível de debugar, e ninguém na comunidade tava disposto a ajudar a simplificar as coisas.

Então eu falei dane-se e fiz os meus próprios.

Esses nodes comprimem pipelines inteiras em blocos únicos e limpos. O que antes precisava de **~40 nodes** agora precisa de **~7** — mesma qualidade, mesmo controle, zero dor de cabeça. Eu fiz pra mim primeiro, mas eu sei que tem outros criadores aí ralando no mesmo caos que eu tava. **Se eu puder te poupar horas de frustração, já valeu a pena.** Ninguém me ajudou a descobrir essas coisas, então eu quero ser a pessoa que te ajuda.

Seja pra geração em massa pro seu Patreon, montar uma galeria no Pixiv, ou só ter um workflow mais limpo — esses nodes são pra você.

---

## ✨ Destaques

- 🎨 **Tema cyan neon** — todos os nodes têm visual dark teal customizado que se destaca
- 📄 **Prompt From File** — lê prompts de `.txt`, faz auto-cycle, resolve wildcards, carrega LoRAs inline
- ⚡ **Supreme KSampler** — latent vazio embutido, preview ao vivo, upscaler e toggles de detailer em um monstro só
- 👁️ **Face Detailer em um node** — substitui 3+ nodes do Impact Pack em um único node
- 🔧 **Suporte a BREAK & colchetes** — keyword `BREAK` e `[de-emphasis]` funcionam em todo lugar
- 🎛️ **UI organizada** — seções colapsáveis pra você encontrar o que precisa

---

## 📦 Instalação

### Opção 1: ComfyUI Manager (Recomendado)
Procure por **FrostzNeeko** no ComfyUI Manager e clique em Instalar.

### Opção 2: Git Clone
```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/XxFrostzNeekoxX/comfyui-frotszneeko-nodes.git
```

### Opção 3: Download ZIP
Baixe e extraia em `ComfyUI/custom_nodes/comfyui-frostzneeko-nodes/`.

Após instalar, **reinicie o ComfyUI**. Todos os nodes aparecem em **FrostzNeeko 🔹** no menu de nodes.

### Dependências

Este pack **não tem dependências obrigatórias** de outros packs de nodes. Tudo é independente.

| Pacote | Necessário? | Pra quê |
|---|---|---|
| `ultralytics` | Só pro Face Detailer | Modelos YOLO de detecção de rosto/corpo |
| `opencv-python` | Opcional | Melhor dilatação de máscara (usa numpy se não tiver) |

Se usar o Face Detailer, instale o ultralytics:
```bash
pip install ultralytics
```

Você também precisa de modelos Ultralytics (`.pt`) em `ComfyUI/models/ultralytics/bbox/` ou `ComfyUI/models/ultralytics/segm/`. Qualquer modelo YOLO funciona. Se já tem o Impact Pack instalado, seus modelos existentes funcionam automaticamente.

---

## 🔹 Nodes

### FN Prompt From File (All-in-One)

O cérebro de workflows de geração em massa. Lê prompts de um arquivo `.txt` e cuida de tudo em um node.

| Recurso | Descrição |
|---|---|
| **Seleção de Linha** | `auto_cycle` (avança cada run), `sequential` (baseado na seed), `random`, `ping_pong` |
| **Auto-Cycle** | Cada run = próxima linha em ordem. Nova fila sempre começa da linha 1 |
| **Wildcards** | Sintaxe `__tag__` — lê de uma pasta `wildcards/` |
| **LoRAs Inline** | Tags `<lora:nome:peso>` no prompt — carregadas e aplicadas automaticamente |
| **Checkpoint** | Loader de checkpoint embutido opcional — sem necessidade de node separado |
| **CLIP Skip** | Parâmetro `clip_skip` embutido (padrão 1, use 2 para modelos anime) |
| **BREAK** | Divide o prompt em chunks de conditioning de 77 tokens |
| **Detailer CLIP** | Saída extra `detailer_clip` — CLIP limpo sem patches de LoRA para Face Detailer |

**Saídas:** `MODEL`, `CLIP`, `detailer_clip`, `VAE`, `CONDITIONING`, `processed_prompt`, `raw_prompt`, `line_number`

<details>
<summary>💡 Formato do arquivo de prompts</summary>

```
masterpiece, best quality, 1girl, red dress, garden, flowers
masterpiece, best quality, 1girl, blue dress, beach, sunset <lora:add_detail:0.8>
masterpiece, best quality, 1boy, suit, office, __expression__
```

Cada linha é um prompt. Linhas vazias são ignoradas. Tags de LoRA são extraídas e aplicadas automaticamente.
</details>

---

### FN Supreme KSampler

O carro-chefe. KSampler completo com tudo embutido — o único node de sampler que você vai precisar.

| Recurso | Descrição |
|---|---|
| **Latent Embutido** | Controles de largura/altura/batch — sem necessidade de node `EmptyLatentImage` |
| **Preview ao Vivo** | Método de preview por node: `auto`, `latent2rgb`, `taesd`, `vae_decoded_only`, `none` |
| **Upscaler** | Upscaler de modelo opcional (ESRGAN, etc.) — aplicado após geração |
| **Toggles de Detailer** | 4 slots nomeados para ativar/desativar Face Detailers downstream |
| **UI Organizada** | Seções colapsáveis: Sampling, Tamanho do Latent, Preview, Upscaler, Detailers |

**Saídas:** `LATENT`, `IMAGE`, `detail_pipe`

> A saída `detail_pipe` conecta aos nodes FN Face Detailer. Nomeie seus detailers (ex: "Olhos", "Rosto") e ative/desative do KSampler sem reconectar fios.

---

### FN Face Detailer

Detecção e inpainting automático de rosto/features. Substitui toda a pipeline do Impact Pack (`UltralyticsDetectorProvider` → `BBOX Detector` → `Detailer`) em **um único node**.

| Recurso | Descrição |
|---|---|
| **Detecção** | Threshold, dilatação, crop factor, drop size — tudo configurável |
| **Sampling** | Controles completos de sampler (seed, steps, cfg, sampler, scheduler, denoise) |
| **Inpainting** | Feather, noise mask, force inpaint, noise mask feather |
| **Controle por Toggle** | Ativar/desativar por nome via `detail_pipe` do KSampler |
| **Wildcard Spec** | Override de prompt de texto opcional para o passo de detailing |
| **Preview** | Preview embutido do resultado detalhado |

**Saídas:** `IMAGE`

> Defina o `name` para corresponder a um slot toggle no FN Supreme KSampler (ex: "Olhos"). O detailer só roda quando seu toggle está ativado.

---

### FN CLIP Dual Encode

Duas áreas de texto em um node — positivo em cima, negativo embaixo.

| Recurso | Descrição |
|---|---|
| **Saída Dupla** | Conditioning positivo e negativo de um único node |
| **BREAK** | Suportado em ambos os prompts positivo e negativo |
| **[Colchetes]** | `[palavra]` de-emphasis (÷1.1 peso) — não suportado nativamente pelo ComfyUI |
| **CLIP Negativo** | Entrada CLIP separada opcional para encoding negativo (ex: CLIP sem LoRA) |

**Saídas:** `positive CONDITIONING`, `negative CONDITIONING`, `CLIP`

---

### FN CLIP Text Encode (Advanced)

Encoder CLIP de texto único com recursos extras.

| Recurso | Descrição |
|---|---|
| **BREAK** | Divide prompt em chunks de 77 tokens |
| **[Colchetes]** | `[palavra]` → `(palavra:0.9091)` conversão de de-emphasis |
| **Pesos Padrão** | `(palavra)`, `((palavra))`, `(palavra:1.5)` — tudo funciona nativamente |

**Saídas:** `CONDITIONING`

---

### FN Checkpoint Loader

Loader de checkpoint limpo, consistente com o tema do pack.

**Saídas:** `MODEL`, `CLIP`, `VAE`

---

### FN Image Saver

Salva imagens com controle total de formato e nomenclatura.

| Recurso | Descrição |
|---|---|
| **Formatos** | PNG, JPEG, WebP |
| **Qualidade** | Slider de qualidade ajustável (1-100) |
| **Nomenclatura** | Prefixo customizado + timestamp opcional |
| **Subpasta** | Subpasta de saída customizada |
| **Metadata** | Metadata completa do workflow embutida (PNG) |
| **Preview** | Preview embutido das imagens salvas |
| **Passthrough** | Saída `IMAGE` para encadeamento |

---

## 🔌 Workflow Típico

Uma pipeline completa de geração + detalhamento facial com apenas **5 nodes**:

```
FN Prompt From File → FN CLIP Dual Encode → FN Supreme KSampler → FN Face Detailer → FN Image Saver
```

| Node | Substitui |
|---|---|
| FN Prompt From File | Load Line From File + Extract LoRA + Lora Loader + CLIPSetLastLayer + Checkpoint Loader |
| FN CLIP Dual Encode | 2× CLIPTextEncode |
| FN Supreme KSampler | EmptyLatentImage + KSampler + PreviewImage |
| FN Face Detailer | UltralyticsProvider + BBOX Detector + SEGS Merge + DetailerForEach |
| FN Image Saver | SaveImage |

**~12 nodes → 5 nodes.** Mesmos resultados, workflow mais limpo.

> 📁 Confira a pasta `workflows/` para templates de workflow prontos pra importar direto no ComfyUI.

---

## ❓ FAQ

<details>
<summary><b>Esses nodes produzem os mesmos resultados que os nodes padrão do ComfyUI?</b></summary>

Sim. A lógica de sampling e encoding CLIP é idêntica aos nodes nativos do ComfyUI. Mesma seed + mesmos parâmetros = mesma saída. Usamos `comfy.sample.sample()` e `clip.encode_from_tokens_scheduled()` diretamente — sem matemática customizada.
</details>

<details>
<summary><b>Preciso do Impact Pack instalado?</b></summary>

**Não.** O Face Detailer é totalmente independente — reimplementa toda a pipeline de detecção e detalhamento internamente. Você só precisa do pacote pip `ultralytics` e dos arquivos de modelo YOLO (`.pt`). Se já tem o Impact Pack instalado, os mesmos arquivos de modelo funcionam automaticamente.
</details>

<details>
<summary><b>O que é o modo <code>auto_cycle</code>?</b></summary>

Cada run em um batch usa a próxima linha: run 1 = linha 1, run 2 = linha 2, run 3 = linha 3, depois volta ao início. Quando você começa uma **nova fila** (cancela tudo e dá queue de novo, ou depois de um batch terminar), sempre reseta para a **linha 1**. Se cancelar apenas uma run no meio do batch, a próxima run pega a próxima linha normalmente.
</details>

---

## 📄 Licença

MIT — faça o que quiser.

---

<p align="center">
  <img src="../img/mascot.png" alt="FrostzNeeko" width="80"/>
  <br/>
  <sub>Feito com ❤️ por FrostzNeeko</sub>
</p>
