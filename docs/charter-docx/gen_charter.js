// Membuat Project Charter (.docx) dengan format sama seperti versi Google Docs 09/10/2026.
// Isi diperbarui sesuai keputusan 20/10/2026 (12 sensor LED merah + fototransistor SMD, tanpa MCP23017, RAB Rp859.500).
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, Header,
  AlignmentType, WidthType, ShadingType, BorderStyle, VerticalAlign, LevelFormat,
  HorizontalPositionRelativeFrom, VerticalPositionRelativeFrom, TextWrappingType,
} = require("docx");

const OUT = process.argv[2];
const KOP = path.join(__dirname, "kop.png");
const TANGGAL = "20 Oktober 2026";

// Ukuran halaman A4 dan margin meniru PDF asli (teks mulai x ≈ 65 pt, tabel lebar ≈ 503 pt)
const PAGE_W = 11906;
const MARGIN_L = 1300;
const TABLE_W = 10060;
const MARGIN_R = PAGE_W - MARGIN_L - TABLE_W;

const FONT = "Times New Roman";
const FILL = "D6EDF1";
const LINE = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const BORDERS = { top: LINE, bottom: LINE, left: LINE, right: LINE };
const PAD = { top: 40, bottom: 40, left: 110, right: 110 };

// ---------- pembantu ----------
function run(text, o = {}) {
  return new TextRun({ text, font: o.font || FONT, size: (o.size || 12) * 2, bold: o.bold,
    italics: o.italics, smallCaps: o.smallCaps });
}
function para(children, o = {}) {
  if (typeof children === "string") children = [run(children, o)];
  return new Paragraph({
    children,
    alignment: o.align || AlignmentType.LEFT,
    spacing: { before: o.before || 0, after: o.after || 0, line: o.line || 264 },
    numbering: o.numbering,
    tabStops: o.tabStops,
    keepNext: o.keepNext,
    keepLines: o.keepLines,
  });
}
function cell(paras, width, o = {}) {
  if (!Array.isArray(paras)) paras = [paras];
  return new TableCell({
    children: paras,
    width: { size: width, type: WidthType.DXA },
    columnSpan: o.span,
    shading: o.fill ? { fill: o.fill, type: ShadingType.CLEAR, color: "auto" } : undefined,
    borders: BORDERS,
    margins: PAD,
    verticalAlign: o.vAlign || VerticalAlign.TOP,
  });
}
function row(cells, o = {}) {
  return new TableRow({ children: cells, cantSplit: o.cantSplit !== false, tableHeader: o.header });
}
function table(widths, rows) {
  return new Table({ width: { size: TABLE_W, type: WidthType.DXA }, columnWidths: widths, rows });
}
const sum = (a) => a.reduce((x, y) => x + y, 0);
// Kepala bagian: baris biru muda dengan judul tebal, membentang semua kolom
function sectionHead(title, widths) {
  return row([cell(para(title, { bold: true, keepNext: true }), sum(widths),
    { span: widths.length, fill: FILL })]);
}
function italicNote(text, widths) {
  return row([cell(para(text, { italics: true, keepNext: true }), sum(widths), { span: widths.length })]);
}
const gap = () => para("", { line: 240 });
const rp = (n) => "Rp" + n.toLocaleString("id-ID");

// ---------- 1. Project Identity ----------
const W1 = [2840, TABLE_W - 2840];
const tim = [
  ["Mararevi Subagyo", "2040241036", true],
  ["Fernandy Raditya Wardhana", "2040241007"],
  ["Achmad Iqbal Adiputra", "2040241121"],
  ["Adhityanoval Dewa Mahendra", "2040241085"],
];
const timParas = tim.map(([nama, nrp, pm]) => para([
  run(nama + (pm ? " (" : "")),
  ...(pm ? [run("Project Manager", { italics: true }), run(")")] : []),
  run("\t" + nrp),
], { numbering: { reference: "tim", level: 0 }, tabStops: [{ type: "left", position: 5560 }] }));

