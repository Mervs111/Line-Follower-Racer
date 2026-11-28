// Ui.cpp — menu OLED SSD1306 128x64 + 5 tombol board interface (sama dengan simulasi/wokwi-oled, sekarang
// memakai robot asli). Tombol kiri -> kanan: KEMBALI  ATAS  OK  BAWAH  LANJUT.
//   ATAS / BAWAH : pindah pilihan; saat mengedit angka tambah / kurang (tahan = berulang, > 1,5 s = langkah x10)
//   OK / LANJUT  : masuk / pilih / simpan
//   KEMBALI      : kembali / batal; tahan 0,8 s = langsung ke layar utama
//   Robot berjalan: tombol apa pun = STOP
// Layar utama: OK = mulai rute, LANJUT = menu, ATAS/BAWAH = ganti rute.
#include <U8g2lib.h>
#include <Wire.h>

#include "App.h"
#include "Routes.h"

static U8G2_SSD1306_128X64_NONAME_F_HW_I2C oled(U8G2_R0, U8X8_PIN_NONE);

enum Screen : uint8_t {
  SCR_HOME, SCR_MENU, SCR_ROUTE, SCR_CALIB, SCR_SENSOR, SCR_PID, SCR_MOTOR, SCR_INFO, SCR_COUNTDOWN, SCR_RUN,
  SCR_DONE
};
enum CalibView : uint8_t { CAL_IDLE, CAL_RUNNING, CAL_DONE };

// ------------------------------------------------------------------ tombol
static const uint16_t DEBOUNCE_MS = 20;
static const uint16_t REPEAT_DELAY_MS = 400;
static const uint16_t REPEAT_RATE_MS = 80;
static const uint16_t LONG_BACK_MS = 800;
static const uint16_t FAST_STEP_MS = 1500;

struct ButtonState {
  uint8_t last = BTN_NONE;
  uint8_t stable = BTN_NONE;
  uint32_t changedAt = 0;
  uint32_t pressedAt = 0;
  uint32_t nextRepeat = 0;
  bool longFired = false;
  bool repeat = false;
};
static ButtonState btn;

