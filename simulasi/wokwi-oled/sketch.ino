/*
  Simulasi tampilan OLED + menu + 5 tombol LFM X1 (Wokwi, ESP32 DevKit C V4, OLED SSD1306 128x64 I2C).

  Tombol (urutan kiri -> kanan sama dengan board interface rev B):
    KEMBALI   ATAS   OK   BAWAH   LANJUT
  Aturan umum:
    ATAS / BAWAH : pindah pilihan; saat mengedit angka: tambah / kurang (tahan = berulang, tahan > 1,5 s = langkah x10)
    OK / LANJUT  : masuk / pilih / simpan
    KEMBALI      : kembali satu layar / batal; tahan 0,8 s = langsung ke layar utama
    Saat robot berjalan: tombol apa pun = STOP
  Di layar utama: OK = mulai, LANJUT = menu, ATAS/BAWAH = ganti rute.

  Yang masih palsu di simulasi: data 12 sensor (garis bergerak sendiri), motor, dan robot berjalan per indeks.
  Baterai dibaca dari potensiometer di GPIO39 (di robot asli: pembagi 100k/33k dari baterai).
*/
#include <Arduino.h>
#include <Wire.h>
#include <U8g2lib.h>
#include <math.h>

// 1 = simulasi Wokwi: tiap tombol ke GPIO sendiri (Wokwi tidak bisa mensimulasikan tangga resistor)
// 0 = robot asli: 5 tombol lewat tangga resistor di GPIO34 (pull-up 10k R5 di PCB utama)
#define SIMULASI 1

const uint8_t PIN_VBAT = 39;        // VBAT_SENSE (ADC1)
const uint8_t PIN_BTN_LADDER = 34;  // BTN tangga resistor (robot asli)
#if SIMULASI
const uint8_t BTN_PINS[5] = {32, 33, 25, 26, 27};  // KEMBALI, ATAS, OK, BAWAH, LANJUT (hanya di simulasi)
#endif

// OLED: SDA 21, SCL 22 (pin I2C bawaan ESP32), reset tidak dipakai
U8G2_SSD1306_128X64_NONAME_F_HW_I2C oled(U8G2_R0, U8X8_PIN_NONE);

// Semua tipe ditaruh di atas fungsi pertama: Arduino membuat prototipe fungsi otomatis di situ.
enum Button : uint8_t { BTN_NONE, BTN_BACK, BTN_UP, BTN_OK, BTN_DOWN, BTN_NEXT };
enum Screen : uint8_t {
  SCR_HOME, SCR_MENU, SCR_ROUTE, SCR_CALIB, SCR_SENSOR, SCR_PID, SCR_MOTOR, SCR_INFO,
  SCR_COUNTDOWN, SCR_RUN, SCR_DONE
};
enum CalibState : uint8_t { CAL_IDLE, CAL_RUNNING, CAL_DONE };

// ------------------------------------------------------------------ tombol
const char* const BTN_NAMES[] = {"-", "KEMBALI", "ATAS", "OK", "BAWAH", "LANJUT"};

const uint16_t DEBOUNCE_MS = 20;
const uint16_t REPEAT_DELAY_MS = 400;  // mulai berulang sesudah ditahan sekian ms
const uint16_t REPEAT_RATE_MS = 80;
const uint16_t LONG_BACK_MS = 800;     // tahan KEMBALI = ke layar utama
const uint16_t FAST_STEP_MS = 1500;    // tahan ATAS/BAWAH lebih lama = langkah x10

struct ButtonState {
  Button last = BTN_NONE;     // bacaan mentah terakhir
  Button stable = BTN_NONE;   // bacaan sesudah debounce
  uint32_t changedAt = 0;
  uint32_t pressedAt = 0;
  uint32_t nextRepeat = 0;
  bool longFired = false;
  bool repeat = false;        // event terakhir hasil ulang otomatis (bukan tekanan baru)
} btn;

