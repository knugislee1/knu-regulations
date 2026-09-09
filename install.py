#!/usr/bin/env python3
"""경북대학교 규정·예규 DB 꾸러미 설치기 — Windows / macOS / Linux 공통, 표준 라이브러리만 사용.

  python3 install.py            # ~/.claude 가 있으면 ~/.claude/skills/knu-regulations 에 스킬로 설치, 없으면 이 폴더에 설치
  python3 install.py --here     # 항상 이 폴더에 설치
  python3 install.py --dest DIR # 지정한 폴더에 설치
성공하면 마지막에 'SELFTEST PASS' 와 '== 설치 완료 ==' 를 출력하고 종료 코드 0을 돌려준다.
"""
import sys, os, shutil, subprocess, argparse, zipfile

KIT = os.path.dirname(os.path.abspath(__file__))
COPY_FILES = ['SKILL.md', 'knu_reg.py', 'INSTALL.md', 'index.md', 'README.md', 'CLAUDE.md', 'AGENTS.md']

def fail(msg):
    print('✗ ' + msg); sys.exit(1)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--here', action='store_true'); ap.add_argument('--dest'); a = ap.parse_args()
    try: sys.stdout.reconfigure(line_buffering=True)   # 자식 프로세스 출력과 순서가 섞이지 않게
    except Exception: pass
    print('== 경북대학교 규정·예규 DB 꾸러미 설치 시작 ==')
    if sys.version_info < (3, 8): fail(f'Python 3.8 이상이 필요합니다 (현재 {sys.version.split()[0]}).')
    import sqlite3; print(f'  python {sys.version.split()[0]} / sqlite {sqlite3.sqlite_version} / {sys.platform}')
    # 데이터 확인
    if not os.path.isdir(os.path.join(KIT, 'data', 'text')):
        dz = os.path.join(KIT, 'data.zip')
        if os.path.exists(dz): print('  data.zip 압축 해제...'); zipfile.ZipFile(dz).extractall(KIT)
        else: fail('data/ 폴더가 없습니다. 꾸러미가 온전한지 확인하세요.')
    n_txt = len([f for f in os.listdir(os.path.join(KIT, 'data', 'text')) if f.endswith('.txt')]); print(f'  텍스트 파일 {n_txt}개 확인')
    # 설치 위치
    claude_dir = os.path.expanduser('~/.claude')
    if a.dest: dest = os.path.abspath(a.dest)
    elif a.here or not os.path.isdir(claude_dir): dest = KIT
    else: dest = os.path.join(claude_dir, 'skills', 'knu-regulations')
    if dest != KIT:
        print(f'  Claude Code 환경 감지 → 스킬로 설치: {dest}' if dest.startswith(claude_dir) else f'  설치 위치: {dest}')
        os.makedirs(dest, exist_ok=True)
        for p in ('data', 'knu_regulations.sqlite'):
            t = os.path.join(dest, p)
            if os.path.isdir(t): shutil.rmtree(t)
            elif os.path.exists(t): os.remove(t)
        shutil.copytree(os.path.join(KIT, 'data'), os.path.join(dest, 'data'))
        for f in COPY_FILES:
            if os.path.exists(os.path.join(KIT, f)): shutil.copy(os.path.join(KIT, f), os.path.join(dest, f))
    else:
        print(f'  이 폴더에 설치: {dest}')
    # DB 생성 + 자가 검증 (별도 프로세스로 실행해 설치기와 독립)
    tool = os.path.join(dest, 'knu_reg.py')
    print('  DB 생성 중 (30초 안팎)...')
    r = subprocess.run([sys.executable, tool, 'build', '--force'], stderr=subprocess.DEVNULL)
    if r.returncode != 0: fail('DB 생성에 실패했습니다. 다음 명령으로 원인을 보세요: python3 "%s" build --force' % tool)
    r = subprocess.run([sys.executable, tool, 'selftest'])
    if r.returncode != 0: fail('자가 검증(selftest)에 실패했습니다.')
    py = 'python' if sys.platform.startswith('win') else 'python3'
    print(f'''
== 설치 완료 ==
설치 위치 : {dest}
질의 도구 : {py} "{tool}" <명령>
  docs 휴학 / search 휴학 학점 / article 학칙 45 / show 8 / history 8 / grep "정당한 사유" / sql "SELECT ..."
응대 지침 : {os.path.join(dest, "SKILL.md")}  (규정 질문에 답할 때 이 문서의 절차·인용 형식을 따를 것)''')

if __name__ == '__main__':
    main()
