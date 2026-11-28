// main.cpp — program robot LFM X1: menu OLED + 5 tombol (Ui.cpp), perintah serial untuk tes (Console.cpp),
// rute path planning per indeks (Routes.cpp). Logika robot ada di library LineFollower.
//
// loop() tidak pernah menunggu: tiap putaran mengerjakan satu langkah mode aktif (rute, ikut garis, kalibrasi,
// tes motor), lalu serial dan menu. Layar OLED (±25 ms per kirim lewat I2C) tidak digambar saat robot berjalan
// supaya PID tetap 1 kHz.
#include <Arduino.h>
#include <Preferences.h>

#include "App.h"
#include "Routes.h"

LineFollower robot;
Settings cfg;
AppMode mode = MODE_IDLE;

uint32_t runStartMs = 0, runTimeMs = 0;
uint8_t runIndexReached = 0;
const char* runMessage = "";
bool calSpin = false;
uint32_t calStartMs = 0;
uint16_t calDurationMs = 3000;

static LfStep routeBuf[MAX_STEPS];
static uint8_t routeLen = 0;
static uint32_t motorUntil = 0;  // 0 = tes motor jalan terus sampai stop
static uint32_t lostSince = 0;
static const uint32_t FOLLOW_LOST_STOP_MS = 1000;

// ---------------------------------------------------------------- pengaturan
float cfgKp() { return cfg.kp1000 / 1000.0f; }
float cfgKd() { return cfg.kd10 / 10.0f; }
int cfgSpeedPwm() { return cfg.speedPwm; }

void saveSettings() {
  Preferences p;
  if (!p.begin("lfm_app", false)) return;
  p.putBytes("cfg", &cfg, sizeof(cfg));
  p.end();
}

static void loadSettings() {
  Preferences p;
  if (p.begin("lfm_app", true)) {
    Settings s;
    if (p.getBytesLength("cfg") == sizeof(s) && p.getBytes("cfg", &s, sizeof(s)) == sizeof(s)) cfg = s;
    p.end();
  }
  if (cfg.route >= ROUTE_COUNT) cfg.route = 0;
  cfg.kp1000 = constrain(cfg.kp1000, 0, 999);
  cfg.kd10 = constrain(cfg.kd10, 0, 999);
  cfg.speedPwm = constrain(cfg.speedPwm, 0, 255);
}

void applySettings() {
  robot.setLineColor(cfg.blackLine);
  robot.setPID(cfgKp(), cfgKd());
}

// ---------------------------------------------------------------- mulai / berhenti
static const char* const TRIG_NAMES[] = {"persimpangan", "cabang kiri", "cabang kanan", "kiri+kanan", "ujung garis",
                                         "langsung"};
static const char* const ACT_NAMES[] = {"lurus", "belok kiri", "belok kanan", "putar balik", "berhenti"};

bool startRoute(uint8_t routeNo) {
  if (mode != MODE_IDLE) stopAll(nullptr);
  if (!robot.isCalibrated()) {
    Serial.println(F("Rute tidak dimulai: sensor belum dikalibrasi"));
    return false;
  }
  routeLen = buildRoute(routeNo, (uint8_t)cfgSpeedPwm(), routeBuf, MAX_STEPS);
  if (routeLen == 0) {
    Serial.println(F("Rute tidak dimulai: rute kosong / tidak ada jalan"));
    return false;
  }
  applySettings();
  robot.setRouteBeep(true);
  Serial.printf("Rute %u \"%s\", %u indeks:\n", routeNo + 1, ROUTES[routeNo].name, routeLen);
  for (uint8_t i = 0; i < routeLen; i++) {
    const LfStep& s = routeBuf[i];
    Serial.printf("  %2u: jika %s lakukan %s, lalu ikuti garis %s kec %u sejauh %u mm\n", i + 1,
                  TRIG_NAMES[s.trigger], ACT_NAMES[s.action], s.whiteLine ? "putih" : "hitam", s.speed, s.followMm);
  }
  robot.routeBegin(routeBuf, routeLen);
  mode = MODE_ROUTE;
  runStartMs = millis();
  runIndexReached = 0;
  runMessage = "";
  return true;
}

bool startFollow() {
  if (mode != MODE_IDLE) stopAll(nullptr);
  if (!robot.isCalibrated()) Serial.println(F("PERINGATAN: belum kalibrasi"));
  applySettings();
  robot.resetFollow();
  lostSince = 0;
  mode = MODE_FOLLOW;
  return true;
}

void startCalibration(bool spin) {
  if (mode != MODE_IDLE) stopAll(nullptr);
  calSpin = spin;
  calStartMs = millis();
  robot.calibrationStart();
  robot.beep(60);
  mode = MODE_CALIB;
}