// Event tombol: sekali saat ditekan, lalu berulang untuk ATAS/BAWAH yang ditahan.
static uint8_t pollButton(uint32_t now) {
  uint8_t raw = robot.readButton();
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

static bool backHeldLong(uint32_t now) {
  if (btn.stable != BTN_BACK || btn.longFired || now - btn.pressedAt < LONG_BACK_MS) return false;
  btn.longFired = true;
  return true;
}

static uint32_t heldMs(uint32_t now) { return btn.stable == BTN_NONE ? 0 : now - btn.pressedAt; }

// ------------------------------------------------------------------ keadaan layar
static Screen screen = SCR_HOME;
static Screen pressScreen = SCR_HOME;
static uint32_t screenSince = 0;
static bool needDraw = true;

static void goTo(Screen s, uint32_t now) {
  screen = s;
  screenSince = now;
  needDraw = true;
}

static const char* const MENU_ITEMS[] = {"Mulai", "Pilih rute", "Kalibrasi", "Lihat sensor",
                                         "Atur PID", "Warna garis", "Tes motor", "Info robot"};
static const uint8_t MENU_COUNT = 8;
static uint8_t menuSel = 0, menuTop = 0;
static uint8_t routeSel = 0, routeTop = 0;
static uint8_t routeLens[16];

static CalibView calView = CAL_IDLE;
static bool calOk = false;
static uint8_t sensorPage = 0;

static const char* const PID_LABELS[] = {"Kp", "Kd", "Kecepatan"};
static uint8_t pidSel = 0;
static bool pidEditing = false;
static int16_t pidBackup = 0;

static const char* const MOTOR_ITEMS[] = {"Maju", "Mundur", "Putar kiri", "Putar kanan"};
static uint8_t motorSel = 0;
static const uint16_t MOTOR_TEST_MS = 1500;
static const int MOTOR_TEST_PWM = 120;

static const char* toastMsg = nullptr;
static uint32_t toastUntil = 0;

static void toast(const char* msg, uint32_t now) {
  toastMsg = msg;
  toastUntil = now + 1200;
  needDraw = true;
}

// ------------------------------------------------------------------ input
static int16_t* pidValue(uint8_t row) {
  if (row == 0) return &cfg.kp1000;
  if (row == 1) return &cfg.kd10;
  return &cfg.speedPwm;
}

static void pidChange(int8_t dir, uint32_t now) {
  int16_t step = heldMs(now) > FAST_STEP_MS ? 10 : 1;
  int16_t maxV = pidSel == 2 ? 255 : 999;
  int16_t* v = pidValue(pidSel);
  *v = constrain(*v + dir * step, 0, maxV);
}

static void keepVisible(uint8_t sel, uint8_t& top, uint8_t visible) {
  if (sel < top) top = sel;
  if (sel >= top + visible) top = sel - visible + 1;
}

static void listMove(uint8_t b, uint8_t& sel, uint8_t count) {
  if (b == BTN_UP && sel > 0) sel--;
  if (b == BTN_DOWN && sel < count - 1) sel++;
}

static void requestRun(uint32_t now) {
  if (!robot.isCalibrated()) {
    toast("Kalibrasi dulu!", now);
    return;
  }
  goTo(SCR_COUNTDOWN, now);
}

static void openMenuItem(uint32_t now) {
  switch (menuSel) {
    case 0: requestRun(now); break;
    case 1: routeSel = cfg.route; goTo(SCR_ROUTE, now); break;
    case 2: calView = CAL_IDLE; goTo(SCR_CALIB, now); break;
    case 3: goTo(SCR_SENSOR, now); break;
    case 4: pidEditing = false; goTo(SCR_PID, now); break;
    case 5:
      cfg.blackLine = !cfg.blackLine;
      applySettings();
      saveSettings();
      toast(cfg.blackLine ? "Garis HITAM" : "Garis PUTIH", now);
      break;
    case 6: goTo(SCR_MOTOR, now); break;
    case 7: goTo(SCR_INFO, now); break;
  }
}

static bool repeatAllowed() {
  if (screen != pressScreen) return false;
  return screen == SCR_HOME || screen == SCR_MENU || screen == SCR_ROUTE || screen == SCR_PID ||
         (screen == SCR_MOTOR && mode != MODE_MOTOR);
}

static void handleInput(uint8_t b, uint32_t now) {
  if (btn.repeat && !repeatAllowed()) return;
  bool enter = (b == BTN_OK || b == BTN_NEXT);
  needDraw = true;
  switch (screen) {
    case SCR_HOME:
      if (b == BTN_OK) requestRun(now);
      if (b == BTN_NEXT) goTo(SCR_MENU, now);
      if (b == BTN_UP || b == BTN_DOWN) {
        cfg.route = (b == BTN_UP) ? (cfg.route + ROUTE_COUNT - 1) % ROUTE_COUNT : (cfg.route + 1) % ROUTE_COUNT;
        saveSettings();
      }
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
        saveSettings();
        toast("Rute disimpan", now);
        goTo(SCR_MENU, now);
      }
      if (b == BTN_BACK) goTo(SCR_MENU, now);
      break;

    case SCR_CALIB:
      if (calView == CAL_IDLE) {
        if (b == BTN_OK || b == BTN_NEXT) {
          calDurationMs = 3000;
          startCalibration(b == BTN_OK);  // OK = robot berayun sendiri, LANJUT = geser dengan tangan
          calView = CAL_RUNNING;
        }
        if (b == BTN_BACK) goTo(SCR_MENU, now);
      } else if (calView == CAL_RUNNING) {
        if (b == BTN_BACK) {
          stopAll("kalibrasi dibatalkan");
          calView = CAL_IDLE;
          toast("Dibatalkan", now);
        }
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
        if (enter) {
          pidEditing = true;
          pidBackup = *pidValue(pidSel);
        }
        if (b == BTN_BACK) goTo(SCR_MENU, now);
      } else {
        if (b == BTN_UP) pidChange(+1, now);
        if (b == BTN_DOWN) pidChange(-1, now);
        if (enter) {
          pidEditing = false;
          applySettings();
          saveSettings();
          toast("Tersimpan", now);
        }
        if (b == BTN_BACK) {
          *pidValue(pidSel) = pidBackup;
          pidEditing = false;
        }
      }
      break;

    case SCR_MOTOR:
      if (mode == MODE_MOTOR) {
        stopAll(nullptr);
        break;
      }
      listMove(b, motorSel, 4);
      if (enter) {
        static const int8_t L[] = {1, -1, -1, 1}, R[] = {1, -1, 1, -1};
        startMotorTest(L[motorSel] * MOTOR_TEST_PWM, R[motorSel] * MOTOR_TEST_PWM, MOTOR_TEST_MS);
        screenSince = now;
      }
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
      stopAll("tombol");  // uiRouteFinished() pindah ke layar hasil
      break;

    case SCR_DONE:
      goTo(SCR_HOME, now);
      break;
  }
}

