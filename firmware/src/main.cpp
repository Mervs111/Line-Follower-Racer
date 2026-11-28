// main.cpp — test harness LFM X1: perintah serial + layar OLED.
// M0: serial jalan, OLED menyala dengan titik berkedip, buzzer bunyi saat start.
// M1: motor lewat perintah serial "m <kiri> <kanan> [ms]".
// M2: "raw" stream sensor mentah. M3: "cal", "pos", "muat", "warna".
#include <Arduino.h>
#include <LineFollower.h>
#include <U8g2lib.h>
#include <Wire.h>

#include "SerialCommand.h"

LineFollower robot;
U8G2_SSD1306_128X64_NONAME_F_HW_I2C oled(U8G2_R0, U8X8_PIN_NONE);
SerialCommand cmd;

uint32_t motorStopAt = 0;  // 0 = motor jalan terus sampai "stop"

// Data yang dikirim terus ke serial tiap 100 ms (perintah yang sama sekali lagi = berhenti)
enum StreamMode : uint8_t { STREAM_NONE, STREAM_RAW, STREAM_POS };
StreamMode streamMode = STREAM_NONE;

static void toggleStream(StreamMode m) {
  streamMode = (streamMode == m) ? STREAM_NONE : m;
  if (streamMode == STREAM_NONE) Serial.println(F("stream berhenti"));
}

static void printStream() {
  uint16_t v[LineFollower::SENSOR_COUNT];
  switch (streamMode) {
    case STREAM_RAW:
      robot.readRaw(v);
      for (uint8_t i = 0; i < LineFollower::SENSOR_COUNT; i++) Serial.printf("%4u ", v[i]);
      Serial.println();
      break;
    case STREAM_POS: {
      int pos = robot.position();
      bool seen = robot.lineDetected();
      const uint16_t* s = robot.sensorValues();
      for (uint8_t i = 0; i < LineFollower::SENSOR_COUNT; i++) Serial.printf("%4u ", s[i]);
      Serial.printf("| pos %5d %s\n", pos, seen ? "" : "(hilang)");
      break;
    }
    default:
      break;
  }
}

static void printCalibration() {
  const uint16_t* mn = robot.calibrationMin();
  const uint16_t* mx = robot.calibrationMax();
  Serial.print(F("min: "));
  for (uint8_t i = 0; i < LineFollower::SENSOR_COUNT; i++) Serial.printf("%4u ", mn[i]);
  Serial.print(F("\nmax: "));
  for (uint8_t i = 0; i < LineFollower::SENSOR_COUNT; i++) Serial.printf("%4u ", mx[i]);
  Serial.printf("\nterkalibrasi: %s\n", robot.isCalibrated() ? "ya" : "BELUM");
}

// ---------------------------------------------------------------- perintah serial
static void printHelp() {
  Serial.println(F("Perintah:"));
  Serial.println(F("  help            daftar perintah"));
  Serial.println(F("  info            versi firmware dan core"));
  Serial.println(F("  beep <ms>       bunyikan buzzer"));
  Serial.println(F("  m <ki> <ka> [ms] motor -255..255 (+ maju), berhenti sendiri sesudah ms (default 1500)"));
  Serial.println(F("  m <ki> <ka> 0   motor jalan terus sampai stop"));
  Serial.println(F("  stop            rem motor (Enter kosong tidak menghentikan; ketik stop)"));
  Serial.println(F("  lepas           lepas motor (roda bebas)"));
  Serial.println(F("  raw             stream 12 nilai mentah S1..S12 (0-4095, gelap = besar); raw lagi = berhenti"));
  Serial.println(F("  cal [ms] [putar] kalibrasi (default 3000 ms, geser robot dengan tangan; putar = robot berayun)"));
  Serial.println(F("  calshow         tampilkan min/max kalibrasi"));
  Serial.println(F("  muat            muat kalibrasi dari NVS"));
  Serial.println(F("  pos             stream nilai 0-1000 + posisi garis (-1000..1000); pos lagi = berhenti"));
  Serial.println(F("  warna hitam|putih  warna garis"));
}