// Tombol yang sedang ditekan (tanpa debounce). Hanya satu tombol terbaca dalam satu waktu.
Button rawButton() {
#if SIMULASI
  for (uint8_t i = 0; i < 5; i++) {
    if (digitalRead(BTN_PINS[i]) == LOW) return (Button)(i + 1);
  }
  return BTN_NONE;
#else
  // tegangan BTN: ATAS 0,30 V, BAWAH 0,93 V, KEMBALI 1,49 V, OK 2,12 V, LANJUT 2,63 V, lepas 3,3 V
  uint32_t mv = analogReadMilliVolts(PIN_BTN_LADDER);
  if (mv < 615) return BTN_UP;
  if (mv < 1210) return BTN_DOWN;
  if (mv < 1805) return BTN_BACK;
  if (mv < 2375) return BTN_OK;
  if (mv < 2965) return BTN_NEXT;
  return BTN_NONE;
#endif
}

// Kembalikan event tombol: sekali saat ditekan, lalu berulang untuk ATAS/BAWAH yang ditahan.
Button pollButton(uint32_t now) {
  Button raw = rawButton();
  if (raw != btn.last) {
    btn.last = raw;
    btn.changedAt = now;
  }
  if (now - btn.changedAt < DEBOUNCE_MS) return BTN_NONE;

  if (raw != btn.stable) {
    btn.stable = raw;
    if (raw == BTN_NONE) return BTN_NONE;
    btn.pressedAt = now;
    btn.nextRepeat = now + REPEAT_DELAY_MS;
    btn.longFired = false;
    btn.repeat = false;
    return raw;
  }
  if ((btn.stable == BTN_UP || btn.stable == BTN_DOWN) && (int32_t)(now - btn.nextRepeat) >= 0) {
    btn.nextRepeat = now + REPEAT_RATE_MS;
    btn.repeat = true;
    return btn.stable;
  }
  return BTN_NONE;
}

bool backHeldLong(uint32_t now) {
  if (btn.stable != BTN_BACK || btn.longFired) return false;
  if (now - btn.pressedAt < LONG_BACK_MS) return false;
  btn.longFired = true;
  return true;
}

uint32_t heldMs(uint32_t now) { return btn.stable == BTN_NONE ? 0 : now - btn.pressedAt; }

// ------------------------------------------------------------------ data robot
const uint8_t ROUTE_COUNT = 5;
const uint8_t ROUTE_STEPS[ROUTE_COUNT] = {12, 8, 15, 10, 6};  // jumlah indeks tiap rute (contoh)

struct Settings {
  uint8_t route = 0;       // 0..ROUTE_COUNT-1
  int16_t kp100 = 80;      // Kp x 100
  int16_t kd100 = 400;     // Kd x 100
  int16_t speedPct = 60;   // kecepatan dasar (%)
  bool blackLine = true;   // true = garis hitam di lantai putih
  bool calibrated = false;
} cfg;

const uint8_t SENSOR_COUNT = 12;
uint16_t sensorVal[SENSOR_COUNT];  // 0..1000, S1 = paling kiri
int16_t linePos = 0;               // -1000 (garis di kiri) .. 1000 (garis di kanan), 0 = tengah
bool lineSeen = true;

uint32_t vbatMv = 7600;
const uint32_t VBAT_LOW_MV = 6800;  // 3,4 V per sel

// Data sensor palsu: garis bergerak kiri-kanan, kadang keluar dari jangkauan sensor.
void updateFakeSensors(uint32_t now) {
  float center = 5.5f + 7.0f * sinf(now * 0.0011f);
  float sum = 0, weighted = 0, maxV = 0;
  for (uint8_t i = 0; i < SENSOR_COUNT; i++) {
    float d = i - center;
    float v = 1000.0f * expf(-d * d / 1.2f);
    sum += v;
    weighted += v * i;
    if (v > maxV) maxV = v;
    // sebelum kalibrasi rentang bacaan sempit (seperti nilai mentah), sesudahnya penuh 0..1000
    sensorVal[i] = cfg.calibrated ? (uint16_t)v : (uint16_t)(350 + v * 0.35f);
  }
  lineSeen = maxV > 500;
  if (lineSeen) {
    linePos = (int16_t)((weighted / sum - 5.5f) * 1000.0f / 5.5f);
  } else {
    linePos = linePos >= 0 ? 1000 : -1000;  // garis hilang: nilai ujung sesuai sisi terakhir
  }
}