static void draw(uint32_t now);

static void updateLogic(uint32_t now) {
  if (screen == SCR_COUNTDOWN && now - screenSince >= 3000) {
    // layar "BERJALAN" dikirim dulu (±25 ms), baru rute dimulai, supaya PID tidak tertahan di awal jalan
    goTo(SCR_RUN, now);
    draw(now);
    needDraw = false;
    if (!startRoute(cfg.route)) {
      toast("Rute gagal mulai", now);
      goTo(SCR_HOME, now);
    }
  } else if (screen == SCR_CALIB && calView == CAL_RUNNING && mode != MODE_CALIB) {
    calView = CAL_DONE;
    calOk = robot.isCalibrated() && robot.calibrationBadMask() == 0;
    needDraw = true;
  }
}

// ------------------------------------------------------------------ gambar
static void font(const uint8_t* f) {
  oled.setFont(f);
  oled.setFontPosTop();
}

static void textRight(int16_t xRight, int16_t y, const char* s) { oled.drawStr(xRight - oled.getStrWidth(s), y, s); }
static void textCenter(int16_t y, const char* s) { oled.drawStr((128 - oled.getStrWidth(s)) / 2, y, s); }

static void fmtVolt(char* buf, size_t n, uint32_t mv) {
  uint32_t v100 = mv / 10;
  snprintf(buf, n, "%lu.%02luV", (unsigned long)(v100 / 100), (unsigned long)(v100 % 100));
}

static void drawBattery(int16_t x, int16_t y, uint32_t now) {
  uint16_t mv = robot.batteryMillivolts();
  if (robot.batteryLow() && ((now / 300) & 1)) return;  // baterai lemah: kedip
  oled.drawFrame(x, y, 12, 7);
  oled.drawBox(x + 12, y + 2, 2, 3);
  int32_t level = ((int32_t)mv - Config::VBAT_EMPTY_MV) * 10 / (Config::VBAT_FULL_MV - Config::VBAT_EMPTY_MV);
  level = constrain(level, 0, 10);
  if (level > 0) oled.drawBox(x + 1, y + 1, level, 5);
}

static void drawHeader(const char* title, uint32_t now) {
  font(u8g2_font_helvB08_tr);
  oled.drawStr(0, 0, title);
  char buf[8];
  uint16_t mv = robot.batteryMillivolts();
  if (mv) fmtVolt(buf, sizeof(buf), mv);
  else snprintf(buf, sizeof(buf), "USB");
  font(u8g2_font_5x7_tr);
  textRight(111, 1, buf);
  drawBattery(114, 1, now);
  oled.drawHLine(0, 10, 128);
}

static void drawRow(int16_t y, const char* label, const char* value, bool selected) {
  font(u8g2_font_6x10_tr);
  if (selected) {
    oled.drawBox(0, y, 122, 13);
    oled.setDrawColor(0);
  }
  oled.drawStr(3, y + 2, label);
  if (value) textRight(119, y + 2, value);
  oled.setDrawColor(1);
}

