// Extension Mind+ V2 (mode upload / Arduino C) untuk robot LFM X1.
// Format mengikuti contoh resmi DFRobot (mindplus-ext2-builder, examples/example-upload-module):
// index.js = definisi blok, func.js = kode C++ yang dihasilkan tiap blok, public/ = config + library C++.
// 1 blok = 1 fungsi library LineFollower (firmware/lib/LineFollower), jadi PID tetap jalan native di ESP32.
import ArgumentType from '../utils/argument-type';
import BlockType from '../utils/block-type';
import DataType from '../utils/data-type';
import blockIconURI from './icon/blockIcon.svg';
import menuIconURI from './icon/menuIcon.svg';
import Func from './func';
import { setLocaleData, formatMessage, setLocale } from '../utils/translation';
import LocaleData from './locales';
setLocaleData(LocaleData);

const ID = 'LFMX1';

// Teks blok: default bahasa Indonesia (dipakai kalau bahasa Mind+ tidak punya terjemahan di locales/).
const t = (key, text) => formatMessage({ id: `gui.blocklyText.${ID}.${key}`, default: text });
const num = (value) => ({ type: ArgumentType.NUMBER, defaultValue: value });
const menu = (name, value) => ({ type: ArgumentType.STRING, menu: name, defaultValue: value });
const INT = [...DataType.NUMBER];  // cara resmi menulis keluaran angka (dokumentasi Mind+ V2)

class ExtensionLFMX1 {
    constructor(runtime, extensionId) {
        this.runtime = runtime;
        this.funcs = new Func(runtime, extensionId);
    }

    setLocale(locale) {
        setLocale(locale);
    }

    getCodePrimitives() {
        return this.funcs;
    }

