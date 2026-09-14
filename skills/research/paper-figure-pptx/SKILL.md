---
name: paper-figure-pptx
description: >
  Standing pipeline for ANY figure destined for a paper, manuscript, rebuttal, SI or conference
  submission - matplotlib draws only the ink, every label lives in an editable PPTX, and PNG+SVG
  are regenerated from that PPTX. Load this BEFORE writing figure code whenever the user asks for
  a paper/manuscript/rebuttal/SI figure in any phrasing - "논문 figure 그려줘", "그림 그려줘",
  "figure 만들어줘", "플롯 그려줘", "리버탈 그림", "SI figure", "패널 추가해줘", "이 데이터로 그림",
  "make a figure for the paper", "plot this for the manuscript" - and also whenever an existing
  figure needs a text/label/axis-title change, or the user has hand-edited a figure PPTX and wants
  the PNG/SVG refreshed ("PPT 고쳤어", "다시 뽑아줘", "PNG SVG 다시", "figure 업데이트").
  CRITICAL - this skill exists to stop three known dead ends: never deliver a matplotlib PNG with
  baked-in labels, never hand-write a new pptx builder (fig2pptx.py already does it), and never try
  to make PowerPoint export SVG (no converter ships with it; its PDF export re-rasterises pictures).
  Do NOT use for slide decks, posters, or presentation graphics - only figures that go into a paper.
---

# 논문 figure = matplotlib 잉크 + PPT 텍스트

글자가 구워진 matplotlib 산출물을 최종본으로 내지 않는다.
문구·글꼴·크기를 코드 재실행 없이 PowerPoint에서 손으로 고칠 수 있어야 한다.

| 요소 | 담당 |
|---|---|
| 데이터 곡선·막대·축선·**눈금 숫자(tick label)** | matplotlib (데이터 종속이라 그림에 남긴다) |
| xlabel · ylabel · title · 패널 (a)(b) · 주석 · 범례 | **PPTX 네이티브 텍스트박스** |
| 최종 PNG·SVG | 편집된 PPTX에서 `pptx2figs.py`로 재생성 |

번들 도구 (`scripts/`, 설치 후 `~/.claude/skills/paper-figure-pptx/scripts/`):

| 파일 | 방향 |
|---|---|
| `fig2pptx.py` | matplotlib `fig` → 편집 가능한 PPTX |
| `pptx2figs.py` | 편집된 PPTX → PNG + SVG |
| `pptx_crop_swap.py` | 패널 그림을 원본 렌더 + PowerPoint 자르기(srcRect)로 교체 |

**세션에서는 절대경로로 호출할 것.** 아래 `{PY}`, `{S}`는 first-run setup 값.

## First-run setup

한 번만 사용자에게 묻고 기억한다:

1. `{PY}` — `python-pptx`(1.0.x), `matplotlib`, `Pillow`가 설치된 파이썬 인터프리터 절대경로.
   없으면 `pip install python-pptx matplotlib pillow`.
2. `{S}` = `~/.claude/skills/paper-figure-pptx/scripts` (절대경로로 풀어 쓴다).
3. PNG 렌더(`pptx2figs.py`)에는 **WSL + Windows PowerPoint**가 필요하다
   (`powershell.exe -NoProfile -Command '$env:TEMP'`가 동작해야 함). 없으면 `--no-png`로
   SVG만 뽑는다. 손그림 도형이 섞인 덱의 SVG 우회에는 `pdftocairo`(poppler-utils)가 필요하다.

## Figure text policy (default)

- 그림 안에 작은 설명문, 회색 각주, 방법론 부제, takeaway 문장을 넣지 않는다. 캡션이나 슬라이드 노트로 보낸다. 색이나 크기를 줄여도 예외가 아니다.
- 패널별 제목을 달지 않는다. 패널 마커 `(a)`, `(b)`만 두고 설명은 캡션에서 한다.
- 축 라벨·단위·눈금·범례·컬러바 라벨, 구조와 데이터를 잇는 짧은 식별자(MC step 번호 등)는 남기고, 아래 파이프라인대로 편집 가능하게 둔다.
- 사용자가 특정 figure에 대해 명시적으로 예외를 요청하지 않는 한 이 기본값을 따른다.