static void drawScrollbar(uint8_t top, uint8_t count, uint8_t visible) {
  if (count <= visible) return;
  const int16_t y0 = 12, h = 52;
  oled.drawVLine(125, y0, h);
  int16_t thumbH = h * visible / count;
  int16_t thumbY = y0 + (h - thumbH) * top / (count - visible);
  oled.drawBox(124, thumbY, 3, thumbH);
}

static void drawFooter(const char* s) {
  oled.drawBox(0, 54, 128, 10);
  oled.setDrawColor(0);
  font(u8g2_font_5x7_tr);
  textCenter(55, s);
  oled.setDrawColor(1);
}

static void drawSensorBars(int16_t yBottom, int16_t maxH) {
  const uint16_t* v = robot.sensorValues();
  for (uint8_t i = 0; i < LineFollower::SENSOR_COUNT; i++) {
    int16_t h = (int32_t)v[i] * maxH / 1000;
    int16_t x = 5 + i * 10;
    if (h > 0) oled.drawBox(x, yBottom - h, 8, h);
  }
  oled.drawHLine(4, yBottom + 1, 120);
}

static void drawHome(uint32_t now) {
  drawHeader("LFM X1", now);
  char buf[22];
  font(u8g2_font_6x10_tr);
  snprintf(buf, sizeof(buf), "R%u %s", cfg.route + 1, ROUTES[cfg.route].name);
  oled.drawStr(0, 14, buf);
  oled.drawStr(0, 26, robot.isCalibrated() ? "Kal: OK" : "Kal: BELUM");
  snprintf(buf, sizeof(buf), "%s %d", cfg.blackLine ? "H" : "P", cfg.speedPwm);
  textRight(127, 26, buf);
  drawSensorBars(50, 12);
  drawFooter("OK:MULAI ^v:RUTE >:MENU");
}

static void drawMenu(uint32_t now) {
  drawHeader("MENU", now);
  keepVisible(menuSel, menuTop, 4);
  char val[8];
  for (uint8_t r = 0; r < 4 && menuTop + r < MENU_COUNT; r++) {
    uint8_t i = menuTop + r;
    const char* v = nullptr;
    if (i == 1) {
      snprintf(val, sizeof(val), "R%u", cfg.route + 1);
      v = val;
    }
    if (i == 2) v = robot.isCalibrated() ? "OK" : "!";
    if (i == 5) v = cfg.blackLine ? "Hitam" : "Putih";
    drawRow(12 + r * 13, MENU_ITEMS[i], v, i == menuSel);
  }
  drawScrollbar(menuTop, MENU_COUNT, 4);
}

static void drawRoute(uint32_t now) {
  drawHeader("PILIH RUTE", now);
  keepVisible(routeSel, routeTop, 4);
  char label[20], val[10];
  for (uint8_t r = 0; r < 4 && routeTop + r < ROUTE_COUNT; r++) {
    uint8_t i = routeTop + r;
    snprintf(label, sizeof(label), "%s%s", i == cfg.route ? "*" : " ", ROUTES[i].name);
    snprintf(val, sizeof(val), "%u idx", i < sizeof(routeLens) ? routeLens[i] : 0);
    drawRow(12 + r * 13, label, val, i == routeSel);
  }
  drawScrollbar(routeTop, ROUTE_COUNT, 4);
}

static void drawProgress(int16_t y, uint32_t elapsed, uint32_t total) {
  oled.drawFrame(10, y, 108, 9);
  int16_t w = (int32_t)min(elapsed, total) * 104 / total;
  if (w > 0) oled.drawBox(12, y + 2, w, 5);
}

