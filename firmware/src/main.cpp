// main.cpp — test harness LFM X1: perintah serial + layar OLED.
// M0: serial jalan, OLED menyala dengan titik berkedip, buzzer bunyi saat start.
// M1: motor lewat perintah serial "m <kiri> <kanan> [ms]".
#include <Arduino.h>
#include <LineFollower.h>
#include <U8g2lib.h>
#include <Wire.h>

#include "SerialCommand.h"

LineFollower robot;
U8G2_SSD1306_128X64_NONAME_F_HW_I2C oled(U8G2_R0, U8X8_PIN_NONE);
SerialCommand cmd;

uint32_t motorStopAt = 0;  // 0 = motor jalan terus sampai "stop"

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
  Serial.println(F("\nLFM X1 siap (M1). Ketik help."));
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
