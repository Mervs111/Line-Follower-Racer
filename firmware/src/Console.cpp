// Console.cpp — perintah serial untuk tes per bagian (115200 baud, akhiri dengan Enter). Ketik help.
// Urutan tes di robot baru: docs/firmware-uji.md.
#include "App.h"
#include "Routes.h"
#include "SerialCommand.h"

static SerialCommand cmd;

enum StreamMode : uint8_t { STREAM_NONE, STREAM_RAW, STREAM_POS, STREAM_ENC, STREAM_BTN };
static StreamMode streamMode = STREAM_NONE;
static const char* const BUTTON_NAMES[] = {"-", "KEMBALI", "ATAS", "OK", "BAWAH", "LANJUT"};

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
      robot.readSensors();
      const uint16_t* s = robot.sensorValues();
      for (uint8_t i = 0; i < LineFollower::SENSOR_COUNT; i++) Serial.printf("%4u ", s[i]);
      Serial.printf("| pos %5d %s%s%s\n", robot.position(), robot.branchLeft() ? "<KIRI " : "",
                    robot.branchRight() ? "KANAN> " : "", robot.lineDetected() ? "" : "(hilang)");
      break;
    }
    case STREAM_ENC:
      Serial.printf("enc kiri %7ld kanan %7ld | jarak %7.1f mm | sudut %6.1f deg\n", robot.encoderLeft(),
                    robot.encoderRight(), robot.distanceMm(), robot.headingDeg());
      break;
    case STREAM_BTN:
      Serial.printf("tombol: %s (%u mV di GPIO34)\n", BUTTON_NAMES[robot.readButton()],
                    (unsigned)analogReadMilliVolts(Pins::BUTTONS));
      break;
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

static void printPid() {
  Serial.printf("kp %.3f  kd %.1f  spd %d (simpan = tulis ke NVS)\n", cfgKp(), cfgKd(), cfgSpeedPwm());
}

static void printHelp() {
  Serial.println(F("--- tes dasar"));
  Serial.println(F("  info | beep <ms> | bat | komp on|off"));
  Serial.println(F("  m <ki> <ka> [ms]   motor -255..255 (+ maju), berhenti sendiri sesudah ms (default 1500, 0 = terus)"));
  Serial.println(F("  stop | lepas       rem / lepas motor (juga menghentikan rute dan ikut garis)"));
  Serial.println(F("  enc [0]            stream encoder, jarak, sudut; enc 0 = reset"));
  Serial.println(F("  btn                stream tombol board interface"));
  Serial.println(F("--- sensor"));
  Serial.println(F("  raw                stream 12 nilai mentah S1..S12 (0-4095, gelap = besar)"));
  Serial.println(F("  cal [ms] [putar]   kalibrasi (default 3000 ms geser dengan tangan; putar = robot berayun)"));
  Serial.println(F("  calshow | muat     tampilkan min/max | muat ulang dari NVS"));
  Serial.println(F("  pos                stream nilai 0-1000 + posisi (-1000..1000) + cabang kiri/kanan"));
  Serial.println(F("  warna hitam|putih  warna garis"));
  Serial.println(F("--- ikut garis"));
  Serial.println(F("  kp <v> | kd <v> | spd <pwm>   atur PID dan kecepatan (tanpa angka = tampilkan)"));
  Serial.println(F("  simpan             simpan kp/kd/spd/warna/rute ke NVS"));
  Serial.println(F("  jalan              ikuti garis sampai stop (berhenti sendiri kalau garis hilang 1 s)"));
  Serial.println(F("--- gerak terukur & path planning (tombol apa pun = batal)"));
  Serial.println(F("  maju <mm> [pwm]    maju lurus (encoder), negatif = mundur"));
  Serial.println(F("  putar <deg> [pwm]  putar di tempat, + = kiri"));
  Serial.println(F("  belok kiri|kanan   putar sampai garis terkunci sensor tengah"));
  Serial.println(F("  indeks <pemicu> <aksi> [mm]   satu indeks: pemicu simpang|kiri|kanan|dua|ujung|langsung,"));
  Serial.println(F("                     aksi lurus|kiri|kanan|balik|berhenti"));
  Serial.println(F("  rute [n]           daftar rute / jalankan rute n"));
  Serial.println(F("Stream (raw/pos/enc/btn): perintah yang sama sekali lagi = berhenti."));
}

static int8_t findWord(const char* w, const char* const* list, uint8_t n) {
  for (uint8_t i = 0; i < n; i++)
    if (!strcmp(w, list[i])) return (int8_t)i;
  return -1;
}

static void reportBlocking(bool ok) {
  Serial.println(ok ? F("selesai") : F("gagal / dibatalkan"));
  robot.routeReset();
}

