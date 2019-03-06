# Rosemary
GUI Program for manga download & management
> Notice: This program is under-develop and for personal purpose. Please don't use this program :-<

## Introduction

지정 사이트의 만화를 다운로드하고 다운로드한 만화를 관리하기 위한 GUI 프로그램

1. 지정 사이트의 만화목록을 크롤링하여 신규 업로드된 만화 리스트를 사용자에게 표시
2. 신규 업로드된 만화를 다운로드하여 ZIP 파일로 압축 및 프로그램 파일 관리 정책에 맞는 파일명 부여
3. 사용자가 지정한 위치의 ZIP파일명을 분석하여 프로그램 관리 정책에 부합하는 만화 파일들을 List-Up
4. 사용자가 만화를 삭제하거나 이동하거나 감상하기 위한 기능 제공

## Development Spec

- Python 3.0
- PyQt 5
- Firestore REST API
- Selenium
- ETC *(ref. requirements.txt)*

## Future Works
- Download Controller의 Interface화

## History
#### 2019-03-06
- Hitomi Controller 추가 완료
#### 2019-03-05
- Gallery, FirebaseClient 분리 및 상호의존성 제거
- Hitomi Controller 추가(under develop)
#### 2019-02-26
- Download Thread Pool 제거
- requests-future 적용
- 상위 파일 복사 기능 수정
#### 2019-02-25
- Download Thread Pool 상한 제한 추가 - *(feature)*
- 설정에서 Thread Pool 상한 설정 기능 추가
#### 2019-02-21
- 빌드 전용 파일 추가
- requests Exception catch 로직 추가
- Logger 개선
- 수동 DB 입력 기능 추가
#### 2019-02-20
- README.md 추가
- 신규 Repository 이관
