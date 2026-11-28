// main.cpp — test harness LFM X1: perintah serial + layar OLED.
// M0: serial jalan, OLED menyala dengan titik berkedip, buzzer bunyi saat start.
// M1: motor lewat perintah serial "m <kiri> <kanan> [ms]".
// M2: "raw" stream sensor mentah. M3: "cal", "pos", "muat", "warna". M4: "kp", "kd", "spd", "jalan".
// M5: "enc", "bat", "btn", "komp", cabang kiri/kanan di "pos", peringatan baterai lemah.
#include <Arduino.h>
#include <LineFollower.h>
#include <U8g2lib.h>
#include <Wire.h>

#include "SerialCommand.h"

LineFollower robot;
U8G2_SSD1306_128X64_NONAME_F_HW_I2C oled(U8G2_R0, U8X8_PIN_NONE);
SerialCommand cmd;

uint32_t motorStopAt = 0;  // 0 = motor jalan terus sampai "stop"

// M4: PID ikut garis
float kp = 0.07f, kd = 3.5f;
int baseSpeed = 120;
bool following = false;
uint32_t lostSince = 0;  // 0 = garis terlihat
const uint32_t LOST_STOP_MS = 1000;  // garis hilang selama ini saat "jalan" -> berhenti

// Data yang dikirim terus ke serial tiap 100 ms (perintah yang sama sekali lagi = berhenti)
enum StreamMode : uint8_t { STREAM_NONE, STREAM_RAW, STREAM_POS, STREAM_ENC, STREAM_BTN };
const char* const BUTTON_NAMES[] = {"-", "KEMBALI", "ATAS", "OK", "BAWAH", "LANJUT"};
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
      Serial.printf("| pos %5d %s%s%s\n", pos, robot.branchLeft() ? "<KIRI " : "",
                    robot.branchRight() ? "KANAN> " : "", seen ? "" : "(hilang)");
      break;
    }
    case STREAM_ENC:
      Serial.printf("enc kiri %7ld kanan %7ld | jarak %7.1f mm | sudut %6.1f deg\n", robot.encoderLeft(),
                    robot.encoderRight(), robot.distanceMm(), robot.headingDeg());
      break;
    case STREAM_BTN: {
      uint8_t b = robot.readButton();
      Serial.printf("tombol: %s (%u mV di GPIO34)\n", BUTTON_NAMES[b], analogReadMilliVolts(Pins::BUTTONS));
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
  Serial.println(F("  kp <v> / kd <v> / spd <v>  atur PID dan kecepatan dasar (tanpa angka = tampilkan)"));
  Serial.println(F("  jalan           ikuti garis sampai stop (berhenti sendiri kalau garis hilang 1 s)"));
  Serial.println(F("  enc             stream encoder, jarak, sudut; enc 0 = reset"));
  Serial.println(F("  bat             tegangan baterai"));
  Serial.println(F("  btn             stream tombol board interface"));
  Serial.println(F("  komp on|off     kompensasi tegangan motor (PWM x 6,0 V / V_baterai)"));
}

static void printPid() { Serial.printf("kp %.3f  kd %.2f  spd %d\n", kp, kd, baseSpeed); }

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
    following = false;
    Serial.println(F("stop"));
  } else if (!strcmp(c, "kp")) {
    if (argc > 1) kp = atof(argv[1]);
    printPid();
  } else if (!strcmp(c, "kd")) {
    if (argc > 1) kd = atof(argv[1]);
    printPid();
  } else if (!strcmp(c, "spd")) {
    if (argc > 1) baseSpeed = constrain(atoi(argv[1]), 0, 255);
    printPid();
  } else if (!strcmp(c, "jalan")) {
    if (!robot.isCalibrated()) Serial.println(F("PERINGATAN: belum kalibrasi"));
    printPid();
    motorStopAt = 0;
    lostSince = 0;
    robot.resetFollow();
    following = true;
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
  } else if (!strcmp(c, "enc")) {
    if (argc > 1 && !strcmp(argv[1], "0")) {
      robot.resetEncoders();
      Serial.println(F("encoder direset"));
    } else {
      toggleStream(STREAM_ENC);
    }
  } else if (!strcmp(c, "bat")) {
    uint16_t mv = robot.batteryMillivolts();
    if (mv == 0) Serial.println(F("baterai tidak terbaca (hanya USB?)"));
    else Serial.printf("baterai %.2f V%s\n", mv / 1000.0f, robot.batteryLow() ? " LEMAH, segera cas" : "");
  } else if (!strcmp(c, "btn")) {
    toggleStream(STREAM_BTN);
  } else if (!strcmp(c, "komp") && argc > 1) {
    bool on = strcmp(argv[1], "off") != 0;
    robot.setVoltageCompensation(on);
    Serial.printf("kompensasi tegangan %s\n", on ? "nyala" : "mati");
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
  Serial.println(F("\nLFM X1 siap (M5). Ketik help."));
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

  if (following) {
    robot.follow(baseSpeed, kp, kd);
    if (robot.lineDetected()) {
      lostSince = 0;
    } else if (lostSince == 0) {
      lostSince = millis() | 1;
    } else if (millis() - lostSince >= LOST_STOP_MS) {
      robot.stop();
      following = false;
      robot.beep(300);
      Serial.println(F("garis hilang 1 s: berhenti"));
    }
    return;  // saat jalan: jangan kirim layar OLED (±25 ms I2C) dan stream, supaya PID tetap 1 kHz
  }

  // Peringatan baterai lemah: bunyi + pesan tiap 10 s
  static uint32_t lastBatWarn = 0;
  if (millis() - lastBatWarn >= 10000) {
    lastBatWarn = millis();
    if (robot.batteryLow()) {
      robot.beep(150);
      Serial.printf("PERINGATAN: baterai lemah %.2f V\n", robot.batteryVoltage());
    }
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
