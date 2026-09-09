#!/usr/bin/env python3
"""경북대학교 규정·예규 DB 질의 도구 — 표준 라이브러리만 사용 (python3 >= 3.8).

DB(knu_regulations.sqlite)가 없으면 data/ 폴더의 CSV·텍스트에서 자동으로 만든다.

  python3 knu_reg.py docs 휴학                 # 제목에 '휴학'이 들어간 문서 목록
  python3 knu_reg.py search 휴학 학점           # 조문 전문검색 (모든 단어 포함, 접두 일치)
  python3 knu_reg.py article 학칙 45           # 「경북대학교 학칙」 제45조 전문
  python3 knu_reg.py show 8                    # 문서 8의 개요 + 조문 목록 (--full: 전문)
  python3 knu_reg.py history 8                 # 문서 8의 제·개정 이력
  python3 knu_reg.py grep "정당한 사유"          # 전체 텍스트 정규식 검색 (줄 단위)
  python3 knu_reg.py verify "학사과정: 6개 학기 이내"   # 인용문이 원문에 글자 그대로 있는지 확인 (환각 방지)
  python3 knu_reg.py sql "SELECT ..."          # 읽기 전용 SQL
  python3 knu_reg.py selftest                  # 설치 자가 검증
  python3 knu_reg.py build --force             # DB 재생성
어느 명령이든 --json 을 붙이면 JSON으로 출력한다.
"""
import sys, os, re, csv, json, sqlite3, argparse, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data')
DB = os.path.join(HERE, 'knu_regulations.sqlite')
csv.field_size_limit(min(sys.maxsize, 2**31 - 1))

SCHEMA = """
CREATE TABLE documents (
  doc_id INTEGER PRIMARY KEY, filename TEXT UNIQUE NOT NULL, title TEXT, kind TEXT,
  number_type TEXT, number INTEGER, number_source TEXT,
  enacted_date TEXT, enacted_number_type TEXT, enacted_number INTEGER,
  first_history_action TEXT, first_history_date TEXT, last_amended_date TEXT, last_amended_action TEXT,
  n_amendments INTEGER, n_articles INTEGER, n_chapters INTEGER, n_appendices INTEGER, n_attachments INTEGER,
  n_chars INTEGER, n_pua INTEGER, hwp_format TEXT, extractor TEXT, extraction_note TEXT, status TEXT, error TEXT,
  hwp_created_utc TEXT, hwp_modified_utc TEXT, file_bytes INTEGER, md5 TEXT, is_duplicate INTEGER, duplicate_of TEXT,
  text_path TEXT, full_text TEXT);
CREATE TABLE amendments (id INTEGER PRIMARY KEY, doc_id INTEGER REFERENCES documents(doc_id), seq INTEGER,
  action TEXT, date TEXT, number_type TEXT, number INTEGER, raw TEXT);
CREATE TABLE articles (id INTEGER PRIMARY KEY, doc_id INTEGER REFERENCES documents(doc_id), seq INTEGER,
  part TEXT, part_seq INTEGER, part_label TEXT, chapter TEXT, section TEXT, article_no TEXT, article_title TEXT,
  text TEXT, n_chars INTEGER);
CREATE INDEX idx_articles_doc ON articles(doc_id); CREATE INDEX idx_articles_no ON articles(article_no);
CREATE INDEX idx_amend_doc ON amendments(doc_id); CREATE INDEX idx_amend_date ON amendments(date);
CREATE INDEX idx_docs_kind ON documents(kind); CREATE INDEX idx_docs_number ON documents(number_type, number);
CREATE VIRTUAL TABLE documents_fts USING fts5(title, full_text, content='documents', content_rowid='doc_id', tokenize='unicode61');
CREATE VIRTUAL TABLE articles_fts USING fts5(article_no, article_title, text, content='articles', content_rowid='id', tokenize='unicode61');
CREATE VIEW v_documents_unique AS SELECT * FROM documents WHERE is_duplicate = 0 AND status = 'ok';
CREATE VIEW v_articles AS SELECT a.id, a.doc_id, d.title AS doc_title, d.kind, d.number_type, d.number, a.part, a.part_seq, a.part_label,
  a.chapter, a.section, a.article_no, a.article_title, a.text, a.n_chars, d.filename, d.is_duplicate FROM articles a JOIN documents d USING(doc_id);
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
"""
DOC_COLS = ['doc_id', 'filename', 'title', 'kind', 'number_type', 'number', 'number_source', 'enacted_date', 'enacted_number_type',
            'enacted_number', 'first_history_action', 'first_history_date', 'last_amended_date', 'last_amended_action', 'n_amendments',
            'n_articles', 'n_chapters', 'n_appendices', 'n_attachments', 'n_chars', 'n_pua', 'hwp_format', 'extractor', 'extraction_note',
            'status', 'error', 'hwp_created_utc', 'hwp_modified_utc', 'file_bytes', 'md5', 'is_duplicate', 'duplicate_of', 'text_path']