static void drawCalib(uint32_t now) {
  drawHeader("KALIBRASI", now);
  font(u8g2_font_6x10_tr);
  if (calView == CAL_IDLE) {
    oled.drawStr(0, 14, "Letakkan robot di");
    oled.drawStr(0, 25, "atas garis.");
    oled.drawStr(0, 38, "OK:berayun >:tangan");
    drawFooter("OK/>:MULAI  <:KEMBALI");
  } else if (calView == CAL_RUNNING) {
    oled.drawStr(0, 14, calSpin ? "Robot berayun..." : "Geser lewati garis");
    drawProgress(27, now - calStartMs, calDurationMs);
    drawSensorBars(52, 12);
  } else if (calOk) {
    font(u8g2_font_helvB08_tr);
    textCenter(20, "Selesai!");
    font(u8g2_font_6x10_tr);
    textCenter(34, "Data disimpan");
    drawFooter("TOMBOL APA SAJA: KEMBALI");
  } else {
    font(u8g2_font_helvB08_tr);
    textCenter(14, "GAGAL");
    font(u8g2_font_5x7_tr);
    char buf[40];
    size_t n = snprintf(buf, sizeof(buf), "Sensor:");
    for (uint8_t i = 0; i < LineFollower::SENSOR_COUNT && n < sizeof(buf) - 4; i++)
      if (robot.calibrationBadMask() & (1u << i)) n += snprintf(buf + n, sizeof(buf) - n, " %u", i + 1);
    textCenter(28, buf);
    textCenter(38, "tidak lihat garis+lantai");
    drawFooter("TOMBOL APA SAJA: KEMBALI");
  }
}

static void drawSensor(uint32_t now) {
  drawHeader("SENSOR", now);
  char buf[20];
  const uint16_t* v = robot.sensorValues();
  if (sensorPage == 0) {
    drawSensorBars(44, 31);
    font(u8g2_font_5x7_tr);
    oled.drawStr(3, 47, "S1");
    oled.drawStr(110, 47, "S12");
  } else {
    font(u8g2_font_5x7_tr);
    for (uint8_t i = 0; i < LineFollower::SENSOR_COUNT; i++) {
      snprintf(buf, sizeof(buf), "%u:%u", i + 1, v[i]);
      oled.drawStr((i % 3) * 43, 13 + (i / 3) * 10, buf);
    }
  }
  font(u8g2_font_6x10_tr);
  int pos = robot.position();
  if (robot.lineDetected()) snprintf(buf, sizeof(buf), "Pos %d", pos);
  else snprintf(buf, sizeof(buf), "Hilang %s", pos < 0 ? "<" : ">");
  oled.drawStr(0, 54, buf);
  textRight(127, 54, sensorPage == 0 ? "^v:angka" : "^v:bar");
}