void updateBattery() {
  uint32_t pinMv = (uint32_t)analogRead(PIN_VBAT) * 3300 / 4095;
  uint32_t mv = pinMv * 133 / 33;  // pembagi 100k/33k
  vbatMv = (vbatMv * 7 + mv) / 8;  // perataan sederhana
}

// ------------------------------------------------------------------ layar
Screen screen = SCR_HOME;
uint32_t screenSince = 0;

void goTo(Screen s, uint32_t now) {
  screen = s;
  screenSince = now;
}

const char* const MENU_ITEMS[] = {"Mulai", "Pilih rute", "Kalibrasi", "Lihat sensor",
                                  "Atur PID", "Warna garis", "Tes motor", "Info robot"};
const uint8_t MENU_COUNT = 8;
uint8_t menuSel = 0, menuTop = 0;

uint8_t routeSel = 0, routeTop = 0;

CalibState calState = CAL_IDLE;
const uint16_t CALIB_MS = 3000;

uint8_t sensorPage = 0;  // 0 = bar, 1 = angka

const char* const PID_LABELS[] = {"Kp", "Kd", "Kecepatan"};
uint8_t pidSel = 0;
bool pidEditing = false;
int16_t pidBackup = 0;

const char* const MOTOR_ITEMS[] = {"Maju", "Mundur", "Putar kiri", "Putar kanan"};
uint8_t motorSel = 0;
bool motorRunning = false;
const uint16_t MOTOR_TEST_MS = 1500;

uint32_t runStart = 0, runTimeMs = 0;
uint8_t runStep = 0;
bool runStopped = false;
const uint16_t STEP_MS = 1500;  // lama tiap indeks di simulasi

const char* toastMsg = nullptr;
uint32_t toastUntil = 0;

void toast(const char* msg, uint32_t now) {
  toastMsg = msg;
  toastUntil = now + 1000;
}

// ------------------------------------------------------------------ input per layar
int16_t* pidValue(uint8_t row) {
  if (row == 0) return &cfg.kp100;
  if (row == 1) return &cfg.kd100;
  return &cfg.speedPct;
}

void pidChange(int8_t dir, uint32_t now) {
  int16_t step = heldMs(now) > FAST_STEP_MS ? 10 : 1;
  int16_t maxV = pidSel == 0 ? 999 : (pidSel == 1 ? 2000 : 100);
  int16_t* v = pidValue(pidSel);
  *v = constrain(*v + dir * step, 0, maxV);
}

// Geser jendela daftar supaya pilihan tetap terlihat.
void keepVisible(uint8_t sel, uint8_t& top, uint8_t visible) {
  if (sel < top) top = sel;
  if (sel >= top + visible) top = sel - visible + 1;
}

void listMove(Button b, uint8_t& sel, uint8_t count) {
  if (b == BTN_UP && sel > 0) sel--;
  if (b == BTN_DOWN && sel < count - 1) sel++;
}

void startRun(uint32_t now) {
  if (!cfg.calibrated) {
    toast("Kalibrasi dulu!", now);
    return;
  }
  goTo(SCR_COUNTDOWN, now);
}

void openMenuItem(uint32_t now) {
  switch (menuSel) {
    case 0: startRun(now); break;
    case 1: routeSel = cfg.route; goTo(SCR_ROUTE, now); break;
    case 2: calState = CAL_IDLE; goTo(SCR_CALIB, now); break;
    case 3: goTo(SCR_SENSOR, now); break;
    case 4: pidEditing = false; goTo(SCR_PID, now); break;
    case 5:
      cfg.blackLine = !cfg.blackLine;
      toast(cfg.blackLine ? "Garis HITAM" : "Garis PUTIH", now);
      break;
    case 6: motorRunning = false; goTo(SCR_MOTOR, now); break;
    case 7: goTo(SCR_INFO, now); break;
  }
}