const identity = table(W1, [
  sectionHead("1.  Project Identity", W1),
  row([cell(para("Nama", { bold: true }), W1[0]), cell(para("Robot Line Tracer Micro"), W1[1])]),
  row([cell(para("Short Description", { bold: true }), W1[0]),
    cell(para("Robot line tracer edukasi untuk anak sekolah, hasil reverse engineering kit Ichiduino " +
      "Pro, yang mampu mengikuti garis secara otomatis dan merencanakan rute terpendek (path planning) " +
      "pada lintasan bercabang. Berbasis ESP32, dapat diprogram dengan block coding berbasis web, dan " +
      "dibangun dengan anggaran maksimal Rp 900.000.", { align: AlignmentType.JUSTIFIED }), W1[1])]),
  row([cell(para("Supervisor", { bold: true }), W1[0]), cell(para("Fira Aulia, S.Tr.T, M.Tr.T"), W1[1])]),
  row([cell(para("Team Member", { bold: true }), W1[0]), cell(timParas, W1[1])]),
]);

// ---------- 2. Business reasons ----------
const W2 = [TABLE_W];
const J = { align: AlignmentType.JUSTIFIED };
const business = table(W2, [
  sectionHead("2. Business reasons for project", W2),
  row([cell([
    para("Robot line tracer edukasi di pasaran lokal, seperti Ichiduino Pro, dijual sekitar Rp 2.000.000 " +
      "per kit lengkap dengan unit kontrol (Ultimate 5 Max) seharga Rp 825.000, dan ditujukan untuk " +
      "kompetisi. Harga dan fiturnya (kecepatan tinggi, baterai LiPo 2S) kurang sesuai sebagai media " +
      "belajar anak.", J),
    para("", J),
    para("Proyek ini melakukan reverse engineering terhadap Ichiduino Pro: fungsi dan arsitekturnya " +
      "dianalisis, lalu dirancang ulang dari nol dengan anggaran maksimal Rp 900.000. Fitur yang " +
      "dipertahankan, diganti, atau ditiadakan dipilih berdasarkan kebutuhan edukasi dan batas anggaran. " +
      "Selain mengikuti garis, robot memiliki kemampuan path planning, yaitu memetakan lintasan bercabang " +
      "dan menentukan rute terpendek menuju titik tujuan, sehingga pengguna dapat belajar konsep algoritma " +
      "dan navigasi melalui block coding berbasis web tanpa instalasi.", J),
  ], TABLE_W)], { cantSplit: false }),
]);

// ---------- 3. Objectives ----------
const tujuan = [
  "Melakukan reverse engineering kit Ichiduino Pro dan merancang ulang robot line tracer edukasi berbasis " +
    "ESP32 dengan anggaran maksimal Rp 900.000.",
  "Membuat robot yang mampu mengikuti garis hitam di atas putih secara otomatis dengan kendali PID, dengan " +
    "akurasi pembacaan posisi garis ≤ 2 mm dan kecepatan rata-rata ≥ 0,5 m/s.",
  "Menerapkan path planning: robot mendeteksi persimpangan, menyimpan peta lintasan sebagai graf, serta " +
    "menghitung dan menjalankan rute terpendek menuju titik tujuan.",
  "Menerapkan fitur keamanan berupa berhenti ≤ 500 ms setelah garis tidak terdeteksi dan pemutusan saat " +
    "tegangan baterai < 3,2 V per sel.",
  "Mengembangkan platform block coding berbasis web (Blockly), termasuk blok navigasi menuju titik tujuan.",
  "Menguji performa, keterulangan gerak, dan path planning robot, serta melakukan uji coba.",
];
const objectives = table(W2, [
  sectionHead("3. Project Objectives/ Purposes", W2),
  row([cell(tujuan.map((t) => para(t, { numbering: { reference: "tujuan", level: 0 }, after: 40 })),
    TABLE_W)], { cantSplit: false }),
]);