static void drawPid(uint32_t now) {
  drawHeader("ATUR PID", now);
  char val[10];
  for (uint8_t r = 0; r < 3; r++) {
    int16_t v = *pidValue(r);
    if (r == 0) snprintf(val, sizeof(val), "%d.%03d", v / 1000, v % 1000);
    else if (r == 1) snprintf(val, sizeof(val), "%d.%d", v / 10, v % 10);
    else snprintf(val, sizeof(val), "%d", v);
    int16_t y = 12 + r * 13;
    if (pidEditing && r == pidSel) {
      drawRow(y, PID_LABELS[r], nullptr, false);
      int16_t w = oled.getStrWidth(val) + 6;
      if ((now / 400) & 1) {
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

static void drawMotor(uint32_t now) {
  drawHeader("TES MOTOR", now);
  if (mode == MODE_MOTOR) {
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

static void drawInfo(uint32_t now) {
  drawHeader("INFO ROBOT", now);
  char buf[32], v[8];
  font(u8g2_font_5x7_tr);
  snprintf(buf, sizeof(buf), "LFM X1 fw %s core %s", LF_VERSION, LF_CORE3 ? "3+" : "2");
  oled.drawStr(0, 13, buf);
  uint16_t mv = robot.batteryMillivolts();
  if (mv) fmtVolt(v, sizeof(v), mv);
  else snprintf(v, sizeof(v), "USB");
  snprintf(buf, sizeof(buf), "Baterai : %s", v);
  oled.drawStr(0, 22, buf);
  snprintf(buf, sizeof(buf), "Kalibr. : %s", robot.isCalibrated() ? "ada" : "BELUM");
  oled.drawStr(0, 31, buf);
  snprintf(buf, sizeof(buf), "Enc L/R : %ld / %ld", robot.encoderLeft(), robot.encoderRight());
  oled.drawStr(0, 40, buf);
  drawFooter("<:KEMBALI");
}

static void drawCountdown(uint32_t now) {
  uint32_t t = now - screenSince;
  char buf[4];
  snprintf(buf, sizeof(buf), "%lu", (unsigned long)(3 - min(t / 1000, (uint32_t)2)));
  font(u8g2_font_6x10_tr);
  textCenter(2, "Siap...");
  font(u8g2_font_logisoso32_tn);
  textCenter(15, buf);
  drawFooter("TOMBOL APA SAJA: BATAL");
}

static void drawTime(int16_t y, uint32_t ms) {
  char buf[12];
  snprintf(buf, sizeof(buf), "%lu.%02lu", (unsigned long)(ms / 1000), (unsigned long)(ms % 1000 / 10));
  font(u8g2_font_logisoso24_tr);
  textCenter(y, buf);
}

static void drawRun(uint32_t now) {
  // digambar sekali saat mulai; selama jalan layar tidak dikirim supaya PID tidak terganggu
  drawHeader("BERJALAN", now);
  char buf[24];
  font(u8g2_font_helvB10_tr);
  snprintf(buf, sizeof(buf), "Rute %u", cfg.route + 1);
  textCenter(18, buf);
  font(u8g2_font_6x10_tr);
  textCenter(36, ROUTES[cfg.route].name);
  drawFooter("TOMBOL APA SAJA: STOP");
}

static void drawDone(uint32_t now) {
  drawHeader(robot.routeState() == ROUTE_DONE ? "SELESAI" : "BERHENTI", now);
  drawTime(13, runTimeMs);
  char buf[28];
  font(u8g2_font_5x7_tr);
  snprintf(buf, sizeof(buf), "detik, indeks %u/%u", runIndexReached, robot.routeCount());
  textCenter(40, buf);
  textCenter(47, runMessage);
  drawFooter("TOMBOL APA SAJA: LANJUT");
}

static void drawToast(uint32_t now) {
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

static void draw(uint32_t now) {
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

// ------------------------------------------------------------------ antarmuka modul
void uiBegin() {
  Wire.begin(Pins::I2C_SDA, Pins::I2C_SCL);
  oled.setBusClock(400000);
  oled.begin();
  oled.setFontMode(1);
  static LfStep tmp[MAX_STEPS];
  for (uint8_t i = 0; i < ROUTE_COUNT && i < sizeof(routeLens); i++)
    routeLens[i] = buildRoute(i, 100, tmp, MAX_STEPS);
  goTo(SCR_HOME, millis());
}

void uiRouteFinished() {
  screen = SCR_DONE;
  screenSince = millis();
  needDraw = true;
}

void uiUpdate() {
  uint32_t now = millis();
  static uint32_t lastPoll = 0, lastDraw = 0;
  bool moving = (mode == MODE_ROUTE || mode == MODE_FOLLOW);

  // tombol tiap 5 ms (saat berjalan tiap 20 ms: cukup untuk STOP, hemat ADC)
  if (now - lastPoll >= (moving ? 20u : 5u)) {
    lastPoll = now;
    uint8_t b = pollButton(now);
    if (b != BTN_NONE) {
      if (moving) {
        if (!btn.repeat) {
          stopAll("tombol");
          if (screen != SCR_DONE) goTo(SCR_HOME, now);
        }
      } else {
        if (!btn.repeat) pressScreen = screen;
        handleInput(b, now);
      }
    }
    if (!moving && backHeldLong(now) && screen != SCR_HOME) goTo(SCR_HOME, now);
  }
  updateLogic(now);
  if (moving) {
    if (needDraw && screen == SCR_RUN) {  // satu gambar statis sebelum PID berjalan penuh
      needDraw = false;
      draw(now);
    }
    return;
  }

  uint32_t period = (mode == MODE_CALIB) ? 100 : 50;
  if (needDraw || now - lastDraw >= period) {
    needDraw = false;
    lastDraw = now;
    // layar yang menampilkan sensor membaca ulang sensor (saat kalibrasi bar diisi calibrationUpdate)
    if (mode != MODE_CALIB && (screen == SCR_HOME || screen == SCR_SENSOR)) robot.readSensors();
    draw(now);
  }
}
