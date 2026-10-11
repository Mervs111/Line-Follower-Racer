import json, sys
sys.path.insert(0, '.')
from gen_kicad import parse
expect = json.load(open('expected_nets.json'))
bad = 0
for proj in ('ltm-main', 'ltm-sensor'):
    net = parse(open(f'{proj}.net').read())
    nets = next(e for e in net if isinstance(e, list) and e[0] == 'nets')
    got = {}
    names = {}
    for n in nets[1:]:
        name = next(e for e in n if isinstance(e, list) and e[0] == 'name')[1].strip('"').lstrip('/')
        nodes = [e for e in n if isinstance(e, list) and e[0] == 'node']
        for nd in nodes:
            ref = next(e for e in nd if e[0] == 'ref')[1].strip('"')
            pin = next(e for e in nd if e[0] == 'pin')[1].strip('"')
            got[f'{ref}.{pin}'] = name
        names[name] = len(nodes)
    exp = expect[proj]
    for k, v in exp.items():
        if got.get(k) != v:
            print(proj, 'SALAH', k, 'harus', v, 'dapat', got.get(k)); bad += 1
    extra = [k for k in got if k not in exp and not k.startswith('#')]
    unconnected = [k for k, v in got.items() if v.startswith('unconnected') and not k.startswith('#')]
    single = [n for n, c in names.items() if c < 2 and not n.startswith('unconnected')]
    print(f'{proj}: {len(exp)} pin dicek, nets={len(names)}, pin tak terduga={extra}, unconnected={unconnected}, net 1-node={single}')
    comps = next(e for e in net if isinstance(e, list) and e[0] == 'components')
    print('  komponen:', len(comps) - 1)
print('HASIL:', 'SEMUA COCOK' if bad == 0 else f'{bad} SALAH')