// Ulang otomatis (ATAS/BAWAH ditahan) hanya untuk pindah pilihan / ubah angka, dan hanya di layar tempat tombol
// mulai ditekan. Jadi menahan tombol untuk STOP tidak ikut melewati layar hasil.
Screen pressScreen = SCR_HOME;

bool repeatAllowed() {
  if (screen != pressScreen) return false;
  return screen == SCR_HOME || screen == SCR_MENU || screen == SCR_ROUTE || screen == SCR_PID ||
         (screen == SCR_MOTOR && !motorRunning);
}

void handleInput(Button b, uint32_t now) {
  if (btn.repeat && !repeatAllowed()) return;
  bool enter = (b == BTN_OK || b == BTN_NEXT);
  switch (screen) {
    case SCR_HOME:
      if (b == BTN_OK) startRun(now);
      if (b == BTN_NEXT) goTo(SCR_MENU, now);
      if (b == BTN_UP) cfg.route = (cfg.route + ROUTE_COUNT - 1) % ROUTE_COUNT;
      if (b == BTN_DOWN) cfg.route = (cfg.route + 1) % ROUTE_COUNT;
      break;

    case SCR_MENU:
      listMove(b, menuSel, MENU_COUNT);
      if (enter) openMenuItem(now);
      if (b == BTN_BACK) goTo(SCR_HOME, now);
      break;

    case SCR_ROUTE:
      listMove(b, routeSel, ROUTE_COUNT);
      if (enter) {
        cfg.route = routeSel;
        toast("Rute disimpan", now);
        goTo(SCR_MENU, now);
      }
      if (b == BTN_BACK) goTo(SCR_MENU, now);
      break;

    case SCR_CALIB:
      if (calState == CAL_IDLE) {
        if (enter) { calState = CAL_RUNNING; screenSince = now; }
        if (b == BTN_BACK) goTo(SCR_MENU, now);
      } else if (calState == CAL_RUNNING) {
        if (b == BTN_BACK) { calState = CAL_IDLE; toast("Dibatalkan", now); }
      } else {
        goTo(SCR_MENU, now);
      }
      break;

    case SCR_SENSOR:
      if (b == BTN_UP || b == BTN_DOWN || b == BTN_NEXT) sensorPage ^= 1;
      if (b == BTN_BACK || b == BTN_OK) goTo(SCR_MENU, now);
      break;

    case SCR_PID:
      if (!pidEditing) {
        listMove(b, pidSel, 3);
        if (enter) { pidEditing = true; pidBackup = *pidValue(pidSel); }
        if (b == BTN_BACK) goTo(SCR_MENU, now);
      } else {
        if (b == BTN_UP) pidChange(+1, now);
        if (b == BTN_DOWN) pidChange(-1, now);
        if (enter) { pidEditing = false; toast("Tersimpan", now); }
        if (b == BTN_BACK) { *pidValue(pidSel) = pidBackup; pidEditing = false; }
      }
      break;

    case SCR_MOTOR:
      if (motorRunning) { motorRunning = false; break; }
      listMove(b, motorSel, 4);
      if (enter) { motorRunning = true; screenSince = now; }
      if (b == BTN_BACK) goTo(SCR_MENU, now);
      break;

    case SCR_INFO:
      if (b == BTN_BACK || b == BTN_OK) goTo(SCR_MENU, now);
      break;

    case SCR_COUNTDOWN:
      toast("Batal", now);
      goTo(SCR_HOME, now);
      break;

    case SCR_RUN:
      runTimeMs = now - runStart;
      runStopped = true;
      goTo(SCR_DONE, now);
      break;

    case SCR_DONE:
      goTo(SCR_HOME, now);
      break;
  }
}