INT_COLS = {'doc_id', 'number', 'enacted_number', 'n_amendments', 'n_articles', 'n_chapters', 'n_appendices', 'n_attachments', 'n_chars',
            'n_pua', 'file_bytes', 'is_duplicate', 'id', 'seq', 'part_seq'}

def _val(col, v):
    if v is None or v == '': return None
    return int(v) if col in INT_COLS else v

def _read_csv(name):
    with open(os.path.join(DATA, name), encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def build(force=False, quiet=False):
    """data/*.csv + data/text/*.txt → knu_regulations.sqlite"""
    if os.path.exists(DB):
        if not force: return
        os.remove(DB)
    say = (lambda *a: None) if quiet else (lambda *a: print(*a, file=sys.stderr))
    manifest = json.load(open(os.path.join(DATA, 'manifest.json'), encoding='utf-8'))
    con = sqlite3.connect(DB); con.executescript(SCHEMA)
    say('문서 적재 중...')
    for r in _read_csv('documents.csv'):
        tp = os.path.join(DATA, 'text', r['filename'][:-4] + '.txt')
        full = open(tp, encoding='utf-8').read() if os.path.exists(tp) else None
        vals = [_val(c, r.get(c)) for c in DOC_COLS]; vals[DOC_COLS.index('text_path')] = os.path.relpath(tp, HERE)
        con.execute('INSERT INTO documents VALUES (%s)' % ','.join('?' * (len(DOC_COLS) + 1)), vals + [full])
    say('이력 적재 중...')
    for r in _read_csv('amendments.csv'):
        con.execute('INSERT INTO amendments VALUES (?,?,?,?,?,?,?,?)',
                    [_val(c, r.get(c)) for c in ('id', 'doc_id', 'seq', 'action', 'date', 'number_type', 'number', 'raw')])
    say('조문 적재 중...')
    for r in _read_csv('articles.csv'):
        con.execute('INSERT INTO articles VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                    [_val(c, r.get(c)) for c in ('id', 'doc_id', 'seq', 'part', 'part_seq', 'part_label', 'chapter', 'section',
                                                 'article_no', 'article_title', 'text', 'n_chars')])
    say('전문검색 색인 생성 중...')
    for t in ('documents_fts', 'articles_fts'): con.execute(f"INSERT INTO {t}({t}) VALUES('rebuild')")
    tri = 'no'
    try:
        con.execute("CREATE VIRTUAL TABLE articles_fts_tri USING fts5(text, content='articles', content_rowid='id', tokenize='trigram')")
        con.execute("INSERT INTO articles_fts_tri(articles_fts_tri) VALUES('rebuild')"); tri = 'yes'
    except sqlite3.OperationalError:
        say('  (sqlite가 trigram 토크나이저를 지원하지 않아 부분문자열 색인은 생략)')
    con.executemany('INSERT INTO meta VALUES (?,?)', [('built_at', datetime.datetime.now().isoformat(timespec='seconds')),
                                                      ('source_snapshot', manifest.get('snapshot_date', '')), ('trigram', tri),
                                                      ('kit_version', manifest.get('kit_version', ''))])
    con.commit(); con.close(); say('완료:', DB)

