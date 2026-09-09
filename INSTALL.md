# 설치·학습 가이드 — AI 에이전트가 읽고 실행하는 문서

사용자가 **"이거 설치해"**(또는 "설치해줘", "세팅해", "install")라고 말하면 이 문서를 처음부터 끝까지 따라 실행한다.
사용자에게 되묻지 말고 끝까지 진행한 뒤, 마지막의 보고 형식으로 결과만 알린다. Claude, ChatGPT, Codex, Cursor, Gemini 등 어느 도구든 같다.

## 0. 이 꾸러미는 무엇인가

경북대학교 규정·예규·지침·세칙·학칙·정관 **547건의 전문 텍스트**(2026-09-09 스냅샷)와 그것을 검색하는 도구다.
- `data/text/*.txt` 547개: 문서별 전문 (한 줄 = 한 문단)
- `data/documents.csv`, `data/articles.csv`, `data/amendments.csv`: 문서·조문·제개정 이력 표
- `knu_reg.py`: 검색 도구 (python3 표준 라이브러리만 사용; 첫 실행 때 SQLite DB를 자동 생성)
- `install.py` / `install.sh`: 설치기 (OS 공통 Python / 셸 래퍼), `get.sh`: git 없이 원격 설치
- `SKILL.md`: 규정 질문에 답하는 절차와 인용 형식 (설치 후 반드시 이 문서를 따른다)
- `index.md`: 547개 문서 목록 (코드를 실행할 수 없는 환경용)

## 1. 지금 무엇을 가지고 있는지 판별

| 상황 | 할 일 |
|---|---|
| 저장소 **주소(URL)만** 받았고 셸·인터넷을 쓸 수 있다 | `git clone https://github.com/knugislee1/knu-regulations.git && cd knu-regulations` (git이 없으면 `curl -fsSL https://raw.githubusercontent.com/knugislee1/knu-regulations/main/get.sh \| bash` 한 줄로 끝) → **2단계** |
| 주소만 받았는데 셸이 없거나 인터넷이 막혀 있다 | 사용자에게 `https://github.com/knugislee1/knu-regulations/releases/latest/download/knu-regulations-kit.zip`을 받아 대화에 첨부해 달라고 요청한다. 첨부되면 → 아래 행 |
| zip이나 폴더를 가지고 있고 셸을 쓸 수 있다 (Claude Code, claude.ai·ChatGPT 코드 실행 샌드박스 등) | zip이면 푼다(`unzip -q knu-regulations-kit.zip` 또는 python zipfile) → **2단계** |
| 파일은 읽을 수 있지만 코드는 실행할 수 없다 | **4단계** |

## 2. 자동 설치 (한 줄)

```bash
python3 install.py
```
(`bash install.sh`도 같다. Windows는 `python install.py`.)

설치기가 하는 일: python3·sqlite 확인 → 데이터 확인 → 설치 위치 결정(`~/.claude`가 있으면 `~/.claude/skills/knu-regulations`에 스킬로, 없으면 현재 폴더) → DB 생성(30초 안팎) → 자가 검증(selftest).

- **성공 판정**: 출력에 `SELFTEST PASS`와 `== 설치 완료 ==`가 있어야 한다. 둘 중 하나라도 없으면 실패다. 실패를 성공처럼 보고하지 않는다.
- python3가 없으면 설치기가 안내 문구를 내고 멈춘다. 사용자에게 "Python 3.8 이상 설치가 필요하다"고 알린다.
- sqlite가 오래돼 trigram 색인이 빠지면 자동으로 생략되며 검색은 접두 검색과 LIKE로 동작한다(정상).
- 홈 폴더에 쓸 수 없으면 `python3 install.py --here`(현재 폴더) 또는 `--dest <폴더>`.

설치 뒤 확인 질의를 한 번 실행해 본다:

```bash
python3 "<설치 위치>/knu_reg.py" search 휴학 --limit 3
```

## 3. 설치 후 응대 방법

규정 관련 질문이 오면 `<설치 위치>/SKILL.md`의 절차를 따른다. 요약:
1. `docs <키워드>`로 문서를 찾고 → 2. `search <단어들>`로 조문을 찾고 → 3. `article <문서> <조>`로 **원문 전문을 읽은 뒤** → 4. 필요하면 `history <문서>`로 개정일 확인 → 5. 인용할 문장을 `verify "<인용문>"`으로 확인 → 6. 조문 원문을 " " 안에 글자 그대로 인용하고 규정명·조번호·번호·최종개정일을 붙여 답하며, 요약은 인용 아래 '풀이'로 분리한다. 원문에 없는 내용은 쓰지 않는다.
- 스냅샷(2026-09-09) 이후 개정은 없다는 점, 한글 3.0 원본 16건은 일부 누락 가능성이 있다는 점을 필요할 때 밝힌다.
- DB에 없는 내용은 "없다"고 말한다. 지어내지 않는다.

Claude Code에 스킬로 설치된 경우에는 새 세션에서도 자동으로 이 스킬이 잡힌다. 대화마다 초기화되는 샌드박스에서는 새 대화에서 zip이 첨부돼 있으면 조용히 2단계를 다시 실행한 뒤 답한다.

## 4. 코드를 실행할 수 없을 때 (파일 읽기만 가능)

1. `index.md`에서 질문과 관련된 문서를 고른다(제목·종류·번호·최종개정일이 있다).
2. 해당 문서의 `data/text/<파일명>.txt`를 열어 "제N조" 줄을 찾아 원문을 읽는다.
3. 같은 인용 형식으로 답하되, `verify`를 쓸 수 없으므로 인용은 이번 답변에서 실제로 읽은 구절만 쓰고, 인용문을 검색어로 파일을 다시 검색해 확인하며, 답 끝에 "원문 대조" 표(인용문 앞 20자 | 파일 | 문서 | 조번호)를 붙인다. 확인하지 못한 문장은 따옴표를 떼고 "요약"으로 표시한다. 파일을 열 수 없으면 사용자에게 그 파일(들)을 첨부해 달라고 요청한다.
4. 사용자가 계속 쓸 계획이면 `bundles/README.md`의 방법(NotebookLM·프로젝트·GPT에 묶음 파일 올리기)을 알려 준다.

## 5. 보고 형식 (설치 직후, 3~4줄)

```
설치 완료: <설치 위치>
검증: SELFTEST PASS (문서 547 / 조문 11,434 / 이력 2,673)
이제 경북대 규정 질문을 하시면 DB에서 조문을 찾아 규정명·조번호·개정일과 함께 답합니다. (스냅샷 2026-09-09)
```
실패했으면 실패한 단계와 원인(출력 마지막 줄)을 그대로 적는다.
