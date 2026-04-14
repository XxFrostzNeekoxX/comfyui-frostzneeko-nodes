<p align="center">
  <b>🌐 言語:</b>
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
  <b>ComfyUI用オールインワンカスタムノード — 大量生成ワークフロー向け</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/ComfyUI-カスタムノード-blue?style=for-the-badge" alt="ComfyUI"/>
  <img src="https://img.shields.io/badge/ライセンス-MIT-green?style=for-the-badge" alt="MIT"/>
  <img src="https://img.shields.io/badge/ノード-7-cyan?style=for-the-badge" alt="7 ノード"/>
</p>

---

## 💬 なぜこれを作ったのか

私は **Patreon**、**Pixiv**、**DeviantArt** などのプラットフォームでコンテンツを公開しています — つまり毎日AI画像を大量生成しています。ComfyUIを使い始めた時、オンラインで見つけたワークフローはどれも悪夢でした：基本的な生成と顔修復をするだけで **30、40、時には50以上のノード**。スパゲッティ配線だらけ、デバッグ不可能、そしてコミュニティの誰も簡素化を手伝ってくれませんでした。

だから、自分で作りました。

これらのノードはパイプライン全体を単一のクリーンなブロックに圧縮します。以前 **~40ノード** 必要だったものが今は **~7ノード** だけ — 同じ品質、同じコントロール、ゼロストレス。まず自分のために作りましたが、同じ混乱の中で苦闘している他のクリエイターがいることを知っています。**あなたの何時間ものフラストレーションを節約できるなら、それで十分です。** 誰も私を助けてくれなかったので、私があなたを助ける人になりたいです。

Patreonのバッチ生成、Pixivギャラリーの構築、または単によりクリーンなワークフローが欲しい方 — これらのノードはあなたのためのものです。

---

## ✨ ハイライト

- 🎨 **シアンネオンテーマ** — すべてのノードがカスタムダークティールの外观で際立つ
- 📄 **ファイルからプロンプト** — `.txt`からプロンプトを読み取り、自動サイクル、ワイルドカード解決、LoRAインライン読み込み
- ⚡ **Supreme KSampler** — 内蔵の空Latent、ライブプレビュー、アップスケーラー、ディテーラートグル、全部入り
- 👁️ **ワンノード Face Detailer** — Impact Packの3つ以上のノードを1つのノードで置換
- 🔧 **BREAK＆ブラケットサポート** — `BREAK`キーワードと`[弱調]`ブラケットがどこでも機能
- 🎛️ **整理されたUI** — 折りたたみ可能なウィジェットセクション

---

## 📦 インストール

### 方法1: ComfyUI Manager（推奨）
ComfyUI Managerで **FrotszNeeko** を検索してインストールをクリック。

### 方法2: Git Clone
```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/XxFrostzNeekoxX/comfyui-frotszneeko-nodes.git
```

### 方法3: ZIPダウンロード
ダウンロードして `ComfyUI/custom_nodes/comfyui-frotszneeko-nodes/` に展開。

インストール後、**ComfyUIを再起動**。すべてのノードがノードメニューの **FrotszNeeko 🔹** に表示されます。

### 依存関係

このパックは他のカスタムノードパックへの**必須依存関係はありません**。すべて自己完結しています。

| パッケージ | 必要？ | 用途 |
|---|---|---|
| `ultralytics` | Face Detailerのみ | YOLO顔/体検出モデル |
| `opencv-python` | オプション | より良いマスク膨張（なければnumpyにフォールバック） |

Face Detailerを使用する場合、ultralyticsをインストール：
```bash
pip install ultralytics
```

Ultralytics検出モデル（`.pt`ファイル）も `ComfyUI/models/ultralytics/bbox/` または `ComfyUI/models/ultralytics/segm/` に必要です。任意のYOLOモデルが使えます。Impact Packをすでにインストールしている場合、既存のモデルが自動的に機能します。

---

## 🔹 ノード

### FN Prompt From File（オールインワン）

大量生成ワークフローの頭脳。`.txt`ファイルからプロンプトを読み取り、1つのノードですべてを処理。

| 機能 | 説明 |
|---|---|
| **行選択** | `auto_cycle`（毎回進む）、`sequential`（シード基準）、`random`、`ping_pong` |
| **自動サイクル** | 各実行 = 順番に次の行。新しいキューは常に1行目から開始 |
| **ワイルドカード** | `__tag__` 構文 — `wildcards/` フォルダから読み取り |
| **インラインLoRA** | プロンプト内の `<lora:名前:重み>` タグ — 自動ロード＆適用 |
| **チェックポイント** | オプションの内蔵チェックポイントローダー |
| **CLIP Skip** | 内蔵 `clip_skip` パラメータ（デフォルト1、アニメモデルは2に設定） |
| **BREAK** | プロンプトを77トークンの独立したコンディショニングチャンクに分割 |
| **ディテーラーCLIP** | LoRAパッチなしのクリーンなCLIP出力 |

**出力:** `MODEL`、`CLIP`、`detailer_clip`、`VAE`、`CONDITIONING`、`processed_prompt`、`raw_prompt`、`line_number`

---

### FN Supreme KSampler

メインの作業ノード。完全なKSampler、すべて内蔵 — 必要な唯一のサンプラーノード。

**出力:** `LATENT`、`IMAGE`、`detail_pipe`

---

### FN Face Detailer

自動顔検出＆インペインティング。Impact Packパイプライン全体を**1つのノード**で置換。

**出力:** `IMAGE`

---

### FN CLIP Dual Encode

1つのノードに2つのテキストエリア — 上がポジティブ、下がネガティブ。

**出力:** `positive CONDITIONING`、`negative CONDITIONING`、`CLIP`

---

### FN CLIP Text Encode（Advanced）・FN Checkpoint Loader・FN Image Saver

追加機能付きCLIPエンコーダー、クリーンなチェックポイントローダー、フォーマット＆命名を完全制御できる画像保存ノード。

---

## 🔌 典型的なワークフロー

```
FN Prompt From File → FN CLIP Dual Encode → FN Supreme KSampler → FN Face Detailer → FN Image Saver
```

**~12ノード → 5ノード。** 同じ結果、よりクリーンなワークフロー。

> 📁 `workflows/` フォルダーをチェックして、ComfyUIに直接インポートできるワークフローテンプレートを入手してください。

---

## 📄 ライセンス

MIT — 好きに使ってください。

---

<p align="center">
  <img src="../img/mascot.png" alt="FrotszNeeko" width="80"/>
  <br/>
  <sub>❤️ を込めて FrotszNeeko が作成</sub>
</p>
