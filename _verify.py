import pathlib, sys
root = pathlib.Path(__file__).parent
dirs = ['01_CORE','02_MEMBRANE','03_SYNAPSE','04_OBSERVER','05_OUTPUT','99_ARCHIVE']
lines = []
lines.append('=== NEW SPATIAL STRUCTURE VERIFICATION ===')
ok = True
for d in dirs:
    p = root/d
    if p.exists() and p.is_dir():
        cnt = sum(1 for _ in p.rglob('*') if _.is_file())
        lines.append(f'  {d:20s} EXISTS  ({cnt} files)')
    else:
        lines.append(f'  {d:20s} MISSING'); ok = False
lines.append('')
lines.append('=== NO-OVERWRITE INVARIANT CHECK (originals preserved) ===')
for src in ['neurosovereign','neuro_stack_final.toml','k8s','terraform','layers','state',
            'science-codeevolve','self_improving_coding_agent','verus',
            'SECURITY_ANALYSIS.md','cross_platform_signing.py','deploy_optimized_system.sh']:
    p = root/src
    lines.append(f'  orig {src:35s} {"preserved" if p.exists() else "MISSING (BAD)"}')
    if not p.exists(): ok = False
lines.append('')
lines.append('=== NEW SPATIAL TREE (depth 2) ===')
def walk(p, depth=0):
    if depth > 2: return
    for child in sorted(p.iterdir()):
        if child.name == '.git' or child.name == '_inventory.txt' or child.name == '_inventory2.txt':
            continue
        prefix = '  '*depth
        if child.is_dir():
            lines.append(f'{prefix}{child.name}/')
            walk(child, depth+1)
        else:
            lines.append(f'{prefix}{child.name}')
for d in dirs:
    p = root/d
    if p.exists():
        lines.append(d)
        walk(p, 1)
lines.append('')
lines.append('INTEGRITY: ' + ('PASS' if ok else 'FAIL'))
(root/'_verify.txt').write_text('\n'.join(lines), encoding='utf-8')
print('\n'.join(lines))