static void handle(int argc, char** argv) {
  const char* c = argv[0];
  if (!strcmp(c, "help") || !strcmp(c, "?")) {
    printHelp();
  } else if (!strcmp(c, "info")) {
    Serial.printf("LFM X1 firmware %s, Arduino-ESP32 core %s, kalibrasi %s, baterai %.2f V\n", LF_VERSION,
                  LF_CORE3 ? ">= 3" : "2.x", robot.isCalibrated() ? "ada" : "BELUM", robot.batteryVoltage());
  } else if (!strcmp(c, "beep")) {
    robot.beep(argc > 1 ? atoi(argv[1]) : 100);
  } else if (!strcmp(c, "bat")) {
    uint16_t mv = robot.batteryMillivolts();
    if (mv == 0) Serial.println(F("baterai tidak terbaca (hanya USB?)"));
    else Serial.printf("baterai %.2f V%s\n", mv / 1000.0f, robot.batteryLow() ? " LEMAH, segera cas" : "");
  } else if (!strcmp(c, "komp") && argc > 1) {
    bool on = strcmp(argv[1], "off") != 0;
    robot.setVoltageCompensation(on);
    Serial.printf("kompensasi tegangan %s\n", on ? "nyala" : "mati");
  } else if (!strcmp(c, "m") && argc >= 3) {
    int l = atoi(argv[1]), r = atoi(argv[2]);
    uint32_t ms = argc > 3 ? strtoul(argv[3], nullptr, 10) : 1500;
    startMotorTest(l, r, ms);
    Serial.printf("motor kiri %d kanan %d%s\n", l, r, ms ? "" : " (sampai stop)");
  } else if (!strcmp(c, "stop")) {
    stopAll("perintah");
  } else if (!strcmp(c, "lepas")) {
    stopAll(nullptr);
    robot.release();
  } else if (!strcmp(c, "enc")) {
    if (argc > 1 && !strcmp(argv[1], "0")) {
      robot.resetEncoders();
      Serial.println(F("encoder direset"));
    } else {
      toggleStream(STREAM_ENC);
    }
  } else if (!strcmp(c, "btn")) {
    toggleStream(STREAM_BTN);
  } else if (!strcmp(c, "raw")) {
    toggleStream(STREAM_RAW);
  } else if (!strcmp(c, "pos")) {
    toggleStream(STREAM_POS);
  } else if (!strcmp(c, "cal")) {
    calDurationMs = argc > 1 ? (uint16_t)atoi(argv[1]) : 3000;
    bool spin = argc > 2 && !strcmp(argv[2], "putar");
    Serial.printf("kalibrasi %u ms%s...\n", calDurationMs, spin ? " (robot berayun)" : ", geser robot melintasi garis");
    startCalibration(spin);
  } else if (!strcmp(c, "calshow")) {
    printCalibration();
  } else if (!strcmp(c, "muat")) {
    Serial.println(robot.loadCalibration() ? F("kalibrasi dimuat") : F("belum ada kalibrasi di NVS"));
  } else if (!strcmp(c, "warna") && argc > 1) {
    cfg.blackLine = strcmp(argv[1], "putih") != 0;
    applySettings();
    Serial.println(cfg.blackLine ? F("garis hitam") : F("garis putih"));
  } else if (!strcmp(c, "kp")) {
    if (argc > 1) cfg.kp1000 = (int16_t)constrain(lroundf(atof(argv[1]) * 1000.0f), 0L, 999L);
    applySettings();
    printPid();
  } else if (!strcmp(c, "kd")) {
    if (argc > 1) cfg.kd10 = (int16_t)constrain(lroundf(atof(argv[1]) * 10.0f), 0L, 999L);
    applySettings();
    printPid();
  } else if (!strcmp(c, "spd")) {
    if (argc > 1) cfg.speedPwm = (int16_t)constrain(atoi(argv[1]), 0, 255);
    printPid();
  } else if (!strcmp(c, "simpan")) {
    saveSettings();
    Serial.println(F("pengaturan disimpan"));
  } else if (!strcmp(c, "jalan")) {
    printPid();
    startFollow();
  } else if (!strcmp(c, "maju") && argc > 1) {
    stopAll(nullptr);
    robot.routeReset();
    reportBlocking(robot.forwardMm(argc > 2 ? atoi(argv[2]) : Config::APPROACH_PWM, atoi(argv[1])));
  } else if (!strcmp(c, "putar") && argc > 1) {
    stopAll(nullptr);
    robot.routeReset();
    reportBlocking(robot.turnDegrees(argc > 2 ? atoi(argv[2]) : Config::TURN_PWM, atoi(argv[1])));
  } else if (!strcmp(c, "belok") && argc > 1) {
    stopAll(nullptr);
    robot.routeReset();
    reportBlocking(robot.turnToLine(!strcmp(argv[1], "kiri"), argc > 2 ? atoi(argv[2]) : Config::TURN_PWM));
  } else if (!strcmp(c, "indeks") && argc >= 3) {
    static const char* const TRIG[] = {"simpang", "kiri", "kanan", "dua", "ujung", "langsung"};
    static const char* const ACT[] = {"lurus", "kiri", "kanan", "balik", "berhenti"};
    int8_t t = findWord(argv[1], TRIG, 6), a = findWord(argv[2], ACT, 5);
    if (t < 0 || a < 0) {
      Serial.println(F("pemicu: simpang|kiri|kanan|dua|ujung|langsung, aksi: lurus|kiri|kanan|balik|berhenti"));
      return;
    }
    stopAll(nullptr);
    robot.routeReset();
    applySettings();
    bool ok = robot.runIndex((uint8_t)t, (uint8_t)a, cfgSpeedPwm(), argc > 3 ? atoi(argv[3]) : 80);
    robot.stop();
    if (!ok) Serial.println(robot.routeMessage());
    reportBlocking(ok);
  } else if (!strcmp(c, "rute")) {
    if (argc < 2) {
      for (uint8_t i = 0; i < ROUTE_COUNT; i++) Serial.printf("  %u: %s\n", i + 1, ROUTES[i].name);
      return;
    }
    int n = atoi(argv[1]);
    if (n >= 1 && n <= ROUTE_COUNT) startRoute((uint8_t)(n - 1));
  } else {
    Serial.printf("Perintah tidak dikenal: %s (ketik help)\n", c);
  }
}

void consoleBegin() {}

void consolePoll() {
  int argc;
  char** argv;
  if (cmd.poll(Serial, argc, argv)) handle(argc, argv);
  static uint32_t lastStream = 0;
  if (streamMode != STREAM_NONE && mode == MODE_IDLE && millis() - lastStream >= 100) {
    lastStream = millis();
    printStream();
  }
}