void finishCalibration() {
  if (calSpin) robot.stop();
  bool ok = robot.calibrationFinish(true);
  mode = MODE_IDLE;
  robot.beep(ok ? 60 : 400);
  if (ok) {
    Serial.println(F("Kalibrasi berhasil, disimpan ke NVS"));
  } else {
    Serial.print(F("Kalibrasi GAGAL, sensor tanpa beda gelap-terang:"));
    for (uint8_t i = 0; i < LineFollower::SENSOR_COUNT; i++)
      if (robot.calibrationBadMask() & (1u << i)) Serial.printf(" S%u", i + 1);
    Serial.println();
  }
}

void startMotorTest(int left, int right, uint32_t ms) {
  if (mode != MODE_IDLE) stopAll(nullptr);
  robot.motor(left, right);
  motorUntil = ms ? (millis() + ms) | 1 : 0;
  mode = MODE_MOTOR;
}

void stopAll(const char* why) {
  AppMode was = mode;
  mode = MODE_IDLE;
  if (was == MODE_ROUTE) {
    robot.routeStop();
    runTimeMs = millis() - runStartMs;
    runIndexReached = robot.routeIndex() - 1;
    runMessage = "Dihentikan";
    uiRouteFinished();
  }
  robot.stop();
  if (why) Serial.printf("stop (%s)\n", why);
}

// ---------------------------------------------------------------- langkah tiap mode
static void stepRoute() {
  static uint8_t lastIdx = 0;
  LfRouteState s = robot.routeUpdate();
  if (robot.routeIndex() != lastIdx) {
    lastIdx = robot.routeIndex();
    Serial.printf("[%5lu ms] indeks %u\n", (unsigned long)(millis() - runStartMs), lastIdx);
  }
  if (s == ROUTE_RUNNING) return;
  lastIdx = 0;
  mode = MODE_IDLE;
  runTimeMs = millis() - runStartMs;
  runIndexReached = (s == ROUTE_DONE) ? robot.routeCount() : robot.routeIndex() - 1;
  runMessage = robot.routeMessage();
  robot.beep(s == ROUTE_DONE ? 250 : 700);
  Serial.printf("%s, %lu.%02lu s, indeks %u/%u\n", runMessage, (unsigned long)(runTimeMs / 1000),
                (unsigned long)(runTimeMs % 1000 / 10), runIndexReached, robot.routeCount());
  uiRouteFinished();
}

static void stepFollow() {
  robot.follow(cfgSpeedPwm(), cfgKp(), cfgKd());
  if (robot.lineDetected()) {
    lostSince = 0;
  } else if (lostSince == 0) {
    lostSince = millis() | 1;
  } else if (millis() - lostSince >= FOLLOW_LOST_STOP_MS) {
    stopAll("garis hilang 1 s");
    robot.beep(300);
  }
}

static void stepCalibration() {
  uint32_t t = millis() - calStartMs;
  if (calSpin) {
    // ayun kanan 1 bagian, kiri 2 bagian, kanan 1 bagian (sama dengan LineFollower::calibrate)
    uint32_t phase = (t / Config::CAL_SWING_MS) % 4;
    int dir = (phase == 0 || phase == 3) ? 1 : -1;
    robot.motor(dir * Config::CAL_SPIN_PWM, -dir * Config::CAL_SPIN_PWM);
  }
  robot.calibrationUpdate();
  if (t >= calDurationMs) finishCalibration();
}

static void stepMotor() {
  if (motorUntil && (int32_t)(millis() - motorUntil) >= 0) {
    robot.stop();
    mode = MODE_IDLE;
    Serial.println(F("motor berhenti (waktu habis)"));
  }
}

// ---------------------------------------------------------------- setup & loop
void setup() {
  Serial.begin(115200);
  robot.begin();  // juga memuat kalibrasi dari NVS
  loadSettings();
  applySettings();
  uiBegin();
  consoleBegin();
  robot.beep(80);
  Serial.printf("\nLFM X1 firmware %s siap. Kalibrasi: %s. Ketik help.\n", LF_VERSION,
                robot.isCalibrated() ? "ada" : "BELUM");
}

void loop() {
  consolePoll();
  switch (mode) {
    case MODE_ROUTE: stepRoute(); break;
    case MODE_FOLLOW: stepFollow(); break;
    case MODE_CALIB: stepCalibration(); break;
    case MODE_MOTOR: stepMotor(); break;
    default: break;
  }
  uiUpdate();

  // Peringatan baterai lemah saat diam: bunyi tiap 10 s
  static uint32_t lastBatWarn = 0;
  if (mode == MODE_IDLE && millis() - lastBatWarn >= 10000) {
    lastBatWarn = millis();
    if (robot.batteryLow()) {
      robot.beep(150);
      Serial.printf("PERINGATAN: baterai lemah %.2f V\n", robot.batteryVoltage());
    }
  }
}