def connect():
    build(quiet=True)
    return sqlite3.connect('file:%s?mode=ro' % DB, uri=True)

def has_trigram(con):
    return con.execute("SELECT value FROM meta WHERE key='trigram'").fetchone()[0] == 'yes'

# ---------- 출력 ----------
def out(rows, cols, args, title=None):
    if getattr(args, 'json', False):
        print(json.dumps([dict(zip(cols, r)) for r in rows], ensure_ascii=False, indent=1)); return
    if title: print(title)
    if not rows: print('  (결과 없음)'); return
    for r in rows:
        print('  ' + ' | '.join('' if v is None else str(v).replace('\n', ' ⏎ ') for v in r))

def resolve_doc(con, key, unique=True):
    """숫자면 doc_id, 아니면 제목 부분일치. 정확히 하나면 doc_id 반환, 여럿이면 후보를 출력하고 None."""
    if re.fullmatch(r'\d+', key.strip()):
        r = con.execute('SELECT doc_id FROM documents WHERE doc_id=?', (int(key),)).fetchone()
        return r[0] if r else None
    kws = key.split()
    where = ' AND '.join(['title LIKE ?'] * len(kws)) + (' AND is_duplicate=0' if unique else '')
    rows = con.execute(f'SELECT doc_id, kind, number_type, number, title FROM documents WHERE {where} ORDER BY length(title)',
                       [f'%{k}%' for k in kws]).fetchall()
    exact = [r for r in rows if r[4].replace(' ', '') == key.replace(' ', '')]
    if len(exact) == 1: return exact[0][0]
    if len(rows) == 1: return rows[0][0]
    if not rows: print(f'문서를 찾지 못함: {key!r}  (docs 명령으로 제목을 확인하세요)'); return None
    print(f'후보가 {len(rows)}개입니다. doc_id로 다시 지정하세요:')
    for r in rows[:30]: print(f'  {r[0]:4d} | {r[1] or ""} | {r[2] or ""} {r[3] or ""} | {r[4]}')
    return None

def fts_query(text):
    toks = re.findall(r'[0-9A-Za-z가-힣]+', text)
    return ' '.join(f'{t}*' for t in toks), toks

# ---------- 명령 ----------
def cmd_docs(con, args):
    kws = args.keywords
    where = ' AND '.join(['title LIKE ?'] * len(kws)) if kws else '1=1'
    if not args.all: where += ' AND is_duplicate=0'
    if args.kind: where += ' AND kind=?'
    params = [f'%{k}%' for k in kws] + ([args.kind] if args.kind else [])
    rows = con.execute(f"""SELECT doc_id, kind, COALESCE(number_type,'')||' '||COALESCE(number,''), enacted_date, last_amended_date, n_articles, title
                           FROM documents WHERE {where} ORDER BY title""", params).fetchall()
    out(rows, ['doc_id', 'kind', 'number', 'enacted', 'last_amended', 'n_articles', 'title'], args, f'문서 {len(rows)}건 (doc_id | 종류 | 번호 | 제정 | 최종개정 | 조문수 | 제목)')