// ---------- 4. Scope ----------
const lingkup = [
  "Reverse engineering kit Ichiduino Pro (analisis fungsi, arsitektur, dan spesifikasi)",
  "Robot line tracer edukasi berbasis ESP32, dirancang dari nol",
  "Elektronik: 12 sensor garis (LED merah + fototransistor SMD, PCB sensor bentuk jangkar) + multiplexer, " +
    "motor DC + encoder, driver motor, OLED, catu daya baterai 2S (2× 18650)",
  "Firmware: baca sensor, kalibrasi, kendali PID, deteksi persimpangan, fitur keamanan",
  "Path planning: pemetaan lintasan bercabang dan pencarian rute terpendek ke titik tujuan",
  "Platform block coding berbasis web (Blockly)",
  "Prototipe sampai desain PCB yang siap diproduksi",
  "Uji performa robot, uji path planning, dan uji coba",
];
const scope = table(W2, [
  sectionHead("4. Project Scope", W2),
  row([cell(lingkup.map((t) => para(t, { numbering: { reference: "bullet", level: 0 } })), TABLE_W)],
    { cantSplit: false }),
]);

// ---------- 5. Deliverables ----------
const W5 = [3060, TABLE_W - 3060];
// nama: array potongan [teks, miring?] meniru format asli
const luaran = [
  [[["Analisis Reverse Engineering", true]], "Tabel analisis fungsi, arsitektur, dan spesifikasi Ichiduino " +
    "Pro beserta keputusan fitur yang dipertahankan, diganti, atau ditiadakan"],
  [[["Prototipe", true]], "Robot Line Tracer Micro yang dapat mengikuti garis dan menjalankan path planning"],
  [[["Desain PCB", false]], "File skematik dan layout PCB yang siap diproduksi"],
  [[["Firmware", true]], "Program pembacaan sensor, kendali PID, deteksi persimpangan, path planning, dan " +
    "fitur keamanan"],
  [[["Platform ", false], ["Block Coding", true]], "Aplikasi web berbasis Blockly untuk memprogram robot " +
    "tanpa menulis kode"],
  [[["Data Pengujian", false]], "Hasil uji akurasi sensor, kecepatan, keterulangan, batas aman, dan uji coba"],
  [[["Laporan Mingguan", false]], "Laporan mingguan berisi aktivitas, perkembangan, dan kendala selama " +
    "proses PJBL"],
  [[["Laporan Akhir", false]], "Laporan menyeluruh mengenai proses, solusi, dan hasil PJBL, beserta manual " +
    "pengguna"],
];
const deliverables = table(W5, [
  sectionHead("5. Key Project Deliverables", W5),
  italicNote("List and description of what are the target to be delivered in the end of the project", W5),
  row([cell(para("Nama", { bold: true }), W5[0], { fill: FILL }),
    cell(para("Deskripsi", { bold: true }), W5[1], { fill: FILL })]),
  ...luaran.map(([nama, desk]) => row([
    cell(para(nama.map(([t, it]) => run(t, { italics: it })), { after: 60 }), W5[0]),
    cell(para(desk, { after: 60 }), W5[1]),
  ])),
]);