// Logika yang berjalan sendiri (hitung mundur, kalibrasi, robot berjalan), tanpa delay().
void updateLogic(uint32_t now) {
  uint32_t t = now - screenSince;
  if (screen == SCR_COUNTDOWN && t >= 3000) {
    runStart = now;
    runStep = 0;
    goTo(SCR_RUN, now);
  } else if (screen == SCR_RUN) {
    runStep = (now - runStart) / STEP_MS;
    if (runStep >= ROUTE_STEPS[cfg.route]) {
      runStep = ROUTE_STEPS[cfg.route];
      runTimeMs = now - runStart;
      runStopped = false;
      goTo(SCR_DONE, now);
    }
  } else if (screen == SCR_CALIB && calState == CAL_RUNNING && t >= CALIB_MS) {
    calState = CAL_DONE;
    cfg.calibrated = true;  // di robot asli: simpan min/max ke NVS
  } else if (screen == SCR_MOTOR && motorRunning && t >= MOTOR_TEST_MS) {
    motorRunning = false;
  }
}

// ------------------------------------------------------------------ gambar
void font(const uint8_t* f) {
  oled.setFont(f);
  oled.setFontPosTop();  // koordinat y = tepi atas huruf
}

void textRight(int16_t xRight, int16_t y, const char* s) { oled.drawStr(xRight - oled.getStrWidth(s), y, s); }
void textCenter(int16_t y, const char* s) { oled.drawStr((128 - oled.getStrWidth(s)) / 2, y, s); }

void fmtVolt(char* buf, size_t n, uint32_t mv) {
  uint32_t v100 = mv / 10;
  snprintf(buf, n, "%lu.%02luV", (unsigned long)(v100 / 100), (unsigned long)(v100 % 100));
}

void fmtFixed2(char* buf, size_t n, int16_t v100) { snprintf(buf, n, "%d.%02d", v100 / 100, v100 % 100); }

void drawBattery(int16_t x, int16_t y, uint32_t now) {
  bool low = vbatMv < VBAT_LOW_MV;
  if (low && ((now / 300) & 1)) return;  // baterai lemah: kedip
  oled.drawFrame(x, y, 12, 7);
  oled.drawBox(x + 12, y + 2, 2, 3);
  int32_t level = ((int32_t)vbatMv - 6400) * 10 / (8400 - 6400);
  level = constrain(level, 0, 10);
  if (level > 0) oled.drawBox(x + 1, y + 1, level, 5);
}

void drawHeader(const char* title, uint32_t now) {
  font(u8g2_font_helvB08_tr);
  oled.drawStr(0, 0, title);
  char buf[8];
  fmtVolt(buf, sizeof(buf), vbatMv);
  font(u8g2_font_5x7_tr);
  textRight(111, 1, buf);
  drawBattery(114, 1, now);
  oled.drawHLine(0, 10, 128);
}

// Satu baris daftar setinggi 13 px; baris terpilih dibalik warnanya.
void drawRow(int16_t y, const char* label, const char* value, bool selected) {
  font(u8g2_font_6x10_tr);
  if (selected) {
    oled.drawBox(0, y, 122, 13);
    oled.setDrawColor(0);
  }
  oled.drawStr(3, y + 2, label);
  if (value) textRight(119, y + 2, value);
  oled.setDrawColor(1);
}

void drawScrollbar(uint8_t top, uint8_t count, uint8_t visible) {
  if (count <= visible) return;
  const int16_t y0 = 12, h = 52;
  oled.drawVLine(125, y0, h);
  int16_t thumbH = h * visible / count;
  int16_t thumbY = y0 + (h - thumbH) * top / (count - visible);
  oled.drawBox(124, thumbY, 3, thumbH);
}

void drawFooter(const char* s) {
  oled.drawBox(0, 54, 128, 10);
  oled.setDrawColor(0);
  font(u8g2_font_5x7_tr);
  textCenter(55, s);
  oled.setDrawColor(1);
}