static void handleCommand(int argc, char** argv) {
  const char* c = argv[0];
  if (!strcmp(c, "help") || !strcmp(c, "?")) {
    printHelp();
  } else if (!strcmp(c, "info")) {
    Serial.printf("LFM X1 firmware %s, Arduino-ESP32 core %s\n", LF_VERSION, LF_CORE3 ? "3.x" : "2.x");
  } else if (!strcmp(c, "beep")) {
    robot.beep(argc > 1 ? atoi(argv[1]) : 100);
  } else if (!strcmp(c, "m") && argc >= 3) {
    int l = atoi(argv[1]), r = atoi(argv[2]);
    uint32_t ms = argc > 3 ? strtoul(argv[3], nullptr, 10) : 1500;
    robot.motor(l, r);
    motorStopAt = ms ? (millis() + ms) | 1 : 0;
    Serial.printf("motor kiri %d kanan %d%s\n", l, r, ms ? "" : " (sampai stop)");
  } else if (!strcmp(c, "stop")) {
    robot.stop();
    motorStopAt = 0;
    Serial.println(F("stop"));
  } else if (!strcmp(c, "lepas")) {
    robot.release();
    motorStopAt = 0;
  } else if (!strcmp(c, "raw")) {
    toggleStream(STREAM_RAW);
  } else if (!strcmp(c, "cal")) {
    uint16_t ms = argc > 1 ? (uint16_t)atoi(argv[1]) : 3000;
    bool spin = argc > 2 && !strcmp(argv[2], "putar");
    Serial.printf("kalibrasi %u ms%s...\n", ms, spin ? " (robot berayun)" : ", geser robot melintasi garis");
    robot.beep(60);
    bool ok = robot.calibrate(ms, spin);
    robot.beep(ok ? 60 : 400);
    if (!ok) {
      Serial.print(F("GAGAL, sensor tanpa beda gelap-terang:"));
      for (uint8_t i = 0; i < LineFollower::SENSOR_COUNT; i++)
        if (robot.calibrationBadMask() & (1u << i)) Serial.printf(" S%u", i + 1);
      Serial.println();
    }
    printCalibration();
  } else if (!strcmp(c, "calshow")) {
    printCalibration();
  } else if (!strcmp(c, "muat")) {
    Serial.println(robot.loadCalibration() ? F("kalibrasi dimuat") : F("belum ada kalibrasi di NVS"));
  } else if (!strcmp(c, "pos")) {
    toggleStream(STREAM_POS);
  } else if (!strcmp(c, "warna") && argc > 1) {
    robot.setLineColor(strcmp(argv[1], "putih") != 0);
    Serial.println(robot.lineIsBlack() ? F("garis hitam") : F("garis putih"));
  } else {
    Serial.printf("Perintah tidak dikenal: %s (ketik help)\n", c);
  }
}

// ---------------------------------------------------------------- setup & loop
void setup() {
  Serial.begin(115200);
  robot.begin();

  Wire.begin(Pins::I2C_SDA, Pins::I2C_SCL);
  oled.setBusClock(400000);
  oled.begin();

  robot.beep(80);
  Serial.println(F("\nLFM X1 siap (M3). Ketik help."));
}

void loop() {
  int argc;
  char** argv;
  if (cmd.poll(Serial, argc, argv)) handleCommand(argc, argv);

  if (motorStopAt && (int32_t)(millis() - motorStopAt) >= 0) {
    robot.stop();
    motorStopAt = 0;
    Serial.println(F("motor berhenti (waktu habis)"));
  }

  static uint32_t lastStream = 0;
  if (streamMode != STREAM_NONE && millis() - lastStream >= 100) {
    lastStream = millis();
    printStream();
  }

  // Kedip titik di OLED tanpa delay()
  static uint32_t lastBlink = 0;
  static bool on = false;
  uint32_t now = millis();
  if (now - lastBlink >= 500) {
    lastBlink = now;
    on = !on;
    oled.clearBuffer();
    oled.setFont(u8g2_font_helvB10_tr);
    oled.drawStr(0, 14, "LFM X1");
    oled.setFont(u8g2_font_6x10_tr);
    oled.drawStr(0, 32, "Firmware " LF_VERSION);
    oled.drawStr(0, 46, "Ketik help di serial");
    if (on) oled.drawDisc(120, 8, 4);
    oled.sendBuffer();
  }
}
