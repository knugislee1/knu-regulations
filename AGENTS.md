# knu-regulations — Agent instructions (Codex, Cursor, ChatGPT, Gemini, Claude 등 공통)

This repository is a text database kit of Kyungpook National University (경북대학교) regulations: 547 documents (snapshot 2026-09-09).

- When the user says **"이거 설치해"** ("install this"): follow `INSTALL.md` — run `python3 install.py` (or `python install.py` on Windows), confirm the output contains `SELFTEST PASS` and `== 설치 완료 ==`, then report the result in 3–4 lines. Do not ask questions first.
- When the user asks about a regulation: follow `SKILL.md` — find documents (`knu_reg.py docs`), find articles (`knu_reg.py search`), read the full article (`knu_reg.py article`), check amendment history (`knu_reg.py history`), and cite 「regulation title」 article number, document number, and last amendment date.
- Without a shell: pick the document in `index.md` and read `data/text/*.txt` directly.
