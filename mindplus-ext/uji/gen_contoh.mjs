// Membuat contoh program blok (M7) sebagai sketsa .ino, memakai func.js yang SAMA dengan extension.
// Generator Mind+ ditiru seadanya (addInclude/addObject/addSetup + nilai parameter apa adanya), jadi file .ino
// di contoh/ = perkiraan kode yang dihasilkan Mind+ dari susunan blok yang sama. Sesudah itu tiap sketsa
// dikompilasi dengan PlatformIO (lihat README) untuk memastikan kode hasil blok memang bisa dikompilasi.
//
//   node mindplus-ext/uji/gen_contoh.mjs
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import Func from '../lfm-x1/func.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.join(here, '..', 'contoh');

function makeGenerator() {
    const g = {
        ORDER_ATOMIC: 0,
        ORDER_UNARY_POSTFIX: 1,
        includes: new Map(), objects: new Map(), setups: new Map(),
        addInclude(id, code) { this.includes.set(id, code ? `#include "${code}"` : `#include <${id}>`); },
        addObject(id, code) { this.objects.set(id, code); },
        addSetup(id, code, priority = 0) { this.setups.set(id, { code, priority }); }
    };
    return g;
}

// Satu program = daftar baris setup dan loop. Baris berupa string = blok bawaan Mind+ (jika, ulangi, tunggu);
// baris berupa [opcode, parameter] = blok LFM X1.
function render(program) {
    const gen = makeGenerator();
    const funcs = new Func(null);
    const block = (op, params = {}) => {
        const parameter = {};
        for (const [k, v] of Object.entries(params)) parameter[k] = { code: String(v) };
        const out = funcs[op](gen, {}, parameter);
        return Array.isArray(out) ? out[0] : out;
    };
    const expand = (lines) => {
        const out = [];
        for (const line of lines) {
            const text = typeof line === 'string' ? line.replace(/\{(\w+)(?::([^}]*))?\}/g, (_, op, arg) => {
                const params = {};
                if (arg) for (const kv of arg.split(',')) { const [k, v] = kv.split('='); params[k] = v; }
                return block(op, params);
            }) : block(line[0], line[1]);
            for (const l of text.split('\n')) if (l.trim()) out.push(l);
        }
        return out;
    };
    const setupLines = expand(program.setup);
    const loopLines = expand(program.loop);
    const setups = [...gen.setups.values()].sort((a, b) => b.priority - a.priority).map((s) => s.code);
    // indentasi ulang menurut kedalaman kurung kurawal (blok bawaan "jika" berisi blok lain)
    const ind = (lines) => {
        let depth = 1;
        return lines.map((l) => {
            const s = l.trim();
            if (s.startsWith('}')) depth--;
            const r = '  '.repeat(Math.max(depth, 1)) + s;
            if (s.endsWith('{')) depth++;
            return r;
        }).join('\n');
    };
    return [
        `// Contoh blok Mind+ "${program.title}" (dibuat gen_contoh.mjs dari func.js; jangan diedit manual)`,
        ...program.about.map((l) => `// ${l}`),
        ...gen.includes.values(),
        '',
        ...gen.objects.values(),
        '',
        'void setup() {',
        ind([...setups, ...setupLines]),
        '}',
        '',
        'void loop() {',
        ind(loopLines),
        '}',
        ''
    ].join('\n');
}