void drawSensorBars(int16_t yBottom, int16_t maxH) {
  for (uint8_t i = 0; i < SENSOR_COUNT; i++) {
    int16_t h = (int32_t)sensorVal[i] * maxH / 1000;
    int16_t x = 5 + i * 10;
    if (h > 0) oled.drawBox(x, yBottom - h, 8, h);
  }
  oled.drawHLine(4, yBottom + 1, 120);
}

void drawHome(uint32_t now) {
  drawHeader("LFM X1", now);
  char buf[16];
  font(u8g2_font_6x10_tr);
  snprintf(buf, sizeof(buf), "Rute %u", cfg.route + 1);
  oled.drawStr(0, 14, buf);
  snprintf(buf, sizeof(buf), "Kec %d%%", cfg.speedPct);
  textRight(127, 14, buf);
  oled.drawStr(0, 26, cfg.calibrated ? "Kal: OK" : "Kal: BELUM");
  textRight(127, 26, cfg.blackLine ? "Garis H" : "Garis P");
  drawSensorBars(50, 12);
  drawFooter("OK:MULAI ^v:RUTE >:MENU");
}

void drawMenu(uint32_t now) {
  drawHeader("MENU", now);
  keepVisible(menuSel, menuTop, 4);
  char val[8];
  for (uint8_t r = 0; r < 4 && menuTop + r < MENU_COUNT; r++) {
    uint8_t i = menuTop + r;
    const char* v = nullptr;
    if (i == 1) { snprintf(val, sizeof(val), "R%u", cfg.route + 1); v = val; }
    if (i == 2) v = cfg.calibrated ? "OK" : "!";
    if (i == 5) v = cfg.blackLine ? "Hitam" : "Putih";
    drawRow(12 + r * 13, MENU_ITEMS[i], v, i == menuSel);
  }
  drawScrollbar(menuTop, MENU_COUNT, 4);
}

void drawRoute(uint32_t now) {
  drawHeader("PILIH RUTE", now);
  keepVisible(routeSel, routeTop, 4);
  char label[12], val[12];
  for (uint8_t r = 0; r < 4 && routeTop + r < ROUTE_COUNT; r++) {
    uint8_t i = routeTop + r;
    snprintf(label, sizeof(label), "%sRute %u", i == cfg.route ? "*" : " ", i + 1);
    snprintf(val, sizeof(val), "%u idx", ROUTE_STEPS[i]);
    drawRow(12 + r * 13, label, val, i == routeSel);
  }
  drawScrollbar(routeTop, ROUTE_COUNT, 4);
}

void drawProgress(int16_t y, uint32_t elapsed, uint32_t total) {
  oled.drawFrame(10, y, 108, 9);
  int16_t w = (int32_t)min(elapsed, total) * 104 / total;
  if (w > 0) oled.drawBox(12, y + 2, w, 5);
}

void drawCalib(uint32_t now) {
  drawHeader("KALIBRASI", now);
  font(u8g2_font_6x10_tr);
  if (calState == CAL_IDLE) {
    oled.drawStr(0, 14, "Letakkan robot di");
    oled.drawStr(0, 25, "atas garis.");
    oled.drawStr(0, 38, "Robot berputar 3 s.");
    drawFooter("OK:MULAI  <:KEMBALI");
  } else if (calState == CAL_RUNNING) {
    oled.drawStr(0, 14, "Mengkalibrasi...");
    drawProgress(27, now - screenSince, CALIB_MS);
    drawSensorBars(52, 12);
  } else {
    font(u8g2_font_helvB08_tr);
    textCenter(20, "Selesai!");
    font(u8g2_font_6x10_tr);
    textCenter(34, "Data disimpan");
    drawFooter("TOMBOL APA SAJA: KEMBALI");
  }
}

