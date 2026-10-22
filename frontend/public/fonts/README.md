# Pretendard 로컬 글꼴

- 버전: Pretendard v1.3.9, 한국어 전체 가변 WOFF2
- 제작자: Kil Hyung-jin. 저작권 고지는 LICENSE.txt 참조.
- 공식 저장소: https://github.com/orioncactus/pretendard
- 고정 커밋: `5c41199ea0024a9e0b2cb31735265056e5472d76`
- 원본: https://raw.githubusercontent.com/orioncactus/pretendard/5c41199ea0024a9e0b2cb31735265056e5472d76/packages/pretendard/dist/web/variable/woff2/PretendardVariable.woff2
- 라이선스 원본: https://raw.githubusercontent.com/orioncactus/pretendard/5c41199ea0024a9e0b2cb31735265056e5472d76/LICENSE
- SIL Open Font License 1.1. 배포 시 LICENSE.txt를 함께 보존한다.
- 글꼴 바이너리와 라이선스 원문은 변경하지 않았다.

## 연결

React 진입 index.html에서 /fonts/font.css를 앱 CSS보다 먼저 불러온다. 소스 자산 위치는 public/fonts이며 Vite가 dist/fonts로 복사한다. CSS의 `Haru Pretendard`는 시스템 글꼴과 구분하는 별칭이며 바이너리 내부 이름은 변경하지 않았다. font.css는 로컬 상대경로만 사용하며 CDN이나 OS 글꼴 설치가 필요 없다. 가변 굵기 범위는 45–920, font-display는 swap이다.

## 자산 기준

| 파일 | 바이트 | SHA-256 |
|---|---:|---|
| PretendardVariable.woff2 | 2057688 | 9599f12fd42fc0bce1cd50b47a0c022e108d7aa64dd0d1bb0ed44f3282d900b4 |
| LICENSE.txt | 4418 | d31ddd9f2bed32fd7e302a205cf2380ba0de6529152d239ef99cfb6f261bfc04 |

테스트는 글꼴 해시·WOFF2 시그니처·라이선스 및 출처의 존재와 HTTP 제공을 확인한다. 실제 브라우저의 글꼴 적용·레이아웃은 별도 화면 검증 대상이다.