const programs = [
    {
        name: 'IkutiGaris',
        title: 'ikuti garis sampai persimpangan',
        about: ['Tekan OK, robot mengikuti garis hitam; berhenti + bunyi di persimpangan pertama.'],
        setup: [
            ['lineColor', { COLOR: 'true' }],
            'if (!{isCalibrated}) {',
            ['calibrate', { MODE: 'true', MS: 3000 }],
            '}',
            ['waitButton', { BTN: 'BTN_OK' }]
        ],
        loop: [
            ['follow', { SPEED: 120, KP: 0.07, KD: 3.5 }],
            'if ({junction}) {',
            ['stop'],
            ['beep', { MS: 300 }],
            ['waitButton', { BTN: 'BTN_OK' }],
            ['forward', { MM: 40, SPEED: 90 }],
            '}'
        ]
    },
    {
        name: 'RuteIndeks',
        title: 'path planning per indeks',
        about: [
            'Rute slide 8 deck pitching (= SLIDE_PLAN simulasi, lulus CoppeliaSim; = rute "Slide 8" di menu OLED).',
            'Tiap indeks = pemicu -> aksi -> ikuti garis sekian mm. Tombol apa pun saat jalan = batal.'
        ],
        setup: [
            ['setPid', { KP: 0.07, KD: 3.5 }],
            ['waitButton', { BTN: 'BTN_OK' }],
            ['routeReset'],
            ['runIndex', { N: 1, TRIG: 'TRIG_LEFT', ACT: 'ACT_LEFT', COLOR: 'true', SPEED: 120, MM: 80 }],
            ['runIndex', { N: 2, TRIG: 'TRIG_JUNCTION', ACT: 'ACT_RIGHT', COLOR: 'true', SPEED: 120, MM: 80 }],
            ['runIndex', { N: 3, TRIG: 'TRIG_JUNCTION', ACT: 'ACT_LEFT', COLOR: 'true', SPEED: 120, MM: 80 }],
            ['runIndex', { N: 4, TRIG: 'TRIG_JUNCTION', ACT: 'ACT_RIGHT', COLOR: 'true', SPEED: 120, MM: 80 }],
            ['runIndex', { N: 5, TRIG: 'TRIG_JUNCTION', ACT: 'ACT_LEFT', COLOR: 'true', SPEED: 120, MM: 80 }],
            ['runIndex', { N: 6, TRIG: 'TRIG_JUNCTION', ACT: 'ACT_STOP', COLOR: 'true', SPEED: 120, MM: 80 }],
            ['beep', { MS: 500 }]
        ],
        loop: []
    },
    {
        name: 'RuteTerpendek',
        title: 'rute terpendek di grid',
        about: [
            'Grid 4 x 4 simpul, robot di (0,0) menghadap utara, tujuan (3,3), 3 simpul terhalang.',
            'Urutan indeks dibuat otomatis (Dijkstra, belok paling sedikit), lalu dijalankan.'
        ],
        setup: [
            ['clearBlocked'],
            ['blockNode', { X: 1, Y: 0 }],
            ['blockNode', { X: 2, Y: 2 }],
            ['blockNode', { X: 1, Y: 2 }],
            ['waitButton', { BTN: 'BTN_OK' }],
            ['routeReset'],
            ['shortestRoute', { COLS: 4, ROWS: 4, SX: 0, SY: 0, HEAD: 1, GX: 3, GY: 3, SPEED: 120 }]
        ],
        loop: []
    },
    {
        name: 'CekSensor',
        title: 'cek sensor dan baterai lewat serial',
        about: ['Kirim posisi garis, cabang kiri/kanan, dan tegangan baterai ke Serial Monitor (115200) tiap 0,1 s.'],
        setup: ['Serial.begin(115200);'],
        loop: [
            'Serial.print({position});',
            'Serial.print(" kiri=");',
            'Serial.print({branch:SIDE=left});',
            'Serial.print(" kanan=");',
            'Serial.print({branch:SIDE=right});',
            'Serial.print(" S6=");',
            'Serial.print({sensorValue:N=6});',
            'Serial.print(" bat=");',
            'Serial.println({battery});',
            'if ({batteryLow}) {',
            ['beep', { MS: 50 }],
            '}',
            'delay(100);'
        ]
    }
];

fs.mkdirSync(outDir, { recursive: true });
for (const p of programs) {
    const dir = path.join(outDir, p.name);
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, `${p.name}.ino`), render(p));
    console.log(`contoh/${p.name}/${p.name}.ino`);
}