void drawSensor(uint32_t now) {
  drawHeader("SENSOR", now);
  char buf[20];
  if (sensorPage == 0) {
    drawSensorBars(44, 31);
    font(u8g2_font_5x7_tr);
    for (uint8_t i = 0; i < SENSOR_COUNT; i += 11) {  // nomor sensor paling kiri dan kanan
      snprintf(buf, sizeof(buf), "S%u", i + 1);
      oled.drawStr(i == 0 ? 3 : 113, 47, buf);
    }
  } else {
    font(u8g2_font_5x7_tr);
    for (uint8_t i = 0; i < SENSOR_COUNT; i++) {  // 3 kolom x 4 baris, "12:1000" muat 35 px
      snprintf(buf, sizeof(buf), "%u:%u", i + 1, sensorVal[i]);
      oled.drawStr((i % 3) * 43, 13 + (i / 3) * 10, buf);
    }
  }
  font(u8g2_font_6x10_tr);
  if (lineSeen) {
    snprintf(buf, sizeof(buf), "Pos %d", linePos);
  } else {
    snprintf(buf, sizeof(buf), "Hilang %s", linePos < 0 ? "<" : ">");
  }
  oled.drawStr(0, 54, buf);
  textRight(127, 54, sensorPage == 0 ? "^v:angka" : "^v:bar");
}

void drawPid(uint32_t now) {
  drawHeader("ATUR PID", now);
  char val[10];
  for (uint8_t r = 0; r < 3; r++) {
    int16_t v = *pidValue(r);
    if (r < 2) fmtFixed2(val, sizeof(val), v);
    else snprintf(val, sizeof(val), "%d%%", v);
    int16_t y = 12 + r * 13;
    if (pidEditing && r == pidSel) {
      drawRow(y, PID_LABELS[r], nullptr, false);
      int16_t w = oled.getStrWidth(val) + 6;
      if ((now / 400) & 1) {  // nilai yang diedit berkedip
        oled.drawBox(122 - w, y, w, 13);
        oled.setDrawColor(0);
      } else {
        oled.drawFrame(122 - w, y, w, 13);
      }
      textRight(119, y + 2, val);
      oled.setDrawColor(1);
    } else {
      drawRow(y, PID_LABELS[r], val, !pidEditing && r == pidSel);
    }
  }
  drawFooter(pidEditing ? "^v:UBAH OK:SIMPAN <:BATAL" : "OK:UBAH  <:KEMBALI");
}

void drawMotor(uint32_t now) {
  drawHeader("TES MOTOR", now);
  if (motorRunning) {
    font(u8g2_font_6x10_tr);
    oled.drawStr(0, 14, "Motor jalan:");
    font(u8g2_font_helvB08_tr);
    oled.drawStr(0, 26, MOTOR_ITEMS[motorSel]);
    drawProgress(40, now - screenSince, MOTOR_TEST_MS);
    drawFooter("TOMBOL APA SAJA: STOP");
    return;
  }
  for (uint8_t r = 0; r < 4; r++) drawRow(12 + r * 13, MOTOR_ITEMS[r], nullptr, r == motorSel);
}

void drawInfo(uint32_t now) {
  drawHeader("INFO ROBOT", now);
  char buf[32], v[8];
  font(u8g2_font_5x7_tr);
  oled.drawStr(0, 14, "LFM X1 - firmware sim");
  fmtVolt(v, sizeof(v), vbatMv);
  snprintf(buf, sizeof(buf), "Baterai : %s", v);
  oled.drawStr(0, 23, buf);
  oled.drawStr(0, 32, "Sensor  : 12x QRE1113");
  snprintf(buf, sizeof(buf), "Rute    : %u (%u indeks)", cfg.route + 1, ROUTE_STEPS[cfg.route]);
  oled.drawStr(0, 41, buf);
  drawFooter("<:KEMBALI");
}

void drawCountdown(uint32_t now) {
  uint32_t t = now - screenSince;
  char buf[4];
  snprintf(buf, sizeof(buf), "%lu", (unsigned long)(3 - min(t / 1000, (uint32_t)2)));
  font(u8g2_font_6x10_tr);
  textCenter(2, "Siap...");
  font(u8g2_font_logisoso32_tn);
  textCenter(15, buf);
  drawFooter("TOMBOL APA SAJA: BATAL");
}

