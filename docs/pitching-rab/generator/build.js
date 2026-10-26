// Deck pitching RAB Line Follower Micro (P01-5), gaya template Canva kelompok.
// Latar diambil dari PDF template (teks, foto stok, titik, kartu dihapus); semua isi = objek PowerPoint asli.
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require("/root/.claude/skills/synced/c4223730-1661-4c29-8e8c-80c31e264ba0_dc5c5629-cdad-4011-b4ec-4ad2655fbd8e/pptx/scripts/apply_theme.js");

const IMG = (f) => path.join(__dirname, "img", f);
const OUT = process.argv[2] || path.join(__dirname, "LFM_Pitching_RAB_P01-5.pptx");

const THEME = {
  name: "LFM Navy",
  headFontFace: "Arial",
  bodyFontFace: "Arial",
  colors: {
    dk1: "0D1D33", lt1: "FFFFFF", dk2: "14273C", lt2: "BFD3E6",
    accent1: "4A6F92", // kartu (steel template, sedikit digelapkan supaya teks putih terbaca)
    accent2: "9CC7EE", // sorotan angka
    accent3: "6386A6", // steel template
    accent4: "1F5981", // biru garis-garis template
    accent5: "1A3152", // ubin navy
    accent6: "E57373", // batas anggaran
    hlink: "9CC7EE", folHlink: "BFD3E6",
  },
};
const HEX = THEME.colors;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13,333 × 7,5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Line Follower Micro: Pitching RAB";
pres.author = "Kelompok P01-5";
pres.subject = "PjBL Semester 5 DTEO FV ITS";
const C = pres.SchemeColor;
const WHITE = C.background1, SOFT = C.background2, HI = C.accent2;

// ---------------------------------------------------------------- layout
const header = (y = 0.66) => [
  { text: { text: "Presentation by Group P01-5", options: { x: 1.23, y, w: 5.5, h: 0.4, fontSize: 16, color: WHITE, margin: 0, valign: "middle" } } },
  { text: { text: "2026", options: { x: 10.36, y, w: 2.0, h: 0.4, fontSize: 16, color: WHITE, margin: 0, align: "right", valign: "middle" } } },
];
// fungsi (bukan objek bersama): pptxgenjs mengubah objek opsi di tempat saat dipakai
const leftTitle = () => [
  { rect: { x: 1.23, y: 1.24, w: 0.045, h: 0.72, fill: { color: WHITE } } },
  { placeholder: { options: { name: "title", type: "title", x: 1.48, y: 1.17, w: 10.7, h: 0.86, fontSize: 40, bold: true, color: WHITE, align: "left", valign: "middle", margin: 0 }, text: "" } },
];