// ---------- 6. Criteria ----------
const kriteria = [
  ["Akurasi pembacaan posisi garis ≤ 2 mm.", " Diuji dengan meletakkan robot dalam keadaan diam (motor mati) " +
    "pada posisi geser −20 s.d. +20 mm (tiap 5 mm) dari tengah garis, lalu posisi yang terbaca sensor " +
    "dibandingkan dengan posisi sebenarnya. Alat ukur: kertas milimeter dan jangka sorong."],
  ["Kecepatan rata-rata robot ≥ 0,5 m/s.", " Dihitung dari panjang lintasan dibagi waktu tempuh, Alat ukur: " +
    "meteran dan stopwatch/video."],
  ["Keterulangan waktu tempuh dengan simpangan baku ≤ 5%.", " Robot dijalankan pada lintasan dan kondisi " +
    "baterai yang sama. Alat ukur: stopwatch/timer firmware."],
  ["Deteksi persimpangan benar ≥ 95%.", " Robot melewati persimpangan, lalu catatan deteksi robot " +
    "dibandingkan dengan jumlah persimpangan sebenarnya. Alat ukur: log serial dan video."],
  ["Path planning menghasilkan rute terpendek pada 10 dari 10 percobaan.", " Diuji pada 10 pasang titik " +
    "awal dan tujuan yang berbeda; rute yang dipilih robot dibandingkan dengan rute terpendek hasil hitung " +
    "manual. Alat ukur: log serial."],
  ["Ketepatan berhenti di titik tujuan dengan error ≤ 30 mm.", " Jarak pusat robot ke titik tujuan diukur " +
    "setelah robot berhenti, pada 10 rute di poin 5. Alat ukur: penggaris/meteran."],
  ["Robot berhenti ≤ 500 ms setelah garis tidak terdeteksi.", " Garis diputus, lalu waktu dihitung dari " +
    "rekaman video slow-motion. Alat ukur: video HP 240 fps."],
  ["Motor mati saat tegangan baterai < 3,2 V per sel.", " Baterai diganti power supply, lalu tegangan " +
    "diturunkan perlahan dan dicatat saat motor mati. Alat ukur: power supply dan multimeter."],
  ["Total biaya proyek ≤ Rp 900.000.", " Dihitung dari jumlah RAB, dan setiap harga disertai tautan toko. " +
    "Alat ukur: daftar harga."],
  ["", "Seluruh proses dan hasil pengujian terdokumentasi dalam laporan mingguan dan laporan akhir PJBL."],
];
const criteria = table(W2, [
  sectionHead("6. Project’s Criteria for Success", W2),
  row([cell(kriteria.map(([b, t]) => para([run(b, { bold: true }), run(t)],
    { numbering: { reference: "kriteria", level: 0 }, line: 240 })), TABLE_W)], { cantSplit: false }),
]);

// ---------- 7. Milestones ----------
const W7 = [880, 6560, TABLE_W - 880 - 6560];
const jadwal = [
  ["Pembagian topik dan pembekalan teori", "Minggu 1–4"],
  ["Penyusunan & pengumpulan RAB (Rencana Anggaran Biaya)", "Minggu 5–6"],
  ["Perancangan arsitektur sistem, wiring diagram, dan flowchart", "Minggu 6–7"],
  ["Perancangan skematik & layout PCB", "Minggu 7–8"],
  ["Uji Pitching RAB", "Minggu 8–9"],
  ["Pembelian komponen dan prototipe breadboard (motor, sensor, kalibrasi) serta pemesanan PCB", "Minggu 9–10"],
  ["Pengembangan platform block coding web", "Minggu 10–12"],
  ["Perakitan PCB dan integrasi sistem", "Minggu 11–12"],
  ["Pengujian dan pengambilan data, uji coba", "Minggu 12–14"],
  ["Batas akhir penyelesaian & pelaporan PJBL", "Minggu 14–15"],
  ["Evaluasi & presentasi akhir", "Minggu 16–17"],
];
const C = AlignmentType.CENTER;
const milestones = table(W7, [
  sectionHead("7. Milestone Dates", W7),
  italicNote("Summary of milestone activities and timeline", W7),
  row([cell(para("No.", { bold: true, align: C }), W7[0], { fill: FILL }),
    cell(para("Milestones/ Major Events", { bold: true, font: "Arial" }), W7[1], { fill: FILL }),
    cell(para("Due dates", { bold: true, font: "Arial" }), W7[2], { fill: FILL })]),
  ...jadwal.map(([k, w], i) => row([
    cell(para(`${i + 1}.`, { align: C, after: 80 }), W7[0]),
    cell(para(k, { after: 80 }), W7[1]),
    cell(para(w, { align: C, after: 80 }), W7[2]),
  ])),
]);