## 1. figure 스크립트는 평소대로 쓴다

`set_xlabel`/`set_title`/`ax.text`/`legend`를 그대로 쓰면 된다. **좌표를 따로 넘길 필요가 없다** —
`fig2pptx`가 각 text artist의 렌더된 실제 위치를 읽어 텍스트를 숨긴 뒤 같은 자리에 Arial
텍스트박스를 심는다. 스크립트는 모듈 레벨에 `fig`만 남겨두면 된다.

일반적인 과학 figure 스타일 규칙(grid 금지, `plt.show()` 금지 등)은 그대로 유효하다. 이 스킬은
그 위에 출력 경로만 바꾼다.

## 2. PPTX 만들기

```python
import sys; sys.path.insert(0, "{S}")
from fig2pptx import export_figure
path, n_text, n_comp, n_vec = export_figure(fig, "output/fig3.pptx")
```

여러 개면 `runpy.run_path(script)`로 각 figure 스크립트를 재실행해 `ns["fig"]`를 회수한 뒤
`export_figure`에 넘긴다 (figure 스크립트를 고칠 필요가 없다).

기본 동작:
- `bake_ticks=True` — 눈금 숫자는 그림에 남긴다 (위 표의 규칙).
- `per_axes=True` — 패널·컬러바·구조 렌더가 각각 독립 그림 객체 (twin axes 병합, inset은 2패스).
- `vector=True` — 모든 그림 객체가 PNG blip + `asvg:svgBlip` **이중 포맷**. PowerPoint가 SVG를
  그리고 구형 뷰어는 PNG로 폴백한다. 덤으로 `<base>_flat.{png,svg}`도 나온다.
- `svg_fonttype='path'` — 그림에 남는 눈금 글자를 외곽선으로 굳힌다. `'none'`으로 두면 Windows
  PowerPoint에 Helvetica가 없어 눈금 글꼴이 조용히 바뀐다.
- `bake_legend=True` — 범례도 그림에 굽는다. 결정학 overbar(`$\bar{1}$`)처럼 PowerPoint 텍스트
  run이 제대로 조판하지 못하는 라벨이 있을 때만 쓴다.
- mathtext(`$\mathit{e}$`, `_{}`/`^{}`)는 유니코드 + 첨자 baseline run으로 변환된다.
- 텍스트 색은 matplotlib artist 색을 그대로 가져간다 (막대 안 흰 숫자 등이 PPTX에서도 유지).
- 내보내기 직후 `<base>_c00…`, `_flat`, `_graphics_full` 중간 파일은 지워도 된다 — PPTX 안에 이미
  들어 있고 `pptx2figs.py`는 디스크의 조각을 읽지 않는다. 최종 PNG·SVG는 반드시 PPTX에서
  `pptx2figs.py`로 뽑는다 (matplotlib PNG는 mathtext 첨자가 DejaVu로 찍혀 글꼴이 섞인다).

## 2b. 구조 렌더를 잘라 쓸 때 — 픽셀을 자르지 말고 PPT 자르기(srcRect)로

OVITO/POV-Ray 렌더의 일부(활성 자리 등)만 보여줄 때 matplotlib에서 배열을 잘라 `imshow` 하면
그 조각의 픽셀만 남아 확대 보간으로 흐려지고, 자른 영역이 그림에 구워져 손으로 못 고친다.
**렌더 전체를 PPTX에 넣고 PowerPoint 자르기(`<a:srcRect>`)로 보이는 영역만 정한다.** 픽셀 손실이
없고, 사용자가 자르기 핸들을 끌어 언제든 영역을 바꿀 수 있다. 렌더 해상도는 ~2600 px이면 충분하다.

