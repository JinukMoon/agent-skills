---
name: snu-etl-video-downloader
description: SNU LCMS(eTL) 강의 영상을 content_id로 다운로드한다. 사용자가 content_id(들)를 주면서 "영상 다운", "강의 다운로드", "N차시 받아줘", "/snu-etl-video-downloader"라고 하면 사용. 여러 개는 병렬로 받고, videos/에 차시 규칙대로 저장한다.
---

# SNU eTL/LCMS 강의 영상 다운로드

## Input

- `content_id` 1개 이상 (예: `0f8b3c...` 형태의 해시 문자열)
- 각 영상의 차시 번호와 제목 (모르면 사용자에게 확인. 제목은 `docums/`의 PDF 제목과 맞추는 것이 관례)

## content_id 얻는 방법 (사용자가 모를 때 안내)

1. eTL(etl.snu.ac.kr) 강의 페이지에서 해당 차시 영상을 클릭해 LCMS 플레이어(lcms.snu.ac.kr)를 연다
2. 브라우저에서 **F12 → Network 탭** 열고 영상을 재생
3. 필터에 `mp4` 또는 `media_files` 입력 → `snu-cms-object.edge.naverncp.com/contents/snu0000001/{content_id}/contents/media_files/screen.mp4` 형태의 요청이 보임
4. URL 경로에서 `snu0000001/` 다음의 해시 문자열이 `content_id`
5. 대안: 플레이어 페이지에서 우클릭 → 페이지 소스 보기 → `content` 검색해도 찾을 수 있음

여러 차시를 받을 때는 차시마다 위 과정을 반복해 content_id 목록을 만든 뒤 한 번에 전달받는 것이 효율적.

## 다운로드 명령

```bash
curl 'https://snu-cms-object.edge.naverncp.com/contents/snu0000001/{content_id}/contents/media_files/screen.mp4' \
  -H 'Referer: https://lcms.snu.ac.kr/' \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36' \
  -o 'videos/{N}차시_{제목}.mp4'
```

## 규칙

1. **저장 위치·이름**: 반드시 `videos/N차시_제목.mp4` (예: `videos/5차시_Methodology.mp4`). 제목은 영문, 공백 대신 `_`.
2. **병렬 다운로드**: content_id가 여러 개면 각 curl을 `run_in_background`로 동시에 실행.
3. **헤더 필수**: `Referer` 헤더 없으면 403. 템플릿 그대로 사용.
4. **완료 확인**: 다운로드 후 파일 크기 확인 — 정상 영상은 보통 170~290MB. 수 KB면 실패(에러 페이지)이므로 내용 확인 후 재시도.
5. **다운로드 완료 후**: 사용자가 트랜스크립션도 원하면 `whisper-transcribe` skill로 이어간다.