def cmd_search(con, args):
    q, toks = fts_query(' '.join(args.query))
    if not toks: print('검색어가 없습니다.'); return
    filt = "AND d.is_duplicate=0" + (" AND d.kind=?" if args.kind else '') + (" AND a.doc_id=?" if args.doc else '') + (" AND a.part=?" if args.part else '')
    params = ([args.kind] if args.kind else []) + ([int(args.doc)] if args.doc else []) + ([args.part] if args.part else [])
    sql = f"""SELECT d.doc_id, d.title, a.part, a.article_no, a.article_title, snippet(articles_fts, 2, '[', ']', '…', 18)
              FROM articles_fts f JOIN articles a ON a.id=f.rowid JOIN documents d USING(doc_id)
              WHERE articles_fts MATCH ? {filt} ORDER BY bm25(articles_fts) LIMIT ?"""
    rows = con.execute(sql, [q] + params + [args.limit]).fetchall(); how = f'어절 접두 검색 ({q})'
    if not rows and has_trigram(con) and all(len(t) >= 3 for t in toks):
        tq = ' AND '.join(f'"{t}"' for t in toks)
        sql = f"""SELECT d.doc_id, d.title, a.part, a.article_no, a.article_title, snippet(articles_fts_tri, 0, '[', ']', '…', 18)
                  FROM articles_fts_tri f JOIN articles a ON a.id=f.rowid JOIN documents d USING(doc_id)
                  WHERE articles_fts_tri MATCH ? {filt} ORDER BY bm25(articles_fts_tri) LIMIT ?"""
        rows = con.execute(sql, [tq] + params + [args.limit]).fetchall(); how = f'부분문자열 검색 ({tq})'
    if not rows:
        like = ' AND '.join(['a.text LIKE ?'] * len(toks))
        sql = f"""SELECT d.doc_id, d.title, a.part, a.article_no, a.article_title, substr(a.text, 1, 80)
                  FROM articles a JOIN documents d USING(doc_id) WHERE {like} {filt} LIMIT ?"""
        rows = con.execute(sql, [f'%{t}%' for t in toks] + params + [args.limit]).fetchall(); how = 'LIKE 검색'
    out(rows, ['doc_id', 'doc_title', 'part', 'article_no', 'article_title', 'snippet'], args,
        f'{how}: {len(rows)}건 (doc_id | 문서 | 구분 | 조 | 조제목 | 발췌)  — 전문은 article 명령으로 확인')

def norm_article_no(s):
    s = s.strip().replace(' ', '')
    m = re.fullmatch(r'(?:제)?(\d+)(?:조)?(?:의(\d+))?', s)
    if not m: return s
    return f'제{m.group(1)}조' + (f'의{m.group(2)}' if m.group(2) else '')

def cmd_article(con, args):
    did = resolve_doc(con, args.doc)
    if did is None: return
    no = norm_article_no(args.article_no)
    rows = con.execute("""SELECT a.part, a.part_label, a.chapter, a.section, a.article_no, a.article_title, a.text
                          FROM articles a WHERE doc_id=? AND article_no=? ORDER BY CASE part WHEN 'body' THEN 0 ELSE 1 END, seq""", (did, no)).fetchall()
    if args.part: rows = [r for r in rows if r[0] == args.part]
    d = con.execute("SELECT title, kind, number_type, number, last_amended_date, extraction_note FROM documents WHERE doc_id=?", (did,)).fetchone()
    if getattr(args, 'json', False):
        print(json.dumps({'doc_id': did, 'title': d[0], 'kind': d[1], 'number': f'{d[2] or ""} {d[3] or ""}'.strip(), 'last_amended': d[4],
                          'matches': [dict(zip(['part', 'part_label', 'chapter', 'section', 'article_no', 'article_title', 'text'], r)) for r in rows]}, ensure_ascii=False, indent=1)); return
    print(f'「{d[0]}」 ({d[1]}, {d[2] or ""} 제{d[3] or "?"}호, 최종개정 {d[4] or "?"})  doc_id={did}')
    if d[5]: print(f'  ※ 추출 주의: {d[5]}')
    if not rows: print(f'  {no} 을(를) 찾지 못함. show 명령으로 조문 목록을 확인하세요.'); return
    for r in rows:
        loc = ' / '.join(x for x in (r[0] if r[0] != 'body' else None, r[1], r[2], r[3]) if x)
        print(f'--- {r[4]}{"(" + r[5] + ")" if r[5] else ""}  [{loc or "본문"}]'); print(r[6])