```python
import sys; sys.path.insert(0, "{S}")
from fig2pptx import export_figure
from pptx_crop_swap import swap_pictures_with_crop
# figure 스크립트에서는 평소처럼 ax.imshow(crop(img))로 레이아웃만 잡는다 (자리·크기 결정용)
p, *_ = export_figure(fig, "out/fig.pptx")
swap_pictures_with_crop(p, sources, crop=0.28)   # sources = 패널 순서(행 우선)의 원본 렌더 경로들
#   crop=0.28 -> min(w,h)의 28 % 정사각 중앙 영역; crop=(l,r,t,b) 또는 패널별 리스트도 가능
#   그림으로 둘 패널(플롯)은 sources 자리에 None
# 이후 pptx2figs.py로 PNG/SVG 재생성 (PowerPoint가 자르기를 적용해 렌더한다)
```

동작: fig2pptx가 심은 패널 그림 객체를 슬라이드 위치(행 우선)로 찾아, 같은 자리·크기에 원본 전체
이미지를 넣고 `crop_left/right/top/bottom`을 설정한 뒤 옛 객체를 지우고, 참조가 끊긴 이미지 파트를
정리한다(안 하면 파일이 두 배로 커진다). 원본이 통째로 들어가므로 PPTX가 수십 MB가 되는 건
정상이고, 파생 SVG도 원본을 품어 커지니 제출은 PNG로 한다.

## 3. 사용자가 PowerPoint에서 편집한 뒤

```bash
{PY} {S}/pptx2figs.py deck.pptx
#  -> deck_final.png (PowerPoint COM 렌더, 4800 px) + deck_final.svg (완전 벡터)
#  옵션: --png-width N, --no-png, --no-svg, --suffix _x, --force-compose
```

몇 번이든 반복 가능하다. **PPTX가 원본이고 PNG·SVG는 파생물이다.**
출력에 `_final`이 붙는 이유: 덱 이름이 matplotlib 스크립트 출력과 겹쳐 덮어쓰는 사고를 막기 위함.

손으로 그린 도형(선·화살표·도형·그룹)이 섞인 덱은 조립기가 못 그리므로 **자동으로 PowerPoint
PDF → `pdftocairo -svg` 경로로 우회**한다. 도형·글자는 벡터로 살지만 사진은 ~200 ppi로
리샘플되니, 이미지 비중이 큰 그림은 PNG를 권할 것. 실행 시 그 경고가 찍힌다.

## ⛔ 다시 시도하지 말 것 (실측으로 닫힌 길)

1. **PowerPoint SVG 내보내기 없음.** `Slide.Export(...,"SVG")`는 "변환기가 설치되어 있지
   않습니다"로 실패. `SaveCopyAs` 41/42는 Invalid enumeration (40은 애니메이션 GIF).
2. **PowerPoint PDF로 벡터 뽑기 금지.** 그림을 다시 굽는다 — 일반 이미지 ~200 ppi JPEG,
   **SVG 그림은 ~101 ppi**로 더 나쁘다. `ExportAsFixedFormat` print intent는 PowerShell
   후기바인딩에서 DISP_E_TYPEMISMATCH로 막힌다. (도형이 섞인 덱의 우회로로만 쓴다.)
3. **pptx 빌더를 새로 짜지 말 것.** pptxgenjs로 좌표를 계산해 얹는 접근은 이미 폐기됐다.

## 검증하고 싶을 때

rsvg/inkscape/cairosvg가 없어도 Windows의 **headless Edge**가 Chromium 정확도로 SVG를 렌더한다:

```bash
"/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" --headless --disable-gpu \
  --no-sandbox --hide-scrollbars --force-device-scale-factor=1 \
  --screenshot="C:\...\shot.png" --window-size=1600,1145 "file:///C:/.../wrap.html"
```
(SVG를 직접 열면 창 크기에 안 맞으므로 `<img src="x.svg" style="width:1600px">` HTML로 감쌀 것.)
이 방법으로 조립 SVG와 PowerPoint 렌더를 비교하면 평균 절대차 ~5.5/255, 글자 중심 오차
1600 px 중 0.1–3.3 px 수준이다. 남은 차이는 래스터라이저 안티앨리어싱이다.

파이썬 함정: `str(PP_ALIGN.LEFT)`는 `"LEFT (1)"`이다. 정렬은 `p.alignment.name`으로 읽을 것.