// ---------- 8. Budget ----------
const W8 = [4100, 1700, 800, 1160, TABLE_W - 4100 - 1700 - 800 - 1160];
const electrical = [
  ["ESP32 DevKit WiFi Bluetooth CH340 Type-C", 76000, 1, "pcs"],
  ["OLED 0.96\" 128×64 I2C", 33000, 1, "pcs"],
  ["LED SMD 1206 merah superbright (sensor, 12 + 3 cadangan)", 500, 15, "pcs"],
  ["Fototransistor SMD 1206 bening, impor (mis. Everlight PT15-21C; 12 + 3 cadangan)", 4000, 15, "pcs"],
  ["Modul multiplexer analog CD74HC4067 16 kanal", 15000, 1, "pcs"],
  ["Modul driver motor TB6612FNG", 25000, 1, "pcs"],
  ["Motor N20 6V ± 500 RPM + encoder", 55000, 2, "pcs"],
  ["Push button", 1000, 4, "pcs"],
  ["Resistor SMD 0805 (330 Ω dan 10 kΩ untuk PCB sensor)", 100, 30, "pcs"],
  ["Resistor 10 kΩ", 200, 10, "pcs"],
  ["Buzzer", 3000, 1, "pcs"],
  ["Baterai Li-ion 18650", 40000, 2, "pcs"],
  ["Holder baterai 2× 18650 (seri)", 8000, 1, "pcs"],
  ["Modul BMS 2S", 10000, 1, "pcs"],
  ["Modul charger 2S USB-C", 25000, 1, "pcs"],
  ["Modul buck converter 5 V (MP1584)", 10000, 1, "pcs"],
  ["Saklar on/off", 3000, 1, "pcs"],
  ["Konektor JST PH2.0 6 pin + header (motor encoder)", 5000, 2, "set"],
  ["Kabel pita 12 pin + 2 box header IDC 2×6 + 2 konektor IDC", 10000, 1, "set"],
  ["Fabrikasi PCB (papan utama + papan sensor) + ongkir", 200000, 1, "paket"],
  ["Komponen pendukung minsys (header & socket female, kapasitor, dioda 1N5819)", 25000, 1, "paket"],
];
const mechanical = [
  ["Roda N20 Ø34 mm", 25000, 1, "pasang"],
  ["Bracket motor N20", 10000, 1, "pasang"],
  ["Skid nilon M3 (pengganti ball caster; baut, spacer, mur nilon)", 5000, 1, "paket"],
  ["Baut, mur, spacer", 15000, 1, "paket"],
];
const lain = [
  ["Timah solder + flux", 25000, 1, "paket"],
  ["Breadboard + kabel jumper", 60000, 1, "paket"],
];
const S = { size: 10, align: C };
const VC = { vAlign: VerticalAlign.CENTER };
function groupRows(title, items) {
  const sub = items.reduce((a, [, h, q]) => a + h * q, 0);
  const rows = [
    row([cell(para(title, { bold: true, align: C, keepNext: true }), TABLE_W, { span: 5, fill: FILL })]),
    row(["Item", "Price per unit", "Qty", "Unit", "Total Price"].map((h, i) =>
      cell(para(h, { bold: true, align: C, keepNext: true }), W8[i], { fill: FILL })), { header: false }),
    ...items.map(([n, h, q, u]) => row([
      cell(para(n, S), W8[0], VC), cell(para(rp(h), S), W8[1], VC), cell(para(String(q), S), W8[2], VC),
      cell(para(u, S), W8[3], VC), cell(para(rp(h * q), S), W8[4], VC),
    ])),
    row([cell(para("Sub Total", S), sum(W8.slice(0, 4)), { span: 4 }),
      cell(para(rp(sub), { ...S, bold: true }), W8[4])]),
  ];
  return { rows, sub };
}
const gE = groupRows("Electrical", electrical);
const gM = groupRows("Mechanical", mechanical);
const gL = groupRows("Lain-Lain", lain);
const TOTAL = gE.sub + gM.sub + gL.sub;
if (TOTAL !== 859500) throw new Error("Total RAB tidak cocok dengan charter.md: " + TOTAL);
const budget = table(W8, [
  sectionHead("8. Budget Summary", W8),
  italicNote("Summary of what are required items to be used", W8),
  ...gE.rows, ...gM.rows, ...gL.rows,
  row([cell(para("TOTAL BUDGET", { bold: true, align: C }), sum(W8.slice(0, 4)), { span: 4 }),
    cell(para(rp(TOTAL), { bold: true, align: C }), W8[4])]),
]);