def cmd_show(con, args):
    did = resolve_doc(con, args.doc)
    if did is None: return
    d = con.execute("""SELECT doc_id, title, kind, number_type, number, enacted_date, last_amended_date, n_amendments, n_articles, n_appendices,
                       n_attachments, hwp_format, extraction_note, filename, full_text FROM documents WHERE doc_id=?""", (did,)).fetchone()
    if args.full:
        print(d[14]); return
    print(f'doc_id={d[0]}  「{d[1]}」  종류={d[2]}  번호={d[3] or ""} 제{d[4] or "?"}호  제정={d[5]}  최종개정={d[6]}  이력={d[7]}건  조문={d[8]}  부칙={d[9]}  별표/별지={d[10]}  원본형식={d[11]}')
    print(f'  파일: {d[13]}')
    if d[12]: print(f'  ※ 추출 주의: {d[12]}')
    rows = con.execute("SELECT part, part_label, chapter, article_no, article_title, n_chars FROM articles WHERE doc_id=? ORDER BY seq", (did,)).fetchall()
    cur = None
    for part, label, ch, no, at, n in rows:
        head = label if part != 'body' else (ch or '')
        if head != cur: cur = head; print(f'  [{part}] {head}' if head else f'  [{part}]')
        if no: print(f'      {no}{"(" + at + ")" if at else ""}  ({n}자)')

def cmd_history(con, args):
    did = resolve_doc(con, args.doc)
    if did is None: return
    rows = con.execute("SELECT seq, action, date, number_type, number, raw FROM amendments WHERE doc_id=? ORDER BY seq", (did,)).fetchall()
    t = con.execute("SELECT title FROM documents WHERE doc_id=?", (did,)).fetchone()[0]
    out(rows, ['seq', 'action', 'date', 'number_type', 'number', 'raw'], args, f'「{t}」 제·개정 이력 {len(rows)}건 (순번 | 구분 | 날짜 | 유형 | 번호 | 원문)')

def cmd_grep(con, args):
    pat = re.compile(args.pattern); rows = []
    for did, title, ft in con.execute("SELECT doc_id, title, full_text FROM documents WHERE is_duplicate=0 AND full_text IS NOT NULL"):
        for i, line in enumerate(ft.split('\n'), 1):
            if pat.search(line):
                rows.append((did, title, i, line.strip()[:160]))
                if len(rows) >= args.limit: break
        if len(rows) >= args.limit: break
    out(rows, ['doc_id', 'title', 'line', 'text'], args, f'정규식 /{args.pattern}/ : {len(rows)}건 (doc_id | 문서 | 줄 | 내용)')

def _norm_q(s): return re.sub(r'\s+', '', s).replace('…', '').replace('...', '')

def cmd_verify(con, args):
    """인용문(공백·줄바꿈 무시)이 어느 문서의 어느 조문에 글자 그대로 있는지 확인한다. '…'로 자른 조각은 각각 검사한다."""
    pieces = [p for p in re.split(r'…|\.\.\.', args.quote) if _norm_q(p)]
    if not pieces: print('인용문이 비어 있습니다.'); return
    rows = con.execute("SELECT a.doc_id, d.title, a.part, a.part_label, a.article_no, a.article_title, a.text FROM articles a JOIN documents d USING(doc_id) WHERE d.is_duplicate=0").fetchall()
    results = []
    for piece in pieces:
        key = _norm_q(piece); hits = [r for r in rows if key in _norm_q(r[6] or '')]
        results.append({'quote': piece.strip(), 'found': bool(hits), 'n_chars': len(key),
                        'hits': [{'doc_id': r[0], 'title': r[1], 'part': r[2], 'part_label': r[3], 'article_no': r[4], 'article_title': r[5]} for r in hits[:5]]})
    if getattr(args, 'json', False): print(json.dumps(results, ensure_ascii=False, indent=1)); return
    ok = all(r['found'] for r in results)
    for r in results:
        if r['found']:
            h = r['hits'][0]; where = f"「{h['title']}」 {h['article_no'] or ''}{'(' + h['article_title'] + ')' if h['article_title'] else ''} [{h['part'] if h['part'] != 'body' else '본문'}{' ' + h['part_label'] if h['part_label'] else ''}]"
            more = f"  (+{len(r['hits']) - 1}곳 더)" if len(r['hits']) > 1 else ''
            print(f"  FOUND  {where}{more}  ← \"{r['quote'][:60]}\"")
        else:
            print(f"  NOT FOUND  ← \"{r['quote'][:60]}\"  (원문에 이 문장이 없음: 인용 금지, article 출력에서 다시 복사할 것)")
    print('VERIFY', 'PASS' if ok else 'FAIL')