void drawTime(int16_t y, uint32_t ms) {
  char buf[12];
  snprintf(buf, sizeof(buf), "%lu.%lu", (unsigned long)(ms / 1000), (unsigned long)(ms % 1000 / 100));
  font(u8g2_font_logisoso24_tr);
  textCenter(y, buf);
}

void drawRun(uint32_t now) {
  drawHeader("BERJALAN", now);
  drawTime(13, now - runStart);
  char buf[20];
  font(u8g2_font_6x10_tr);
  snprintf(buf, sizeof(buf), "Indeks %u/%u", runStep + 1, ROUTE_STEPS[cfg.route]);
  textCenter(41, buf);
  // posisi garis di bawah robot
  oled.drawFrame(14, 55, 100, 7);
  oled.drawVLine(64, 53, 2);
  int16_t x = 64 + (int32_t)linePos * 46 / 1000;
  oled.drawBox(x - 2, 56, 5, 5);
}

void drawDone(uint32_t now) {
  drawHeader(runStopped ? "BERHENTI" : "SELESAI", now);
  drawTime(14, runTimeMs);
  char buf[24];
  font(u8g2_font_6x10_tr);
  snprintf(buf, sizeof(buf), "detik, indeks %u/%u", runStep, ROUTE_STEPS[cfg.route]);
  textCenter(41, buf);
  drawFooter("TOMBOL APA SAJA: LANJUT");
}

void drawToast(uint32_t now) {
  if (!toastMsg || (int32_t)(now - toastUntil) >= 0) return;
  font(u8g2_font_6x10_tr);
  int16_t w = oled.getStrWidth(toastMsg) + 12;
  int16_t x = (128 - w) / 2;
  oled.setDrawColor(0);
  oled.drawBox(x - 2, 20, w + 4, 21);
  oled.setDrawColor(1);
  oled.drawRFrame(x, 22, w, 17, 3);
  oled.drawStr(x + 6, 26, toastMsg);
}

void draw(uint32_t now) {
  oled.clearBuffer();
  switch (screen) {
    case SCR_HOME: drawHome(now); break;
    case SCR_MENU: drawMenu(now); break;
    case SCR_ROUTE: drawRoute(now); break;
    case SCR_CALIB: drawCalib(now); break;
    case SCR_SENSOR: drawSensor(now); break;
    case SCR_PID: drawPid(now); break;
    case SCR_MOTOR: drawMotor(now); break;
    case SCR_INFO: drawInfo(now); break;
    case SCR_COUNTDOWN: drawCountdown(now); break;
    case SCR_RUN: drawRun(now); break;
    case SCR_DONE: drawDone(now); break;
  }
  drawToast(now);
  oled.sendBuffer();
}

// ------------------------------------------------------------------ setup & loop
void setup() {
  Serial.begin(115200);
#if SIMULASI
  for (uint8_t i = 0; i < 5; i++) pinMode(BTN_PINS[i], INPUT_PULLUP);
#endif
  oled.setBusClock(400000);
  oled.begin();
  oled.setFontMode(1);  // huruf transparan, supaya teks putih di atas kotak hitam bisa digambar
  updateBattery();
  Serial.println("LFM X1 simulasi OLED siap");
}

void loop() {
  static uint32_t lastSensor = 0, lastBat = 0, lastDraw = 0;
  uint32_t now = millis();

  Button b = pollButton(now);
  if (b != BTN_NONE) {
    if (!btn.repeat) {
      pressScreen = screen;
      Serial.printf("tombol %s\n", BTN_NAMES[b]);
    }
    handleInput(b, now);
  }
  if (backHeldLong(now) && screen != SCR_HOME) goTo(SCR_HOME, now);
  updateLogic(now);

  if (now - lastSensor >= 20) { lastSensor = now; updateFakeSensors(now); }
  if (now - lastBat >= 100) { lastBat = now; updateBattery(); }
  if (now - lastDraw >= 40) { lastDraw = now; draw(now); }
}