    getInfo() {
        return {
            name: formatMessage({ id: `gui.extensionName.${ID}`, default: 'Robot LFM X1' }),
            blockIconURI: blockIconURI,
            menuIconURI: menuIconURI,
            color1: '#0E9AA7',
            color2: '#0B7A84',
            color3: '#095F66',
            blocks: [
                // ---- persiapan & sensor
                { opcode: 'init', blockType: BlockType.COMMAND, text: t('init', 'inisialisasi robot LFM X1') },
                {
                    opcode: 'calibrate', blockType: BlockType.COMMAND,
                    text: t('calibrate', 'kalibrasi sensor [MODE] selama [MS] ms'),
                    arguments: { MODE: menu('calModeMenu', 'false'), MS: num(3000) }
                },
                { opcode: 'loadCalibration', blockType: BlockType.COMMAND, text: t('loadCalibration', 'muat kalibrasi tersimpan') },
                { opcode: 'isCalibrated', blockType: BlockType.BOOLEAN, text: t('isCalibrated', 'sensor sudah dikalibrasi?'), outputTypes: [DataType.BOOL] },
                {
                    opcode: 'lineColor', blockType: BlockType.COMMAND, text: t('lineColor', 'warna garis [COLOR]'),
                    arguments: { COLOR: menu('colorMenu', 'true') }
                },
                '---',
                { opcode: 'position', blockType: BlockType.REPORTER, text: t('position', 'posisi garis'), outputTypes: INT },
                { opcode: 'lineDetected', blockType: BlockType.BOOLEAN, text: t('lineDetected', 'garis terdeteksi?'), outputTypes: [DataType.BOOL] },
                { opcode: 'junction', blockType: BlockType.BOOLEAN, text: t('junction', 'ada persimpangan?'), outputTypes: [DataType.BOOL] },
                {
                    opcode: 'branch', blockType: BlockType.BOOLEAN, text: t('branch', 'ada cabang [SIDE]?'),
                    arguments: { SIDE: menu('sideMenu', 'left') }, outputTypes: [DataType.BOOL]
                },
                {
                    opcode: 'sensorValue', blockType: BlockType.REPORTER, text: t('sensorValue', 'nilai sensor S[N]'),
                    arguments: { N: menu('sensorMenu', '6') }, outputTypes: INT
                },
                '---',
                // ---- gerak
                {
                    opcode: 'follow', blockType: BlockType.COMMAND,
                    text: t('follow', 'ikuti garis kecepatan [SPEED] Kp [KP] Kd [KD]'),
                    arguments: { SPEED: num(120), KP: num(0.07), KD: num(3.5) }
                },
                {
                    opcode: 'motor', blockType: BlockType.COMMAND, text: t('motor', 'motor kiri [L] kanan [R]'),
                    arguments: { L: num(100), R: num(100) }
                },
                { opcode: 'stop', blockType: BlockType.COMMAND, text: t('stop', 'berhenti') },
                {
                    opcode: 'forward', blockType: BlockType.COMMAND, text: t('forward', 'maju [MM] mm kecepatan [SPEED]'),
                    arguments: { MM: num(200), SPEED: num(90) }
                },
                {
                    opcode: 'turnDegrees', blockType: BlockType.COMMAND,
                    text: t('turnDegrees', 'putar [DEG] derajat (+ kiri) kecepatan [SPEED]'),
                    arguments: { DEG: num(90), SPEED: num(90) }
                },
                {
                    opcode: 'turnToLine', blockType: BlockType.COMMAND,
                    text: t('turnToLine', 'belok [SIDE] sampai ketemu garis kecepatan [SPEED]'),
                    arguments: { SIDE: menu('sideMenu', 'left'), SPEED: num(90) }
                },
                '---',
                // ---- path planning per indeks
                {
                    opcode: 'setPid', blockType: BlockType.COMMAND, text: t('setPid', 'atur PID rute Kp [KP] Kd [KD]'),
                    arguments: { KP: num(0.07), KD: num(3.5) }
                },
                {
                    opcode: 'runIndex', blockType: BlockType.COMMAND,
                    text: t('runIndex', 'indeks [N] jika [TRIG] lakukan [ACT] lalu ikuti garis [COLOR] kecepatan [SPEED] sejauh [MM] mm'),
                    arguments: {
                        N: num(1), TRIG: menu('trigMenu', 'TRIG_JUNCTION'), ACT: menu('actMenu', 'ACT_LEFT'),
                        COLOR: menu('colorMenu', 'true'), SPEED: num(120), MM: num(80)
                    }
                },
                { opcode: 'routeReset', blockType: BlockType.COMMAND, text: t('routeReset', 'mulai rute baru') },
                {
                    opcode: 'blockNode', blockType: BlockType.COMMAND, text: t('blockNode', 'tandai simpul x [X] y [Y] terhalang'),
                    arguments: { X: num(1), Y: num(1) }
                },
                { opcode: 'clearBlocked', blockType: BlockType.COMMAND, text: t('clearBlocked', 'hapus semua simpul terhalang') },
                {
                    opcode: 'shortestRoute', blockType: BlockType.COMMAND,
                    text: t('shortestRoute', 'jalankan rute terpendek grid [COLS] x [ROWS] dari x [SX] y [SY] menghadap [HEAD] ke x [GX] y [GY] kecepatan [SPEED]'),
                    arguments: {
                        COLS: num(4), ROWS: num(4), SX: num(0), SY: num(0), HEAD: menu('headingMenu', '1'),
                        GX: num(3), GY: num(3), SPEED: num(120)
                    }
                },
                '---',
                // ---- lain-lain
                { opcode: 'battery', blockType: BlockType.REPORTER, text: t('battery', 'tegangan baterai (V)'), outputTypes: [DataType.FLOAT] },
                { opcode: 'batteryLow', blockType: BlockType.BOOLEAN, text: t('batteryLow', 'baterai lemah?'), outputTypes: [DataType.BOOL] },
                {
                    opcode: 'beep', blockType: BlockType.COMMAND, text: t('beep', 'bunyi [MS] ms'),
                    arguments: { MS: num(100) }
                },
                {
                    opcode: 'button', blockType: BlockType.BOOLEAN, text: t('button', 'tombol [BTN] ditekan?'),
                    arguments: { BTN: menu('buttonMenu', 'BTN_OK') }, outputTypes: [DataType.BOOL]
                },
                {
                    opcode: 'waitButton', blockType: BlockType.COMMAND, text: t('waitButton', 'tunggu tombol [BTN] ditekan'),
                    arguments: { BTN: menu('buttonMenu', 'BTN_OK') }
                },
                { opcode: 'distance', blockType: BlockType.REPORTER, text: t('distance', 'jarak tempuh (mm)'), outputTypes: [DataType.FLOAT] },
                { opcode: 'resetDistance', blockType: BlockType.COMMAND, text: t('resetDistance', 'reset jarak tempuh') }
            ],
            menus: {
                calModeMenu: {
                    acceptReporters: false,
                    items: [
                        { text: t('calHand', 'geser dengan tangan'), value: 'false' },
                        { text: t('calSpin', 'robot berayun sendiri'), value: 'true' }
                    ]
                },
                colorMenu: {
                    acceptReporters: false,
                    items: [
                        { text: t('black', 'hitam'), value: 'true' },
                        { text: t('white', 'putih'), value: 'false' }
                    ]
                },
                sideMenu: {
                    acceptReporters: false,
                    items: [
                        { text: t('left', 'kiri'), value: 'left' },
                        { text: t('right', 'kanan'), value: 'right' }
                    ]
                },
                sensorMenu: {
                    acceptReporters: true,
                    items: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
                },
                trigMenu: {
                    acceptReporters: false,
                    items: [
                        { text: t('trigJunction', 'ada persimpangan'), value: 'TRIG_JUNCTION' },
                        { text: t('trigLeft', 'ada cabang kiri'), value: 'TRIG_LEFT' },
                        { text: t('trigRight', 'ada cabang kanan'), value: 'TRIG_RIGHT' },
                        { text: t('trigBoth', 'ada cabang kiri dan kanan'), value: 'TRIG_BOTH' },
                        { text: t('trigEnd', 'garis habis'), value: 'TRIG_END' },
                        { text: t('trigDirect', 'langsung'), value: 'TRIG_DIRECT' }
                    ]
                },
                actMenu: {
                    acceptReporters: false,
                    items: [
                        { text: t('actForward', 'lurus'), value: 'ACT_FORWARD' },
                        { text: t('actLeft', 'belok kiri'), value: 'ACT_LEFT' },
                        { text: t('actRight', 'belok kanan'), value: 'ACT_RIGHT' },
                        { text: t('actUturn', 'putar balik'), value: 'ACT_UTURN' },
                        { text: t('actStop', 'berhenti'), value: 'ACT_STOP' }
                    ]
                },
                headingMenu: {
                    acceptReporters: false,
                    items: [
                        { text: t('east', 'timur (x+)'), value: '0' },
                        { text: t('north', 'utara (y+)'), value: '1' },
                        { text: t('west', 'barat (x-)'), value: '2' },
                        { text: t('south', 'selatan (y-)'), value: '3' }
                    ]
                },
                buttonMenu: {
                    acceptReporters: false,
                    items: [
                        { text: t('btnBack', 'KEMBALI'), value: 'BTN_BACK' },
                        { text: t('btnUp', 'ATAS'), value: 'BTN_UP' },
                        { text: t('btnOk', 'OK'), value: 'BTN_OK' },
                        { text: t('btnDown', 'BAWAH'), value: 'BTN_DOWN' },
                        { text: t('btnNext', 'LANJUT'), value: 'BTN_NEXT' }
                    ]
                }
            }
        };
    }
}

export default ExtensionLFMX1;