// ---------- Persetujuan ----------
const WP = [5240, TABLE_W - 5240];
const ttd = (jabatan) => [
  para(TANGGAL, { keepNext: true }), para(jabatan, { keepNext: true }),
  para("", { keepNext: true }), para("", { keepNext: true }),
  para("______________", { keepNext: true }),
];
const approval = table(WP, [
  sectionHead("Persetujuan", WP),
  row([cell(ttd("Pengawas PJBL,"), WP[0]), cell(ttd("Manajer Proyek,"), WP[1])]),
  row([cell(para("Fira Aulia, S.Tr.T, M.Tr.T"), WP[0]), cell(para("Mararevi Subagyo"), WP[1])]),
]);

// ---------- Header (kop departemen) ----------
const kopWidthPx = Math.round((PAGE_W / 1440) * 96);
const header = new Header({
  children: [new Paragraph({ children: [new ImageRun({
    type: "png", data: fs.readFileSync(KOP),
    transformation: { width: kopWidthPx, height: Math.round(kopWidthPx * 63 / 944) },
    floating: {
      horizontalPosition: { relative: HorizontalPositionRelativeFrom.PAGE, offset: 0 },
      verticalPosition: { relative: VerticalPositionRelativeFrom.PAGE, offset: 0 },
      wrap: { type: TextWrappingType.NONE }, behindDocument: true,
    },
  })] })],
});

// ---------- Dokumen ----------
const num = (ref, fmt, text, left, hanging, size) => ({ reference: ref, levels: [{
  level: 0, format: fmt, text, alignment: AlignmentType.LEFT,
  style: { paragraph: { indent: { left, hanging } }, run: size ? { size: size * 2, font: FONT } : undefined },
}] });
const doc = new Document({
  creator: "Mararevi Subagyo",
  title: "Project Charter PJBL",
  styles: { default: { document: { run: { font: FONT, size: 24 } } } },
  numbering: { config: [
    num("tim", LevelFormat.DECIMAL, "%1.", 720, 360),
    num("tujuan", LevelFormat.DECIMAL, "%1.", 360, 360, 11),
    num("kriteria", LevelFormat.DECIMAL, "%1.", 360, 360),
    { reference: "bullet", levels: [{ level: 0, format: LevelFormat.BULLET, text: "●",
      alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 720, hanging: 360 } }, run: { font: "Arial", size: 18 } } }] },
  ] },
  sections: [{
    properties: { page: {
      size: { width: PAGE_W, height: 16838 },
      margin: { top: 1440, bottom: 1300, left: MARGIN_L, right: MARGIN_R, header: 0, footer: 500 },
    } },
    headers: { default: header },
    children: [
      para([run("Project Charter", { bold: true, smallCaps: true })]),
      para("Semester Ganjil 2026-2027"),
      gap(), identity, gap(), business, gap(), objectives, gap(), scope, gap(), deliverables, gap(),
      criteria, gap(), milestones, gap(), budget, gap(), approval,
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log("OK", OUT, "total", rp(TOTAL), "| electrical", rp(gE.sub));
});
