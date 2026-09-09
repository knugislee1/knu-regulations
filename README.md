# 경북대학교 규정·예규 DB 꾸러미 (knu-regulations)

> **AI 에이전트에게 (Claude, ChatGPT, Codex, Cursor, Gemini 등)** — 사용자가 이 주소와 함께 **"이거 설치해"**라고 하면:
> 1. 셸을 쓸 수 있으면 아래 한 줄을 실행하고, 출력에 `SELFTEST PASS`와 `== 설치 완료 ==`가 있는지 확인한 뒤 [INSTALL.md](INSTALL.md) 3절대로 응대한다. 되묻지 않는다.
>    `git clone https://github.com/knugislee1/knu-regulations.git && cd knu-regulations && python3 install.py`
>    (git이 없으면 `curl -fsSL https://raw.githubusercontent.com/knugislee1/knu-regulations/main/get.sh | bash`, Windows는 `python install.py`)
> 2. 셸이 없거나 인터넷이 막힌 샌드박스면, 사용자에게 [꾸러미 zip](https://github.com/knugislee1/knu-regulations/releases/latest/download/knu-regulations-kit.zip)을 받아 대화에 첨부해 달라고 한 뒤 [INSTALL.md](INSTALL.md)를 따른다.
> 3. 설치 뒤 규정 질문에는 [SKILL.md](SKILL.md)의 절차와 인용 형식을 따른다.

경북대학교 규정·예규·지침·세칙·학칙·정관 **547건의 전문 텍스트**(2026-09-09 스냅샷)와, 그것을 문서·조문·제개정 이력 단위로 검색하는 도구입니다.
설치에 필요한 것은 Python 3.8 이상뿐입니다(외부 패키지·인터넷 불필요). 설치하면 SQLite DB가 만들어지고, AI 도우미가 규정 질문에 조문 원문을 찾아 규정명·조번호·개정일과 함께 답하게 됩니다.

## 사람이 할 일

| 사용하는 환경 | 할 일 |
|---|---|
| 컴퓨터에 설치된 AI 도구 (Claude Code, Codex, Cursor 등) | 대화창에 `https://github.com/knugislee1/knu-regulations 이거 설치해` 라고 입력. 끝. |
| 웹 채팅 AI (claude.ai, ChatGPT 등 — 샌드박스가 인터넷을 못 씀) | [꾸러미 zip](https://github.com/knugislee1/knu-regulations/releases/latest/download/knu-regulations-kit.zip)을 받아 대화에 첨부하고 "이거 설치해". claude.ai 프로젝트라면 zip을 프로젝트 지식에 올리고 [PROJECT_INSTRUCTIONS.md](PROJECT_INSTRUCTIONS.md) 내용을 프로젝트 지침에 붙여넣기. |
| 터미널에서 직접 | `git clone https://github.com/knugislee1/knu-regulations.git && cd knu-regulations && python3 install.py` (Windows: `python install.py`) |
| git 없이 한 줄 | `curl -fsSL https://raw.githubusercontent.com/knugislee1/knu-regulations/main/get.sh \| bash` → `~/knu-regulations-kit`에 설치 |

설치 위치: Claude Code가 있는 컴퓨터(`~/.claude` 폴더가 있음)에서는 `~/.claude/skills/knu-regulations`에 **스킬**로 들어가 이후 어느 프로젝트·세션에서든 자동으로 쓰입니다. 그 밖에는 저장소 폴더 안에 설치됩니다.

## 설치되면

```bash
python3 knu_reg.py docs 휴학              # 제목에 '휴학'이 들어간 문서
python3 knu_reg.py search 휴학 학점        # 조문 전문검색 (어절 접두 → 부분문자열 → LIKE 순으로 자동 완화)
python3 knu_reg.py article 학칙 45        # 「경북대학교 학칙」 제45조 전문
python3 knu_reg.py history 8              # 제·개정 이력
python3 knu_reg.py grep "정당한 사유"       # 정규식 검색
python3 knu_reg.py sql "SELECT ..."       # 읽기 전용 SQL
```

AI 도우미는 [SKILL.md](SKILL.md)에 따라 ① 문서 찾기 → ② 조문 찾기 → ③ **조문 원문 전문 읽기** → ④ 개정일 확인 → ⑤ 「규정명」 제N조(제목), 문서 번호, 최종개정일을 인용해 답합니다. DB에 없는 내용은 없다고 말하고, 스냅샷 시점 이후 개정은 반영되지 않았음을 알립니다.

## 저장소 구성

| 파일 | 용도 |
|---|---|
| `INSTALL.md` | AI가 읽는 설치·응대 가이드 ("이거 설치해"의 진입점) |
| `install.py` / `install.sh` | 설치기 (OS 공통 Python / 셸 래퍼) |
| `get.sh` | git 없이 원격 설치하는 한 줄 스크립트 |
| `SKILL.md` | 규정 질문 응대 절차·인용 형식 (Claude Code 스킬 정의 겸용) |
| `CLAUDE.md`, `AGENTS.md` | 저장소를 연 AI 도구가 자동으로 읽는 짧은 지시문 |
| `knu_reg.py` | 검색 도구 (DB 자동 생성 포함) |
| `PROJECT_INSTRUCTIONS.md` | claude.ai 프로젝트 지침에 붙여넣을 텍스트 |
| `index.md` | 547개 문서 목록 (코드를 실행할 수 없는 환경용) |
| `data/` | 문서별 전문 텍스트 547개 + 문서·조문·이력 CSV + manifest |

## 알아 둘 것

- **공식 규정집이 아닙니다.** 2026-09-09 이후 개정은 들어 있지 않습니다. 법적 효력이 필요한 사항은 경북대학교 규정집 원본으로 확인하세요.
- 한글 3.0 형식 원본 16건(주로 1984~2006년 연구소 규정)은 변환 시 표·일부 문단이 빠졌고, 복구한 조각을 문서 끝에 붙여 두었습니다. AI가 이 문서를 인용할 때는 그 한계를 함께 말하도록 되어 있습니다.
- 내용이 완전히 같은 파일 4쌍(파일명 끝 " (1)")은 기본 검색에서 제외됩니다.
- 갱신(관리자용): 원본 hwp가 바뀌면 `build_db.py`로 DB를 다시 만들고 `make_kit.py`로 이 저장소 내용을 다시 생성해 커밋합니다.

## 라이선스

코드는 MIT. 규정 원문의 권리는 경북대학교에 있으며, 이 저장소의 텍스트는 검색 편의를 위한 사본입니다. 자세한 내용은 [LICENSE](LICENSE).
