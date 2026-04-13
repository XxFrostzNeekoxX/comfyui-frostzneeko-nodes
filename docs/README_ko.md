<p align="center">
  <b>🌐 언어:</b>
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
  <b>ComfyUI용 올인원 커스텀 노드 — 대량 생성 워크플로우를 위해 설계</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/ComfyUI-커스텀_노드-blue?style=for-the-badge" alt="ComfyUI"/>
  <img src="https://img.shields.io/badge/라이선스-MIT-green?style=for-the-badge" alt="MIT"/>
  <img src="https://img.shields.io/badge/노드-7-cyan?style=for-the-badge" alt="7 노드"/>
</p>

---

AI 콘텐츠를 대량 생성하면서 30개 이상의 노드로 간단한 작업을 하는 지저분한 워크플로우에 지쳤습니다. 그래서 모든 것을 깔끔하고 빠르게 유지하기 위해 이 올인원 노드를 만들었습니다 — **~40개 노드에서 ~7개로** 줄이면서 완전한 제어를 유지합니다. 대량 생성을 하신다면, 많은 시간을 절약해 줄 것입니다.

## ✨ 하이라이트

- 🎨 **시안 네온 테마** — 모든 노드가 커스텀 다크 틸 룩으로 눈에 띕니다
- 📄 **파일에서 프롬프트** — `.txt`에서 프롬프트를 읽고, 자동 순환, 와일드카드 해석, LoRA 인라인 로드
- ⚡ **올인원 KSampler** — 내장 빈 Latent, 실시간 미리보기, 업스케일러, 디테일러 토글
- 👁️ **원노드 Face Detailer** — Impact Pack의 3개 이상 노드를 하나로 대체
- 🔧 **BREAK 및 대괄호 지원** — `BREAK` 키워드와 `[약화]` 대괄호가 모든 곳에서 작동
- 🎛️ **정리된 UI** — 접을 수 있는 위젯 섹션

---

## 📦 설치

### 방법 1: ComfyUI Manager (권장)
ComfyUI Manager에서 **FrotszNeeko**를 검색하고 설치를 클릭하세요.

### 방법 2: Git Clone
```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/XxFrostzNeekoxX/comfyui-frotszneeko-nodes.git
```

### 방법 3: ZIP 다운로드
다운로드하여 `ComfyUI/custom_nodes/comfyui-frotszneeko-nodes/`에 압축을 풀어주세요.

설치 후 **ComfyUI를 재시작**하세요. 모든 노드가 노드 메뉴의 **FrotszNeeko 🔹** 아래에 표시됩니다.

### 의존성

이 팩은 다른 커스텀 노드 팩에 대한 **필수 의존성이 없습니다**. 모든 것이 독립적입니다.

| 패키지 | 필요? | 용도 |
|---|---|---|
| `ultralytics` | Face Detailer에만 필요 | YOLO 얼굴/신체 감지 모델 |
| `opencv-python` | 선택 사항 | 더 나은 마스크 팽창 (없으면 numpy로 대체) |

Face Detailer를 사용한다면 ultralytics를 설치하세요:
```bash
pip install ultralytics
```

Ultralytics 감지 모델 (`.pt` 파일)도 `ComfyUI/models/ultralytics/bbox/` 또는 `ComfyUI/models/ultralytics/segm/`에 필요합니다. 어떤 YOLO 모델이든 작동합니다. Impact Pack이 이미 설치되어 있다면, 기존 모델이 자동으로 작동합니다.

---

## 🔹 노드

### FN Prompt From File (올인원)

대량 생성 워크플로우의 두뇌. `.txt` 파일에서 프롬프트를 읽고 하나의 노드로 모든 것을 처리합니다.

| 기능 | 설명 |
|---|---|
| **라인 선택** | `auto_cycle` (매 실행마다 진행), `sequential` (시드 기반), `random`, `ping_pong` |
| **자동 순환** | 각 실행 = 순서대로 다음 라인. 새 큐는 항상 1번 라인부터 시작 |
| **와일드카드** | `__tag__` 구문 — `wildcards/` 폴더에서 읽기 |
| **인라인 LoRA** | 프롬프트의 `<lora:이름:가중치>` 태그 — 자동 로드 및 적용 |
| **체크포인트** | 선택적 내장 체크포인트 로더 |
| **CLIP Skip** | 내장 `clip_skip` 매개변수 (기본값 1, 애니메이션 모델은 2로 설정) |
| **BREAK** | 프롬프트를 77토큰 독립 컨디셔닝 청크로 분할 |
| **디테일러 CLIP** | LoRA 패치 없는 깨끗한 CLIP 출력 |

**출력:** `MODEL`, `CLIP`, `detailer_clip`, `VAE`, `CONDITIONING`, `processed_prompt`, `raw_prompt`, `line_number`

---

### FN KSampler Preview

메인 작업 노드. 추가 기능이 내장된 완전한 KSampler.

**출력:** `LATENT`, `IMAGE`, `detail_pipe`

---

### FN Face Detailer

자동 얼굴 감지 및 인페인팅. Impact Pack 파이프라인 전체를 **하나의 노드**로 대체합니다.

**출력:** `IMAGE`

---

### FN CLIP Dual Encode

하나의 노드에 두 개의 텍스트 영역 — 위가 긍정, 아래가 부정.

**출력:** `positive CONDITIONING`, `negative CONDITIONING`, `CLIP`

---

### FN CLIP Text Encode (Advanced) · FN Checkpoint Loader · FN Image Saver

추가 기능이 있는 CLIP 인코더, 깔끔한 체크포인트 로더, 포맷 및 이름 지정을 완전히 제어할 수 있는 이미지 저장 노드.

---

## 🔌 일반적인 워크플로우

```
FN Prompt From File → FN CLIP Dual Encode → FN KSampler Preview → FN Face Detailer → FN Image Saver
```

**~12개 노드 → 5개 노드.** 같은 결과, 더 깔끔한 워크플로우.

---

## 📄 라이선스

MIT — 마음대로 사용하세요.

---

<p align="center">
  <img src="../img/mascot.png" alt="FrotszNeeko" width="80"/>
  <br/>
  <sub>❤️를 담아 FrotszNeeko 제작</sub>
</p>
