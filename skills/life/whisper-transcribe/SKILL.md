---
name: whisper-transcribe
description: 다운받은 강의 영상(mp4)을 Whisper로 트랜스크립트(txt)로 변환한다. 사용자가 "트랜스크립트 떠줘", "whisper 돌려줘", "자막 추출", "/whisper-transcribe"라고 하거나 영상 다운로드 후 텍스트화를 원하면 사용. ffmpeg로 wav 추출(병렬) 후 Whisper를 순차 실행한다.
---

# Whisper 트랜스크립션 파이프라인

## 첫 사용 설정 (이 컴퓨터에서 처음일 때만)

처음 쓸 때 아래를 확인하고, 사용자가 쓰는 Python 환경(conda env 등)을 한 번 물어봐서
기억해둔다. 이후 모든 명령은 그 환경의 `bin`을 `PATH` 앞에 넣어 실행한다
(아래 명령의 `{ENV_BIN}` 자리에 예: `~/miniconda3/envs/myenv/bin`).

```bash
# CUDA 지원 torch가 깔린 env에 설치해야 GPU 사용 가능
pip install openai-whisper
conda install -c conda-forge ffmpeg   # 또는 시스템 ffmpeg
```

- 설치 확인: `python -c "import torch; print(torch.cuda.is_available())"` → `True`여야 GPU 사용
- 모델 가중치는 첫 실행 시 `~/.cache/whisper/`에 자동 다운로드됨 (medium ~1.5GB, large-v3 ~3GB)
- **CPU 폴백 함정**: torch가 CPU 빌드면 에러 없이 조용히 CPU로 돌아 수 배 느려짐 — 반드시 위 확인 명령으로 검증

## Input

- 대상 mp4 파일(들). 지정이 없으면 `videos/`에서 `transcripts/`에 같은 이름의 `.txt`가 없는 영상 전부 (idempotent).

## Step 1: ffmpeg 오디오 추출 (병렬 가능, CPU, 수 초)

```bash
PATH={ENV_BIN}:$PATH \
  ffmpeg -i 'videos/{이름}.mp4' -vn -acodec pcm_s16le -ar 16000 -ac 1 'audio/{이름}.wav' -y
```

- 여러 영상이면 각각 `run_in_background`로 동시 실행 가능

## Step 2: Whisper 트랜스크립션 (반드시 순차, GPU)

```bash
PATH={ENV_BIN}:$PATH \
  whisper 'audio/{이름}.wav' --model medium --language ko \
  --output_format txt --output_dir transcripts --verbose False \
  > 'logs/whisper_{이름}.log' 2>&1
```

## 규칙 (전부 실전에서 검증된 함정들)

1. **CUDA torch가 있는 env로 실행** — 첫 사용 설정에서 확인한 `{ENV_BIN}`을 `PATH` 앞에 넣는다. CUDA 미지원 env면 CPU 폴백되어 수 배 느림.
2. **Whisper는 순차 실행** — 병렬 시 GPU OOM. 여러 파일이면 하나의 background 쉘 루프에서 순서대로 처리.
3. **언어 명시** — 자동 감지보다 안정적. 한국어 강의는 `--language ko`, 영어는 `--language en`.
4. **idempotent**: `transcripts/{이름}.txt`가 이미 있으면 건너뛴다.
5. **로그**: 출력은 `logs/whisper_*.log`로 리다이렉트 (`run_in_background` + 직접 로그 파일, tail 파이프 금지).
6. **소요 시간**: medium 모델 기준 30분 영상 ≈ 15분, VRAM ~5GB. GPU 여유가 있으면 `--model large-v3` (~10GB)도 가능.
7. 완료 후 `transcripts/{이름}.txt` 존재와 용량(보통 19~33KB)을 확인해 보고한다.