pres.defineSlideMaster({
  title: "JUDUL",
  background: { path: IMG("p1.png") },
  objects: [
    { text: { text: "2026", options: { x: 10.8, y: 0.66, w: 1.5, h: 0.5, fontSize: 25, color: WHITE, margin: 0, align: "right", valign: "middle" } } },
    { placeholder: { options: { name: "title", type: "title", x: 1.55, y: 1.98, w: 6.9, h: 2.95, fontSize: 74, bold: true, color: WHITE, align: "left", valign: "top", margin: 0, lineSpacingMultiple: 0.8 }, text: "" } },
    { placeholder: { options: { name: "subtitle", type: "body", x: 1.55, y: 4.92, w: 6.4, h: 0.42, fontSize: 20, color: WHITE, align: "left", valign: "middle", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "keterangan", type: "body", x: 1.55, y: 5.36, w: 6.0, h: 0.38, fontSize: 16, color: SOFT, align: "left", valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({ title: "ISI_A", background: { path: IMG("p9.png") }, objects: [...header(), ...leftTitle()] });
pres.defineSlideMaster({ title: "ISI_B", background: { path: IMG("p8.png") }, objects: [...header(0.6), ...leftTitle()] });
pres.defineSlideMaster({
  title: "ISI_TENGAH",
  background: { path: IMG("p3.png") },
  objects: [
    ...header(),
    { placeholder: { options: { name: "title", type: "title", x: 1.6, y: 1.12, w: 10.13, h: 0.86, fontSize: 40, bold: true, color: WHITE, align: "center", valign: "middle", margin: 0 }, text: "" } },
    { rect: { x: 3.3, y: 2.07, w: 6.73, h: 0.035, fill: { color: WHITE } } },
  ],
});
pres.defineSlideMaster({
  title: "PENUTUP",
  background: { path: IMG("p10.png") },
  objects: [
    ...header(0.72),
    { rect: { x: 1.42, y: 2.12, w: 0.045, h: 3.05, fill: { color: WHITE } } },
    { placeholder: { options: { name: "title", type: "title", x: 1.68, y: 2.0, w: 6.2, h: 3.3, fontSize: 88, bold: true, color: WHITE, align: "left", valign: "middle", margin: 0, lineSpacingMultiple: 0.85 }, text: "" } },
  ],
});

// ---------------------------------------------------------------- bantuan
function dots(s, x, y, name = "Titik hias") {
  for (let i = 0; i < 3; i++) {
    s.addShape(pres.ShapeType.ellipse, { x: x + i * 0.27, y, w: 0.17, h: 0.17, fill: { color: WHITE }, objectName: `${name} ${i + 1}` });
  }
}
function framed(s, file, x, y, w, h, name, alt, pad = 0.06) {
  s.addShape(pres.ShapeType.rect, { x: x - pad, y: y - pad, w: w + 2 * pad, h: h + 2 * pad, fill: { color: WHITE }, objectName: `${name} bingkai` });
  s.addImage({ path: IMG(file), x, y, w, h, altText: alt, objectName: name });
}
function bullets(s, items, opt) {
  s.addText(
    items.map((t, i) => ({ text: t, options: { bullet: { indent: 16 }, breakLine: i < items.length - 1, paraSpaceAfter: opt.gap ?? 8 } })),
    { fontSize: 14, color: WHITE, valign: "top", margin: 0, isTextBox: true, ...opt }
  );
}
function card(s, x, y, w, h, head, body, name, fill = C.accent1) {
  s.addShape(pres.ShapeType.rect, { x, y, w, h, fill: { color: fill }, objectName: `${name} latar` });
  s.addText(
    [
      { text: head, options: { bold: true, fontSize: 16, breakLine: true, paraSpaceAfter: 6 } },
      { text: body, options: { fontSize: 14 } },
    ],
    { x: x + 0.18, y: y + 0.16, w: w - 0.36, h: h - 0.32, color: WHITE, valign: "top", margin: 0, isTextBox: true, objectName: `${name} teks` }
  );
}

// ---------------------------------------------------------------- 1. Judul
pres.addSection({ title: "Pembuka" });
let s = pres.addSlide({ masterName: "JUDUL", sectionTitle: "Pembuka" });
s.addText("LINE\nFOLLOWER\nMICRO", { placeholder: "title" });
s.addText("Presentation by Group P01-5", { placeholder: "subtitle" });
s.addText("Pitching RAB · 27 Oktober 2026", { placeholder: "keterangan" });
s.addNotes("Pembuka. Kami kelompok P01-5 dengan proyek Line Follower Micro: robot edukasi pengikut garis yang bisa merencanakan rute, hasil reverse engineering kit Ichiduino Pro. Hari ini kami mengajukan RAB untuk pembelian komponen dan fabrikasi PCB.");

// ---------------------------------------------------------------- 2. Tim
s = pres.addSlide({ masterName: "ISI_A", sectionTitle: "Pembuka" });
s.addText("TIM KAMI", { placeholder: "title" });
const tim = [
  ["MS", "Mararevi Subagyo", "2040241036", "Project Manager, [isi peran]"],
  ["FR", "Fernandy Raditya Wardhana", "2040241007", "[isi peran]"],
  ["AI", "Achmad Iqbal Adiputra", "2040241121", "[isi peran]"],
  ["AD", "Adhityanoval Dewa Mahendra", "2040241085", "[isi peran]"],
];
tim.forEach(([ini, nama, nrp, peran], i) => {
  const x = 1.23 + i * 2.77, y = 2.35, w = 2.55, h = 2.75;
  s.addShape(pres.ShapeType.rect, { x, y, w, h, fill: { color: C.accent5 }, objectName: `Kartu anggota ${i + 1}` });
  s.addShape(pres.ShapeType.ellipse, { x: x + 0.2, y: y + 0.22, w: 0.78, h: 0.78, fill: { color: C.accent1 }, objectName: `Inisial ${i + 1} lingkaran` });
  s.addText(ini, { x: x + 0.2, y: y + 0.22, w: 0.78, h: 0.78, fontSize: 18, bold: true, color: WHITE, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `Inisial ${i + 1}` });
  s.addText(
    [
      { text: nama, options: { bold: true, fontSize: 16, breakLine: true, paraSpaceAfter: 4 } },
      { text: `NRP ${nrp}`, options: { fontSize: 14, color: SOFT, breakLine: true, paraSpaceAfter: 8 } },
      { text: peran, options: { fontSize: 14 } },
    ],
    { x: x + 0.2, y: y + 1.15, w: w - 0.4, h: 1.45, color: WHITE, valign: "top", margin: 0, isTextBox: true, objectName: `Anggota ${i + 1}` }
  );
});
s.addText([{ text: "Dosen pembimbing: ", options: { bold: true } }, { text: "Fira Aulia, S.Tr.T, M.Tr.T" }], { x: 1.23, y: 5.42, w: 8, h: 0.4, fontSize: 16, color: WHITE, margin: 0, isTextBox: true, objectName: "Pembimbing" });
dots(s, 10.9, 5.55);
s.addNotes("Perkenalan tim dan pembagian peran. Isi peran tiap anggota sebelum presentasi.");

// ---------------------------------------------------------------- 3. Latar belakang
pres.addSection({ title: "Masalah dan solusi" });
s = pres.addSlide({ masterName: "ISI_TENGAH", sectionTitle: "Masalah dan solusi" });
s.addText("LATAR BELAKANG", { placeholder: "title" });
s.addText("± Rp2 juta", { x: 1.6, y: 2.55, w: 4.9, h: 1.0, fontSize: 60, bold: true, color: HI, margin: 0, isTextBox: true, objectName: "Harga kit" });
s.addText("harga satu kit line tracer edukasi Ichiduino Pro; unit kontrolnya saja Rp825.000", { x: 1.6, y: 3.6, w: 4.6, h: 0.75, fontSize: 16, color: WHITE, margin: 0, valign: "top", isTextBox: true, objectName: "Harga kit keterangan" });
dots(s, 1.6, 4.75);
bullets(s, [
  "Kit edukasi di pasaran dirancang untuk kompetisi (motor 1200 RPM, LiPo 2S 400 mAh): mahal dan kurang pas sebagai media belajar anak sekolah.",
  "Arahan dosen: reverse engineering produk contoh, lalu buat ulang dengan budget maksimal Rp1.000.000.",
  "Syarat minimum robot: mengikuti garis secara otomatis dan punya kemampuan path planning.",
], { x: 6.85, y: 2.55, w: 4.85, h: 3.3, gap: 12, objectName: "Masalah poin" });
s.addNotes("Masalah: kit edukasi mahal, sekitar dua juta rupiah, dan dirancang untuk lomba. Dari dosen kami mendapat batas: reverse engineering, anggaran maksimal satu juta rupiah (naik dari 900 ribu), minimal bisa ikut garis dan path planning.");

// ---------------------------------------------------------------- 4. Solusi
s = pres.addSlide({ masterName: "ISI_B", sectionTitle: "Masalah dan solusi" });
s.addText("SOLUSI KAMI", { placeholder: "title" });
s.addText(
  "Line Follower Micro: hasil reverse engineering Ichiduino Pro yang dirancang ulang dari nol, dari elektronik, PCB, sampai firmware dan block coding.",
  { x: 1.23, y: 2.4, w: 4.7, h: 1.25, fontSize: 16, color: WHITE, margin: 0, valign: "top", isTextBox: true, objectName: "Solusi ringkas" }
);
s.addText([{ text: "Rp887.000", options: { bold: true, fontSize: 36, color: HI, breakLine: true } }, { text: "± 44% harga kit pembanding", options: { fontSize: 14, color: WHITE } }],
  { x: 1.23, y: 3.85, w: 4.6, h: 1.0, margin: 0, valign: "top", isTextBox: true, objectName: "Biaya solusi" });
s.addText("Target uji lapangan: lomba IARC XII Smart Robotics, 9–10 Januari 2027 (arena grid, garis hitam 2 cm).",
  { x: 1.23, y: 5.05, w: 4.6, h: 0.8, fontSize: 14, color: SOFT, margin: 0, valign: "top", isTextBox: true, objectName: "Target lomba" });
[
  ["Ikuti garis", "Kendali PID dengan 12 sensor QRE1113GR"],
  ["Path planning", "Rute = urutan indeks (pola sensor → aksi); di grid dibuat otomatis dari rute terpendek"],
  ["Block coding web", "Diprogram lewat Blockly di browser, tanpa instalasi"],
  ["Aman", "BMS baterai, motor mati < 3,2 V/sel, berhenti ≤ 500 ms saat garis hilang"],
].forEach(([h, b], i) => card(s, 6.35 + (i % 2) * 2.83, 2.35 + Math.floor(i / 2) * 1.83, 2.68, 1.68, h, b, `Fitur ${i + 1}`));
s.addNotes("Solusi kami empat fitur utama: ikut garis dengan PID, path planning dengan peta by index seperti Ichiduino (rute ditulis sebagai urutan langkah: pola sensor lalu aksi), block coding berbasis web, dan fitur keamanan. Biayanya sekitar 44 persen harga kit pembanding.");

// ---------------------------------------------------------------- 5. Reverse engineering
s = pres.addSlide({ masterName: "ISI_A", sectionTitle: "Masalah dan solusi" });
s.addText("REVERSE ENGINEERING", { placeholder: "title" });
const th = (t) => ({ text: t, options: { bold: true, fill: { color: C.accent1 }, color: WHITE } });
const re = [
  ["Harga", "± Rp1.999.999", "Rp887.000", "56% lebih murah"],
  ["Otak", "ATmega2560", "ESP32 240 MHz dual-core, WiFi/BT", "diganti"],
  ["Sensor garis", "12 sensor optik", "12 QRE1113GR + multiplexer", "dipertahankan"],
  ["Layar", "OLED 0,96\"", "OLED 0,96\" (bar bacaan sensor)", "dipertahankan"],
  ["Baterai", "LiPo 2S 400 mAh", "2× 18650 + BMS + charger USB-C", "diganti, lebih awet"],
  ["Motor", "DC 16 mm 12 V 1200 RPM", "N20 6 V 500 RPM + encoder", "diganti"],
  ["Pemrograman", "mBlock, Arduino IDE", "Blockly web, Arduino", "diganti"],
  ["Path planning", "per indeks, berbasis waktu", "indeks + encoder + rute otomatis", "dikembangkan"],
  ["Servo, kipas", "2 port servo, 1 port kipas", "tidak ada", "ditiadakan"],
];
s.addTable(
  [[th("Aspek"), th("Ichiduino Pro (pembanding)"), th("Line Follower Micro"), th("Keputusan")],
   ...re.map((r, i) => r.map((c, j) => ({ text: c, options: { bold: j === 0 || (i === 0 && j === 2), color: j === 3 ? HI : WHITE, fill: { color: i % 2 ? C.accent5 : C.text1 } } })))],
  { x: 1.23, y: 2.25, w: 10.87, colW: [1.85, 3.2, 3.77, 2.05], rowH: 0.36, fontSize: 14, color: WHITE, valign: "middle", margin: [0.03, 0.1, 0.03, 0.1], border: { type: "solid", pt: 0.75, color: C.accent3 }, objectName: "Tabel reverse engineering" }
);
s.addNotes("Tabel reverse engineering: fungsi utama kit dipertahankan (12 sensor, OLED), komponen yang mahal atau kurang cocok untuk edukasi diganti. Path planning di kit disusun per indeks lewat mBlock dengan aksi berbasis waktu (ms). Kami pakai cara yang sama, tapi aksi belok dan maju diukur encoder sehingga tidak tergantung tegangan baterai, dan di lintasan grid urutan indeksnya bisa dibuat otomatis dari rute terpendek. Fitur lomba ditiadakan. Kinerja nyata kit akan diukur di lintasan yang sama.");

// ---------------------------------------------------------------- 6. Sasaran terukur
s = pres.addSlide({ masterName: "ISI_TENGAH", sectionTitle: "Masalah dan solusi" });
s.addText("SASARAN TERUKUR", { placeholder: "title" });
[
  ["≤ 2 mm", "akurasi posisi garis"],
  ["≥ 0,5 m/s", "kecepatan rata-rata"],
  ["≤ 5%", "simpangan baku waktu tempuh, 10 putaran"],
  ["≥ 95%", "deteksi persimpangan, ≥ 40 persimpangan"],
  ["10 / 10", "rute pada peta indeks dijalankan benar"],
  ["≤ 30 mm", "error berhenti di titik tujuan"],
  ["≤ 500 ms", "berhenti saat garis hilang"],
  ["< 3,2 V", "per sel: motor mati, baterai lemah"],
].forEach(([v, l], i) => {
  const x = 1.6 + (i % 4) * 2.56, y = 2.45 + Math.floor(i / 4) * 1.62, w = 2.38, h = 1.45;
  s.addShape(pres.ShapeType.rect, { x, y, w, h, fill: { color: C.accent5 }, objectName: `Sasaran ${i + 1} latar` });
  s.addText([{ text: v, options: { bold: true, fontSize: 28, color: HI, breakLine: true, paraSpaceAfter: 4 } }, { text: l, options: { fontSize: 14, color: WHITE } }],
    { x: x + 0.17, y: y + 0.14, w: w - 0.34, h: h - 0.24, valign: "top", margin: 0, isTextBox: true, objectName: `Sasaran ${i + 1}` });
});
s.addText("Tiap sasaran punya cara uji dan alat ukur bersatuan (3–10 ulangan); sasaran ke-9: total biaya ≤ Rp1.000.000.",
  { x: 1.6, y: 5.75, w: 10.1, h: 0.35, fontSize: 14, color: SOFT, margin: 0, isTextBox: true, objectName: "Catatan sasaran" });
s.addNotes("Sasaran terukur dari charter. Semua bernilai, bersatuan, dan punya cara uji. Sasaran biaya dibahas di bagian RAB.");

// ---------------------------------------------------------------- 7. Arsitektur
pres.addSection({ title: "Rancangan" });
s = pres.addSlide({ masterName: "ISI_A", sectionTitle: "Rancangan" });
s.addText("ARSITEKTUR SISTEM", { placeholder: "title" });
framed(s, "diagram-blok.png", 1.29, 2.3, 6.5, 6.5 / (3700 / 2210), "Diagram blok", "Diagram blok perangkat keras: input sensor, mux, tombol, baterai; ESP32; output driver, motor, encoder, OLED, buzzer; sistem daya");
bullets(s, [
  "12 QRE1113GR → multiplexer CD74HC4067 → ESP32: cukup 5 pin (1 ADC + 4 pemilih kanal).",
  "ESP32 → driver TB6612FNG → 2 motor N20; encoder kembali ke ESP32.",
  "Daya: 2× 18650 → BMS 2S → saklar → buck 5 V; motor langsung dari baterai.",
  "OLED, 2 tombol, buzzer, sensor tegangan baterai. Program dari Blockly lewat Wi-Fi atau USB-C.",
], { x: 8.2, y: 2.3, w: 3.95, h: 3.75, gap: 12, objectName: "Arsitektur poin" });
s.addNotes("Arsitektur: input sensor lewat multiplexer ke ESP32, ESP32 mengatur driver motor, encoder memberi umpan balik, OLED dan tombol untuk menu. Sistem daya dari dua baterai 18650 dengan BMS.");

// ---------------------------------------------------------------- 8. Kendali dan path planning
s = pres.addSlide({ masterName: "ISI_B", sectionTitle: "Rancangan" });
s.addText("KENDALI & PATH PLANNING", { placeholder: "title" });
framed(s, "diagram-kendali.png", 1.29, 2.3, 7.3, 7.3 / (1840 / 620), "Diagram kendali", "Diagram blok kendali loop tertutup: setpoint, PID, driver, motor, robot, sensor, pengolahan sinyal, loop dalam encoder");
bullets(s, [
  "Loop luar: posisi garis dari 12 sensor → PID → kecepatan motor kiri/kanan.",
  "Loop dalam: encoder mengukur jarak tempuh dan sudut belok 90° (tanpa IMU).",
  "Peta by index (gaya Ichiduino): rute = urutan indeks; tiap indeks: pola sensor → aksi (maju/kiri/kanan) → ikuti garis. Di grid, urutannya bisa dibuat otomatis dari rute terpendek (BFS).",
], { x: 1.23, y: 4.9, w: 7.4, h: 1.25, gap: 3, objectName: "Kendali poin" });
// grid 4 × 4 dengan rute contoh
const gx = 9.25, gy = 2.4, gs = 0.72;
const node = (i, j) => [gx + i * gs, gy + j * gs];
for (let k = 0; k < 4; k++) {
  s.addShape(pres.ShapeType.line, { x: gx, y: gy + k * gs, w: 3 * gs, h: 0, line: { color: C.accent3, width: 2 }, objectName: `Grid baris ${k + 1}` });
  s.addShape(pres.ShapeType.line, { x: gx + k * gs, y: gy, w: 0, h: 3 * gs, line: { color: C.accent3, width: 2 }, objectName: `Grid kolom ${k + 1}` });
}
const route = [[0, 3], [1, 3], [1, 2], [2, 2], [2, 1], [3, 1], [3, 0]];
for (let k = 0; k < route.length - 1; k++) {
  const [x1, y1] = node(...route[k]), [x2, y2] = node(...route[k + 1]);
  s.addShape(pres.ShapeType.line, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1), line: { color: C.accent2, width: 5 }, objectName: `Rute ${k + 1}` });
}
for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) {
  const [x, y] = node(i, j);
  s.addShape(pres.ShapeType.ellipse, { x: x - 0.08, y: y - 0.08, w: 0.16, h: 0.16, fill: { color: WHITE }, objectName: `Simpul ${i}-${j}` });
}
route.slice(1, -1).forEach(([i, j], k) => {
  // indeks = nomor langkah di rute (bukan nomor simpul)
  const [x, y] = node(i, j);
  s.addText(String(k + 1), { x: x + 0.09, y: y - 0.33, w: 0.3, h: 0.26, fontSize: 12, bold: true, color: C.accent2, margin: 0, isTextBox: true, objectName: `Indeks ${k + 1}` });
});
for (const [lbl, [i, j]] of [["S", [0, 3]], ["T", [3, 0]]]) {
  const [x, y] = node(i, j);
  s.addShape(pres.ShapeType.ellipse, { x: x - 0.2, y: y - 0.2, w: 0.4, h: 0.4, fill: { color: C.accent2 }, objectName: `Titik ${lbl} lingkaran` });
  s.addText(lbl, { x: x - 0.2, y: y - 0.2, w: 0.4, h: 0.4, fontSize: 14, bold: true, color: C.text1, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `Titik ${lbl}` });
}
s.addText("Indeks = urutan langkah rute S → T\n1 kiri · 2 kanan · 3 kiri\n4 kanan · 5 kiri · 6 berhenti", { x: 8.95, y: 4.88, w: 3.1, h: 0.72, fontSize: 13, color: SOFT, margin: 0, valign: "top", isTextBox: true, objectName: "Grid keterangan" });
s.addNotes("Kendali loop tertutup: posisi garis diumpankan ke PID; encoder dipakai untuk jarak dan belok 90 derajat. Path planning memakai peta yang ditentukan di awal (pre-defined map by index, usulan Bu Fira), seperti blok path planning Ichiduino di mBlock: rute ditulis sebagai urutan indeks. Tiap indeks berisi pola sensor pemicu (misalnya persimpangan kiri), aksi (maju, belok kiri, belok kanan), lalu ikuti garis lagi sampai indeks berikutnya. Contoh di grid: dari S, indeks 1 belok kiri, 2 kanan, 3 kiri, 4 kanan, 5 kiri, 6 berhenti di T. Bedanya dengan kit: aksi kami diukur encoder, bukan waktu, dan di lintasan grid urutan indeks bisa dibuat otomatis dari rute terpendek (BFS). Robot tidak perlu menjelajah dulu.");

// ---------------------------------------------------------------- 9. PCB
s = pres.addSlide({ masterName: "ISI_A", sectionTitle: "Rancangan" });
s.addText("RANCANGAN PCB", { placeholder: "title" });
s.addImage({ path: IMG("sensor-bawah.png"), x: 1.23, y: 2.15, w: 2.25 * (2087 / 1158), h: 2.25, altText: "Render PCB sensor rev B tampak bawah: 12 sensor QRE1113GR di pita melengkung bentuk jangkar", objectName: "PCB sensor" });
s.addImage({ path: IMG("utama-iso.png"), x: 8.3, y: 2.15, w: 2.25 * (1717 / 1652), h: 2.25, altText: "Render PCB utama bentuk mobil F1, tampak miring", objectName: "PCB utama" });
const pcbInfo = (x, w, head, body, chip, name) => {
  s.addText([{ text: head, options: { bold: true, fontSize: 16, breakLine: true, paraSpaceAfter: 4 } }, { text: body, options: { fontSize: 14 } }],
    { x, y: 5.02, w, h: 0.72, color: WHITE, margin: 0, valign: "top", isTextBox: true, objectName: `${name} keterangan` });
  s.addShape(pres.ShapeType.roundRect, { x, y: 4.5, w: chip.length * 0.095 + 0.4, h: 0.4, rectRadius: 0.2, fill: { color: C.accent1 }, objectName: `${name} status latar` });
  s.addText(chip, { x, y: 4.5, w: chip.length * 0.095 + 0.4, h: 0.4, fontSize: 14, bold: true, color: WHITE, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `${name} status` });
};
pcbInfo(1.23, 5.4, "PCB sensor rev B · 95 × 51 mm", "12 QRE1113GR jarak 8 mm, mux SOIC-24, JST XH 8 pin", "DRC 0 error · siap cetak", "PCB sensor");
pcbInfo(7.0, 5.1, "PCB utama · 100 × 127 mm, bentuk mobil F1", "ESP32, TB6612, buck 5 V, OLED, tombol, buzzer", "Routing selesai · sisa 11 error DRC", "PCB utama");
s.addNotes("Dua PCB custom, dibuat di KiCad 10. PCB sensor sudah DRC 0 error dan siap cetak; jarak sensor 8 mm dipilih untuk garis lomba 2 cm. PCB utama sudah dirouting, semua jalur tersambung, tinggal 11 error DRC dari dua footprint (transistor Q1 dan saklar SW1) sebelum dicetak. Aturan cetak mengikuti tempat cetak: jalur minimal 0,3 mm.");

// ---------------------------------------------------------------- 10. Mekanik
s = pres.addSlide({ masterName: "ISI_B", sectionTitle: "Rancangan" });
s.addText("RANCANGAN MEKANIK", { placeholder: "title" });
framed(s, "v16-iso.png", 1.29, 2.3, 5.4, 5.4 / 1.4, "Model 3D iso", "Model 3D robot v16 tampak miring di atas garis hitam");
framed(s, "v16-samping.png", 7.25, 2.3, 2.15, 2.15 / 1.4, "Model 3D samping", "Model 3D robot tampak samping");
framed(s, "v16-belakang.png", 9.6, 2.3, 2.15, 2.15 / 1.4, "Model 3D belakang", "Model 3D robot tampak belakang miring");
bullets(s, [
  "± 116 × 165 × 62 mm, bentuk rendah seperti kit pembanding.",
  "PCB jadi sasis; semua komponen dan baterai di atas, muka sensor ± 3 mm dari lantai.",
  "Body 3D print (cover, bumper, dudukan, sayap) belum di RAB: menunggu info printer lab.",
], { x: 7.19, y: 3.95, w: 4.6, h: 1.8, gap: 4, objectName: "Mekanik poin" });
s.addNotes("Model 3D versi 16 dari CAD: ukuran sekitar 11,6 x 16,5 x 6,2 cm, setara kit pembanding. PCB menjadi sasis. Body 3D print belum dianggarkan karena menunggu info printer lab.");

// ---------------------------------------------------------------- 10b. Simulasi
s = pres.addSlide({ masterName: "ISI_B", sectionTitle: "Rancangan" });
s.addText("SIMULASI", { placeholder: "title" });
framed(s, "sim-2d.png", 1.29, 2.3, 3.85, 3.85, "Gambar simulasi", "Lintasan robot hasil simulasi di arena grid 4 kali 4: dari S belok di indeks 1 sampai 5 lalu berhenti di T");
bullets(s, [
  "Model robot ukuran asli dibangun otomatis di CoppeliaSim dari skrip Python: roda Ø34 jarak 91 mm, N20 500 RPM, 12 sensor di posisi PCB rev B.",
  "Arena grid 30 cm, garis hitam 2 cm. Logika sama dengan firmware: PID + path planning per indeks, belok diukur encoder.",
], { x: 5.55, y: 2.3, w: 6.5, h: 1.7, gap: 8, objectName: "Simulasi poin" });
s.addText("Hasil uji logika kendali (simulasi 2D, gambar kiri):", { x: 5.55, y: 4.05, w: 6.5, h: 0.32, fontSize: 14, bold: true, color: SOFT, margin: 0, isTextBox: true, objectName: "Hasil simulasi judul" });
[
  ["8,2 s · 9 mm", "rute contoh S → T, berhenti 9 mm dari T"],
  ["25 / 25 lulus", "kecepatan 0,3–0,7 m/s, 5 variasi derau sensor"],
  ["Rute otomatis", "rute terpendek, juga saat simpul terhalang kubus"],
].forEach(([h, b], i) => card(s, 5.55 + i * 2.2, 4.45, 2.05, 1.55, h, b, `Hasil simulasi ${i + 1}`));
s.addNotes("Simulasi sesuai arahan dosen. Model robot ukuran asli dibangun otomatis di CoppeliaSim dari skrip Python: roda 34 mm berjarak 91 mm, motor N20 500 RPM, dan 12 sensor di posisi PCB sensor rev B. Arena grid 30 cm dengan garis hitam 2 cm seperti lomba. Logikanya sama dengan yang akan masuk firmware: PID ikut garis dan path planning per indeks, belok diukur encoder lalu dikunci ke garis oleh sensor. Sebelum dijalankan di CoppeliaSim, logika yang sama diuji dulu di simulasi 2D (gambar kiri): rute contoh dari S ke T selesai 8,2 detik dan berhenti 9 mm dari titik tujuan; kecepatan 0,3 sampai 0,7 meter per detik lulus semua; rute terpendek otomatis juga lulus saat ada simpul terhalang.");

// ---------------------------------------------------------------- 11. RAB ringkas
pres.addSection({ title: "Anggaran" });
s = pres.addSlide({ masterName: "ISI_A", sectionTitle: "Anggaran" });
s.addText("RENCANA ANGGARAN BIAYA", { placeholder: "title" });
s.addText([{ text: "Rp887.000", options: { bold: true, fontSize: 48, color: HI, breakLine: true } }, { text: "Elektrikal Rp832.000 + Mekanik Rp55.000", options: { fontSize: 16, color: WHITE } }],
  { x: 1.23, y: 2.35, w: 4.6, h: 1.35, margin: 0, valign: "top", isTextBox: true, objectName: "Total RAB" });
bullets(s, [
  "Porsi terbesar: fabrikasi 2 PCB (Rp200.000) dan 12 sensor QRE1113GR (Rp180.000).",
  "Di luar RAB: lintasan uji, breadboard dan timah (pinjam lab), software gratis (Blockly, Arduino, KiCad).",
  "Kit Ichiduino Pro hanya pembanding, tidak dianggarkan ulang.",
], { x: 1.23, y: 3.95, w: 4.6, h: 2.15, gap: 8, objectName: "RAB poin" });
s.addChart(pres.ChartType.bar, [{ name: "Biaya (ribu rupiah)", labels: ["PCB & konektor", "Sensor garis", "Penggerak", "Daya & baterai", "Otak & antarmuka", "Mekanik lain"], values: [240, 203, 170, 136, 118, 20] }], {
  x: 6.2, y: 2.2, w: 5.95, h: 3.95, barDir: "bar", barGapWidthPct: 45, chartColors: ["9CC7EE"],
  catAxisOrientation: "maxMin", catAxisLabelColor: "FFFFFF", catAxisLabelFontSize: 14, catAxisLabelFontFace: "+mn-lt", catAxisLineShow: false,
  valAxisHidden: true, valAxisMaxVal: 300, valGridLine: { style: "none" }, catGridLine: { style: "none" },
  showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: '"Rp"0" rb"', dataLabelColor: "FFFFFF", dataLabelFontSize: 14, dataLabelFontFace: "+mn-lt",
  showLegend: false, showTitle: true, title: "Biaya per kelompok (ribu rupiah)", titleColor: "BFD3E6", titleFontSize: 14, titleFontFace: "+mn-lt",
  objectName: "Grafik RAB per kelompok", altText: "Grafik batang biaya per kelompok: PCB dan konektor 240 ribu, sensor garis 203 ribu, penggerak 170 ribu, daya dan baterai 136 ribu, otak dan antarmuka 118 ribu, mekanik lain 20 ribu",
});
s.addNotes("Total RAB 887 ribu rupiah. Terbesar untuk fabrikasi dua PCB dan 12 sensor. Rincian lengkap tiap item ada di lampiran.");

// ---------------------------------------------------------------- 12. Alasan komponen
s = pres.addSlide({ masterName: "ISI_B", sectionTitle: "Anggaran" });
s.addText("ALASAN KOMPONEN UTAMA", { placeholder: "title" });
[
  ["ESP32 DevKit · Rp76.000", "240 MHz dual-core + WiFi untuk Blockly; ESP32-S3 > Rp130.000"],
  ["12× QRE1113GR · Rp180.000", "LED IR + fototransistor satu kemasan bersekat: papan tipis, sensor ± 3 mm dari lantai"],
  ["2× N20 + encoder · Rp110.000", "v maks 0,89 m/s (sasaran ≥ 0,5 m/s); encoder untuk belok 90° dan jarak tempuh"],
  ["TB6612FNG · Rp25.000", "Tegangan jatuh jauh lebih kecil dari L298N, sehingga tidak panas"],
  ["2× 18650 + BMS + charger · Rp115.000", "± 3 jam pemakaian, dilindungi BMS, diisi lewat USB-C"],
  ["Fabrikasi 2 PCB · Rp200.000", "Papan custom menggantikan kabel breadboard: rapi dan awet dipakai siswa"],
].forEach(([h, b], i) => card(s, 1.23 + (i % 3) * 3.6, 2.3 + Math.floor(i / 3) * 1.92, 3.42, 1.76, h, b, `Komponen ${i + 1}`));
s.addNotes("Alasan pemilihan enam komponen dengan biaya terbesar. Semua harga dari daftar harga toko (tautan di charter).");

// ---------------------------------------------------------------- 13. Riwayat RAB
s = pres.addSlide({ masterName: "ISI_A", sectionTitle: "Anggaran" });
s.addText("RIWAYAT RAB & EFISIENSI", { placeholder: "title" });
const revLbl = ["Rev 3.2", "Rev 3.3", "Rev 3.4", "13/10", "15/10", "20/10 (1)", "20/10 (2)", "21/10", "22/10", "26/10"];
const revVal = [845, 858, 833, 896, 879.5, 859.5, 867, 887, 902, 887];
s.addChart(
  [
    { type: pres.ChartType.line, data: [{ name: "Total RAB", labels: revLbl, values: revVal }], options: { chartColors: ["9CC7EE"], lineSize: 3, lineDataSymbol: "circle", lineDataSymbolSize: 9, showValue: true, dataLabelPosition: "t", dataLabelFormatCode: "General", dataLabelColor: "FFFFFF", dataLabelFontSize: 12, dataLabelFontFace: "+mn-lt" } },
    { type: pres.ChartType.line, data: [{ name: "Batas Rp1.000 rb", labels: revLbl, values: revVal.map(() => 1000) }], options: { chartColors: ["E57373"], lineSize: 2, lineDash: "dash", lineDataSymbol: "none", showValue: false } },
  ],
  {
    x: 1.15, y: 2.2, w: 7.0, h: 3.95,
    valAxisMinVal: 800, valAxisMaxVal: 1050, valAxisMajorUnit: 50, valAxisLabelColor: "BFD3E6", valAxisLabelFontSize: 12, valAxisLabelFontFace: "+mn-lt", valAxisLineShow: false,
    valGridLine: { color: "2A4466", size: 0.75 }, catGridLine: { style: "none" },
    catAxisLabelColor: "BFD3E6", catAxisLabelFontSize: 12, catAxisLabelFontFace: "+mn-lt",
    showLegend: true, legendPos: "b", legendColor: "FFFFFF", legendFontSize: 12, legendFontFace: "+mn-lt",
    showTitle: true, title: "Total RAB per revisi (ribu rupiah)", titleColor: "BFD3E6", titleFontSize: 14, titleFontFace: "+mn-lt",
    objectName: "Grafik riwayat RAB", altText: "Grafik garis total RAB per revisi antara 833 dan 902 ribu rupiah, terakhir 887 ribu, dengan garis batas 1 juta rupiah",
  }
);
s.addText([{ text: "Sisa Rp113.000", options: { bold: true, fontSize: 36, color: HI, breakLine: true } }, { text: "(11,3%) di bawah batas Rp1.000.000", options: { fontSize: 16, color: WHITE } }],
  { x: 8.45, y: 2.3, w: 3.7, h: 1.25, margin: 0, valign: "top", isTextBox: true, objectName: "Selisih anggaran" });
bullets(s, [
  "Kenaikan terbesar: QRE1113GR lokal Rp15.000/pcs (+Rp105.000).",
  "Dihemat: MCP23017 + LED dihapus, skid nilon, alat pinjam lab (−Rp85.000), mux harga toko (−Rp15.000).",
  "Sisa untuk kenaikan harga atau body 3D print (belum di RAB).",
], { x: 8.45, y: 3.5, w: 3.7, h: 2.3, gap: 8, objectName: "Selisih poin" });
s.addNotes("RAB sudah sepuluh kali direvisi. Kenaikan terbesar dari harga QRE1113GR lokal yang ternyata tiga kali perkiraan, sedangkan penghematan datang dari penghapusan MCP23017 dan LED indikator, skid nilon, serta alat yang dipinjam dari lab; revisi terakhir 26/10: IC multiplexer dapat harga toko 20 ribu, turun 15 ribu dari perkiraan. Dengan batas anggaran Rp1.000.000, RAB 887 ribu masih menyisakan 113 ribu (11,3 persen) untuk kenaikan harga atau item yang belum masuk RAB seperti body 3D print.");

// ---------------------------------------------------------------- 14. Jadwal & risiko
pres.addSection({ title: "Penutup" });
s = pres.addSlide({ masterName: "ISI_TENGAH", sectionTitle: "Penutup" });
s.addText("JADWAL & RISIKO", { placeholder: "title" });
const gates = [
  ["G1", "Penetapan", "minggu 1–2", "lulus 02/10"],
  ["G2", "Rancangan + RAB", "minggu 3–6", "hari ini"],
  ["FMEA", "Analisis bahaya", "minggu 7–8", ""],
  ["G3", "Prototipe jalan 3×, PCB dipesan", "≤ minggu 10", ""],
  ["G4", "Pembuktian + uji siswa", "minggu 11–14", ""],
  ["G5", "Serah terima", "minggu 15–16", ""],
];
const tx0 = 2.1, tdx = 1.83, ty = 2.75;
s.addShape(pres.ShapeType.line, { x: tx0, y: ty, w: tdx * 5, h: 0, line: { color: C.accent3, width: 3 }, objectName: "Garis waktu" });
gates.forEach(([g, n, wk, st], i) => {
  const cx = tx0 + i * tdx;
  const done = i === 0, now = i === 1;
  s.addShape(pres.ShapeType.ellipse, { x: cx - 0.27, y: ty - 0.27, w: 0.54, h: 0.54, fill: { color: done || now ? C.accent2 : C.accent1 }, objectName: `Gerbang ${g} lingkaran` });
  s.addText(g, { x: cx - 0.45, y: ty - 0.27, w: 0.9, h: 0.54, fontSize: g.length > 2 ? 11 : 14, bold: true, color: done || now ? C.text1 : WHITE, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: `Gerbang ${g}` });
  s.addText([{ text: n, options: { bold: true, breakLine: true } }, { text: wk, options: { color: SOFT, breakLine: !!st } }, ...(st ? [{ text: st, options: { color: HI, bold: true } }] : [])],
    { x: cx - 0.85, y: ty + 0.38, w: 1.7, h: 1.15, fontSize: 13, color: WHITE, align: "center", valign: "top", margin: 0, isTextBox: true, objectName: `Gerbang ${g} keterangan` });
});
[
  ["PCB salah desain / terlambat", "Prototipe breadboard dulu, PCB dipesan paling lambat minggu 10"],
  ["Biaya melebihi batas", "RAB dipantau tiap pembelian, harga disertai tautan toko"],
  ["QRE tanpa cadangan", "Tiap sensor diuji di breadboard sebelum disolder"],
].forEach(([h, b], i) => card(s, 1.6 + i * 3.45, 4.45, 3.25, 1.45, h, b, `Risiko ${i + 1}`));
s.addNotes("Jadwal mengikuti gerbang PjBL. G1 sudah lulus 2 Oktober, hari ini bagian dari G2. Sesudah dana cair: beli komponen, uji di breadboard, lalu pesan PCB paling lambat minggu 10 untuk G3. Tiga risiko yang berkaitan dengan dana dan penanganannya.");

// ---------------------------------------------------------------- 15. Penutup
s = pres.addSlide({ masterName: "PENUTUP", sectionTitle: "Penutup" });
s.addText("TERIMA\nKASIH", { placeholder: "title" });
s.addText([{ text: "Mohon persetujuan dana", options: { fontSize: 18, breakLine: true } }, { text: "Rp887.000", options: { fontSize: 48, bold: true, color: HI } }],
  { x: 8.0, y: 1.95, w: 4.2, h: 1.35, color: WHITE, margin: 0, valign: "top", isTextBox: true, objectName: "Permohonan dana" });
s.addText("untuk pembelian komponen dan fabrikasi 2 PCB. Sesudah dana cair:", { x: 8.0, y: 3.38, w: 4.1, h: 0.6, fontSize: 14, color: WHITE, margin: 0, valign: "top", isTextBox: true, objectName: "Permohonan keterangan" });
s.addText(
  ["Beli komponen", "Uji rangkaian di breadboard", "Pesan PCB sensor + PCB utama", "Firmware dan prototipe untuk G3"].map((t, i, a) => ({ text: t, options: { bullet: { type: "number" }, breakLine: i < a.length - 1, paraSpaceAfter: 6 } })),
  { x: 8.0, y: 4.05, w: 4.1, h: 1.7, fontSize: 16, color: WHITE, margin: 0, valign: "top", isTextBox: true, objectName: "Langkah sesudah dana" }
);
dots(s, 5.0, 5.55);
s.addNotes("Penutup: kami mohon persetujuan dana 887 ribu rupiah. Rencana sesudah dana cair ada di sisi kanan. Terima kasih, kami siap menjawab pertanyaan.");

// ---------------------------------------------------------------- Lampiran
pres.addSection({ title: "Lampiran" });
const rabTable = (rows, footer) => {
  const head = ["Item", "Harga", "Qty", "Total"].map(th);
  const body = rows.map((r, i) => r.map((c, j) => ({ text: c, options: { align: j === 0 ? "left" : "right", fill: { color: i % 2 ? C.accent5 : C.text1 } } })));
  const foot = footer ? [footer.map((c, j) => ({ text: c, options: { bold: true, align: j === 0 ? "left" : "right", fill: { color: C.accent1 } } }))] : [];
  return [[...head], ...body, ...foot];
};
const tableOpt = (name) => ({ x: 1.23, y: 2.25, w: 10.87, colW: [6.07, 1.7, 1.3, 1.8], rowH: 0.34, fontSize: 14, color: WHITE, valign: "middle", margin: [0.03, 0.1, 0.03, 0.1], border: { type: "solid", pt: 0.75, color: C.accent3 }, objectName: name });
const elek = [
  ["ESP32 DevKit WiFi Bluetooth CH340 Type-C", "Rp76.000", "1", "Rp76.000"],
  ["OLED 0,96\" 128×64 I2C", "Rp33.000", "1", "Rp33.000"],
  ["Sensor reflektif QRE1113GR SMD (toko lokal)", "Rp15.000", "12", "Rp180.000"],
  ["IC multiplexer CD74HC4067M SOP-24 (WKH Electronic)", "Rp20.000", "1", "Rp20.000"],
  ["Modul driver motor TB6612FNG", "Rp25.000", "1", "Rp25.000"],
  ["Motor N20 6V 500 RPM + encoder", "Rp55.000", "2", "Rp110.000"],
  ["Push button", "Rp1.000", "4", "Rp4.000"],
  ["Resistor SMD 0805 (220 Ω, 10 kΩ)", "Rp100", "30", "Rp3.000"],
  ["Resistor 10 kΩ", "Rp200", "10", "Rp2.000"],
  ["Buzzer", "Rp3.000", "1", "Rp3.000"],
  ["Baterai Li-ion 18650", "Rp40.000", "2", "Rp80.000"],
  ["Holder baterai 2× 18650 (seri)", "Rp8.000", "1", "Rp8.000"],
  ["Modul BMS 2S", "Rp10.000", "1", "Rp10.000"],
  ["Modul charger 2S USB-C", "Rp25.000", "1", "Rp25.000"],
  ["Buck converter 5 V (MP1584)", "Rp10.000", "1", "Rp10.000"],
  ["Saklar on/off", "Rp3.000", "1", "Rp3.000"],
  ["Konektor JST PH2.0 6 pin + header (encoder motor)", "Rp5.000", "2 set", "Rp10.000"],
  ["Komponen pendukung (header, socket, kapasitor, dioda)", "Rp25.000", "1 paket", "Rp25.000"],
  ["Konektor JST XH 8 pin + kabel (perkiraan)", "Rp5.000", "1 set", "Rp5.000"],
  ["Fabrikasi PCB (2 papan) + ongkir", "Rp200.000", "1 paket", "Rp200.000"],
];
s = pres.addSlide({ masterName: "ISI_A", sectionTitle: "Lampiran" });
s.addText("LAMPIRAN A · RAB ELEKTRIKAL (1/2)", { placeholder: "title" });
s.addTable(rabTable(elek.slice(0, 10), ["Subtotal halaman ini", "", "", "Rp456.000"]), tableOpt("Tabel RAB elektrikal 1"));
s.addNotes("Rincian RAB elektrikal bagian pertama.");
s = pres.addSlide({ masterName: "ISI_A", sectionTitle: "Lampiran" });
s.addText("LAMPIRAN B · RAB ELEKTRIKAL (2/2)", { placeholder: "title" });
s.addTable(rabTable(elek.slice(10), ["Total elektrikal", "", "", "Rp832.000"]), tableOpt("Tabel RAB elektrikal 2"));
s.addNotes("Rincian RAB elektrikal bagian kedua; total elektrikal 832 ribu.");
s = pres.addSlide({ masterName: "ISI_A", sectionTitle: "Lampiran" });
s.addText("LAMPIRAN C · RAB MEKANIK & REKAP", { placeholder: "title" });
s.addTable(rabTable([
  ["Roda N20 Ø34 mm", "Rp25.000", "1 pasang", "Rp25.000"],
  ["Bracket motor N20", "Rp10.000", "1 pasang", "Rp10.000"],
  ["Skid nilon (baut, spacer, mur nilon)", "Rp5.000", "1 paket", "Rp5.000"],
  ["Baut, mur, spacer", "Rp15.000", "1 paket", "Rp15.000"],
], ["Total mekanik", "", "", "Rp55.000"]), { ...tableOpt("Tabel RAB mekanik"), h: undefined });
[["Elektrikal", "Rp832.000"], ["Mekanik", "Rp55.000"], ["Total RAB", "Rp887.000"]].forEach(([k, v], i) => {
  const x = 1.23 + i * 3.7;
  s.addShape(pres.ShapeType.rect, { x, y: 4.55, w: 3.45, h: 1.3, fill: { color: i === 2 ? C.accent1 : C.accent5 }, objectName: `Rekap ${k} latar` });
  s.addText([{ text: k, options: { fontSize: 14, breakLine: true, paraSpaceAfter: 2 } }, { text: v, options: { fontSize: 30, bold: true, color: i === 2 ? WHITE : HI } }],
    { x: x + 0.2, y: 4.67, w: 3.05, h: 1.08, color: WHITE, margin: 0, valign: "top", isTextBox: true, objectName: `Rekap ${k}` });
});
s.addNotes("RAB mekanik dan rekap total 887 ribu. Lintasan uji, breadboard, dan timah di luar RAB.");

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("ditulis:", OUT);
})();