def cmd_sql(con, args):
    if not re.match(r'^\s*(select|with|pragma|explain)\b', args.query, re.I): print('읽기 전용: SELECT/WITH만 허용'); return
    cur = con.execute(args.query); rows = cur.fetchmany(args.limit); cols = [c[0] for c in cur.description]
    out(rows, cols, args, ' | '.join(cols))

def cmd_selftest(con, args):
    m = json.load(open(os.path.join(DATA, 'manifest.json'), encoding='utf-8')); ok = True
    def chk(name, got, exp):
        nonlocal ok; good = (got == exp); ok &= good; print(f'  {"PASS" if good else "FAIL"}  {name}: {got} (기대 {exp})')
    chk('documents', con.execute('SELECT count(*) FROM documents').fetchone()[0], m['n_documents'])
    chk('articles', con.execute('SELECT count(*) FROM articles').fetchone()[0], m['n_articles'])
    chk('amendments', con.execute('SELECT count(*) FROM amendments').fetchone()[0], m['n_amendments'])
    chk('total_chars', con.execute('SELECT sum(n_chars) FROM documents').fetchone()[0], m['total_chars'])
    chk('full_text loaded', con.execute('SELECT count(*) FROM documents WHERE full_text IS NOT NULL').fetchone()[0], m['n_documents'])
    chk('fts docs rows', con.execute('SELECT count(*) FROM documents_fts').fetchone()[0], m['n_documents'])
    n = con.execute("SELECT count(*) FROM articles_fts WHERE articles_fts MATCH '휴학*'").fetchone()[0]; chk('fts search 휴학* >0', n > 0, True)
    print(f'  INFO  trigram 부분문자열 색인: {"있음" if has_trigram(con) else "없음"}  |  스냅샷 {m.get("snapshot_date")}  |  kit {m.get("kit_version")}')
    print('SELFTEST', 'PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)

def main(argv=None):
    p = argparse.ArgumentParser(description='경북대학교 규정·예규 DB 질의 도구'); p.add_argument('--json', action='store_true', help='JSON 출력')
    sp = p.add_subparsers(dest='cmd', required=True)
    a = sp.add_parser('docs', help='제목으로 문서 찾기'); a.add_argument('keywords', nargs='*'); a.add_argument('--kind'); a.add_argument('--all', action='store_true', help='중복 파일 포함')
    a = sp.add_parser('search', help='조문 전문검색'); a.add_argument('query', nargs='+'); a.add_argument('--kind'); a.add_argument('--doc'); a.add_argument('--part'); a.add_argument('--limit', type=int, default=20)
    a = sp.add_parser('article', help='조문 전문 보기'); a.add_argument('doc'); a.add_argument('article_no'); a.add_argument('--part')
    a = sp.add_parser('show', help='문서 개요/전문'); a.add_argument('doc'); a.add_argument('--full', action='store_true')
    a = sp.add_parser('history', help='제·개정 이력'); a.add_argument('doc')
    a = sp.add_parser('grep', help='정규식 검색'); a.add_argument('pattern'); a.add_argument('--limit', type=int, default=50)
    a = sp.add_parser('verify', help='인용문이 원문에 있는지 확인'); a.add_argument('quote')
    a = sp.add_parser('sql', help='읽기 전용 SQL'); a.add_argument('query'); a.add_argument('--limit', type=int, default=200)
    sp.add_parser('selftest', help='설치 자가 검증')
    a = sp.add_parser('build', help='DB 생성'); a.add_argument('--force', action='store_true')
    args = p.parse_args(argv)
    if args.cmd == 'build': build(force=args.force); return
    con = connect()
    {'docs': cmd_docs, 'search': cmd_search, 'article': cmd_article, 'show': cmd_show, 'history': cmd_history,
     'grep': cmd_grep, 'verify': cmd_verify, 'sql': cmd_sql, 'selftest': cmd_selftest}[args.cmd](con, args)

if __name__ == '__main__':
    main()
