// LineFollower.h — library utama robot line follower LFM X1 (ESP32 DevKit, 12 sensor QRE1113 + mux, TB6612FNG).
// Fungsi di sini dipanggil langsung oleh blok Mind+ (1 blok = 1 fungsi), jadi namanya dijaga tetap.
// Aturan: tanpa delay() dan String di jalur kendali; kompatibel Arduino-ESP32 core 2.x dan 3.x.
#pragma once

#include <Arduino.h>

#include "LfCompat.h"
#include "Pins.h"
#include "RobotConfig.h"

#define LF_VERSION "0.1.0"

// Nomor tombol board interface, urut kiri -> kanan.
enum LfButton : uint8_t { BTN_NONE = 0, BTN_BACK = 1, BTN_UP = 2, BTN_OK = 3, BTN_DOWN = 4, BTN_NEXT = 5 };

// ---- Path planning per indeks (gaya blok Ichiduino): tiap indeks = pemicu -> aksi -> ikuti garis sejauh mm.
// Pemicu: kapan aksi dijalankan.
enum LfTrigger : uint8_t {
  TRIG_JUNCTION = 0,  // persimpangan apa saja (cabang kiri atau kanan)
  TRIG_LEFT = 1,      // ada cabang kiri
  TRIG_RIGHT = 2,     // ada cabang kanan
  TRIG_BOTH = 3,      // cabang kiri dan kanan (simpang T dari batang / perempatan)
  TRIG_END = 4,       // garis habis (ujung garis)
  TRIG_DIRECT = 5     // langsung, tanpa menunggu sensor
};
// Aksi di persimpangan. Belok dan berhenti dilakukan dengan poros roda tepat di tengah persimpangan (encoder).
enum LfAction : uint8_t {
  ACT_FORWARD = 0,  // lurus melewati persimpangan
  ACT_LEFT = 1,     // belok kiri (putar di tempat sampai garis kiri terkunci sensor tengah)
  ACT_RIGHT = 2,    // belok kanan
  ACT_UTURN = 3,    // putar balik
  ACT_STOP = 4      // berhenti (akhir rute)
};
enum LfRouteState : uint8_t { ROUTE_IDLE = 0, ROUTE_RUNNING = 1, ROUTE_DONE = 2, ROUTE_FAILED = 3 };

struct LfStep {
  uint8_t trigger;    // LfTrigger
  uint8_t action;     // LfAction
  uint8_t speed;      // PWM ikut garis sesudah aksi (dipakai sampai indeks berikutnya beraksi)
  uint16_t followMm;  // sesudah aksi: ikuti garis sejauh ini dulu, pemicu berikutnya belum dicek
  bool whiteLine;     // sesudah aksi ikuti garis putih (false = hitam)
};

class LineFollower {
 public:
  static constexpr uint8_t SENSOR_COUNT = Config::SENSOR_COUNT;

  // Inisialisasi semua pin dan muat kalibrasi dari NVS. Panggil sekali di setup().
  // Motor tetap mati (STBY LOW) sampai motor() dipanggil.
  void begin();

  // ---------------------------------------------------------------- sensor mentah
  // Baca 12 sensor lewat mux ke out[0..11] (S1 paling kiri .. S12 paling kanan), nilai ADC 0-4095.
  // QRE1113 dengan pull-up: makin gelap permukaan, makin besar nilainya.
  void readRaw(uint16_t out[]);

  // ---------------------------------------------------------------- kalibrasi
  // Kalibrasi selama durationMs. spin = false: geser robot melintasi garis dengan tangan (semua sensor harus
  // pernah melihat garis dan lantai). spin = true: robot berayun kiri-kanan sendiri di atas garis.
  // Min/max tiap sensor disimpan ke NVS (Preferences). Return true kalau ke-12 sensor melihat beda gelap-terang.
  // Menunggu sampai selesai (tanpa delay(); loop millis()).
  bool calibrate(uint16_t durationMs = 3000, bool spin = false);
  // Versi tanpa menunggu (untuk menu OLED): start, update berulang-ulang, lalu finish.
  void calibrationStart();
  void calibrationUpdate();
  bool calibrationFinish(bool save = true);
  // Muat kalibrasi dari NVS (begin() sudah memanggilnya). false kalau belum pernah kalibrasi.
  bool loadCalibration();
  bool saveCalibration();
  bool isCalibrated() const { return calibrated_; }
  // Bit i = 1 kalau sensor S(i+1) gagal di kalibrasi terakhir (beda gelap-terang terlalu kecil).
  uint16_t calibrationBadMask() const { return calBadMask_; }
  const uint16_t* calibrationMin() const { return calMin_; }
  const uint16_t* calibrationMax() const { return calMax_; }

  // ---------------------------------------------------------------- garis
  // true = garis hitam di lantai putih (default), false = garis putih di lantai hitam.
  void setLineColor(bool blackOnWhite);
  bool lineIsBlack() const { return blackLine_; }
  // Baca ulang ke-12 sensor dan hitung posisi. Fungsi di bawah memanggilnya sendiri kalau bacaan terakhir
  // lebih tua dari 0,5 ms, jadi biasanya tidak perlu dipanggil manual.
  void readSensors();
  // Nilai sensor ternormalisasi 0-1000 (1000 = tepat di atas garis). n = 1..12 (S1 paling kiri).
  uint16_t sensorValue(uint8_t n);
  // Array 12 nilai ternormalisasi dari bacaan terakhir (tanpa membaca ulang).
  const uint16_t* sensorValues() const { return val_; }
  // Bit i = 1 kalau sensor S(i+1) melihat garis (nilai >= 500).
  uint16_t sensorPattern();
  // Posisi garis -1000..1000: 0 = tengah, + = garis di kanan robot, -1000/1000 = di bawah S1/S12.
  // Rata-rata berbobot memakai koordinat x busur sensor (rev B). Garis hilang -> nilai ujung sisi terakhir.
  int position();
  bool lineDetected();
  // Jumlah sensor yang melihat garis.
  uint8_t sensorsOnLine();

  // ---------------------------------------------------------------- persimpangan
  // Cabang kiri / kanan: sensor lengan (S1-S3 / S10-S12, |x| >= 28 mm) melihat garis. Di garis lurus garis 2 cm
  // tidak sampai ke sensor ini kecuali robot melenceng > ±16 mm.
  bool branchLeft();
  bool branchRight();
  // Ada persimpangan: cabang kiri atau kanan terlihat (simpang T, simpang 4, ujung garis melintang).
  bool junction();

  // ---------------------------------------------------------------- motor
  // Kecepatan motor kiri dan kanan -255..255 (+ = maju, 0 = rem). Arah tiap motor bisa dibalik di RobotConfig.h.
  void motor(int left, int right);
  // Rem kedua motor (short brake TB6612).
  void stop();
  // Lepas kedua motor (STBY LOW, roda bebas). motor() berikutnya menyalakan lagi.
  void release();
  // Kompensasi tegangan (default nyala): PWM dikali 6,0 V / V_baterai supaya motor 6 V tidak kelebihan tegangan
  // dan kecepatan tidak berubah saat baterai turun. motor(255, 255) = setara 6 V di motor.
  void setVoltageCompensation(bool on) { voltageComp_ = on; }

  // ---------------------------------------------------------------- encoder
  // Hitungan encoder sejak begin()/resetEncoders() (+ = maju). 840 hitungan per putaran roda (RobotConfig.h).
  long encoderLeft();
  long encoderRight();
  void resetEncoders();
  // Jarak tempuh rata-rata kedua roda sejak reset (mm).
  float distanceMm();
  // Sudut putar robot sejak reset (derajat, + = berlawanan jarum jam / ke kiri), dari selisih encoder.
  float headingDeg();

  // ---------------------------------------------------------------- PID ikut garis
  // Satu langkah PID ikut garis pada laju tetap 1 kHz; kalau dipanggil lebih cepat langsung return.
  // Panggil terus-menerus di loop() tanpa delay(). speed = PWM dasar 0..255.
  // kp per satuan posisi (posisi -1000..1000), kd per perubahan posisi tiap 1 ms.
  // Titik awal tuning (dari simulasi): follow(120, 0.07, 3.5).
  void follow(int speed, float kp, float kd);
  // Lupakan error sebelumnya (suku D mulai dari nol). follow() melakukannya sendiri sesudah jeda > 20 ms.
  void resetFollow() { followStarted_ = false; }
  // Koreksi PID terakhir (selisih PWM kiri-kanan / 2), untuk tampilan/log.
  int lastCorrection() const { return lastCorrection_; }

  // Kp/Kd yang dipakai rute dan gerak terukur di bawah (follow() tetap menerima kp/kd sendiri).
  void setPID(float kp, float kd) {
    kp_ = kp;
    kd_ = kd;
  }
  float routeKp() const { return kp_; }
  float routeKd() const { return kd_; }

  // ---------------------------------------------------------------- path planning per indeks
  // Tanpa menunggu (untuk program dengan menu): routeBegin() lalu panggil routeUpdate() terus di loop() sampai
  // hasilnya bukan ROUTE_RUNNING. steps harus tetap ada selama rute berjalan.
  void routeBegin(const LfStep* steps, uint8_t count);
  LfRouteState routeUpdate();
  void routeStop();  // hentikan rute + rem motor
  LfRouteState routeState() const { return routeState_; }
  uint8_t routeIndex() const { return routeIdx_ + 1; }  // indeks yang sedang dikerjakan (1 = pertama)
  uint8_t routeCount() const { return routeCount_; }
  const char* routeMessage() const { return routeMsg_; }  // keterangan selesai/gagal
  void setRouteBeep(bool on) { routeBeep_ = on; }        // bunyi pendek tiap aksi dimulai

  // Menunggu sampai selesai (untuk blok Mind+): kerjakan satu indeks. Panggil berurutan, indeks 1, 2, 3, ...
  // Antar panggilan robot tetap jalan (tidak berhenti). Tombol apa pun = batal: motor berhenti dan semua
  // runIndex() berikutnya langsung return false sampai routeReset().
  bool runIndex(uint8_t trigger, uint8_t action, int speed, int followMm, bool whiteLine = false);
  void routeReset();

  // ---------------------------------------------------------------- gerak terukur (menunggu sampai selesai)
  // Maju lurus sejauh mm (negatif = mundur) memakai encoder. Tombol apa pun = batal (return false).
  bool forwardMm(int speed, int mm);
  // Putar di tempat sejauh deg derajat (+ = kiri / berlawanan jarum jam), dari selisih encoder.
  bool turnDegrees(int speed, int deg);
  // Putar di tempat ke kiri/kanan sampai sensor tengah menemukan garis (minimal 60 derajat).
  bool turnToLine(bool left, int speed);

  // ---------------------------------------------------------------- rute terpendek (grid)
  // Rute terpendek di grid cols x rows simpul (simpul (x, y), x ke timur, y ke utara, maks 8 x 8). Robot
  // diletakkan tepat sesudah simpul start menghadap heading (0 timur, 1 utara, 2 barat, 3 selatan) dan wajib
  // berangkat ke arah itu. blocked = daftar simpul terlarang sebagai pasangan x, y (nBlocked pasangan).
  // Dari rute sama panjang dipilih yang beloknya paling sedikit. Hasil ditulis ke out sebagai indeks
  // (pemicu persimpangan, aksi lurus/kiri/kanan, terakhir berhenti). Return jumlah indeks, 0 = tidak ada rute.
  static uint8_t planGridRoute(uint8_t cols, uint8_t rows, uint8_t startX, uint8_t startY, uint8_t heading,
                               uint8_t goalX, uint8_t goalY, const uint8_t* blocked, uint8_t nBlocked,
                               LfStep* out, uint8_t maxSteps, uint8_t speed, uint16_t followMm);
  // Versi blok: simpul terhalang dikumpulkan dulu (maks 16), lalu runShortestRoute() membuat rute dan
  // menjalankannya indeks demi indeks dengan runIndex() (menunggu sampai berhenti di tujuan).
  void clearBlockedNodes() { nBlocked_ = 0; }
  void blockNode(uint8_t x, uint8_t y);
  bool runShortestRoute(uint8_t cols, uint8_t rows, uint8_t startX, uint8_t startY, uint8_t heading, uint8_t goalX,
                        uint8_t goalY, int speed, int followMm = 80);

  // ---------------------------------------------------------------- buzzer
  // Bunyikan buzzer selama ms milidetik. Tidak menunggu: buzzer dimatikan oleh timer.
  void beep(uint16_t ms);

  // ---------------------------------------------------------------- tombol (5 tombol tangga resistor, GPIO34)
  // Tombol yang sedang ditekan saat ini (LfButton, BTN_NONE = tidak ada), tanpa debounce.
  uint8_t readButton();
  // true selama tombol id (1..5, lihat LfButton) ditekan, sesudah stabil 20 ms.
  bool buttonPressed(uint8_t id);
  // Tombol yang baru saja ditekan (sekali per tekanan), BTN_NONE kalau tidak ada. Panggil berulang-ulang.
  uint8_t buttonClicked();

  // ---------------------------------------------------------------- baterai
  // Tegangan baterai (V), dirata-rata. 0 kalau baterai tidak terpasang (mis. hanya USB).
  float batteryVoltage();
  uint16_t batteryMillivolts();
  // true kalau baterai terpasang dan di bawah 6,8 V (3,4 V per sel): segera cas.
  bool batteryLow();

 private:
  void driveRaw(int left, int right);
  void refreshSensors();
  void updateButtons();
  void updateBattery(bool force = false);

  // path planning (LfRoute.cpp)
  enum Phase : uint8_t { PH_WATCH, PH_CHECK, PH_SKIP, PH_CROSS, PH_APPROACH, PH_TURN, PH_POST };
  void routeStart(const LfStep* steps, uint8_t count, bool chain);
  void phaseBegin(Phase p);
  void beginAction();
  void startPost();
  void finishStep();
  void routeFail(const char* msg);
  void straight();
  float phaseMm();
  float phaseDeg();
  bool reached(float targetMm, int pwm);
  void checkEncoderAlive();
  bool waitAbort();
  void syncButtons();
  void armChainWatchdog();
  void disarmChainWatchdog();

  float kp_ = 0.07f, kd_ = 3.5f;
  const LfStep* steps_ = nullptr;
  uint8_t routeCount_ = 0, routeIdx_ = 0;
  LfRouteState routeState_ = ROUTE_IDLE;
  Phase phase_ = PH_WATCH;
  const char* routeMsg_ = "";
  bool routeBeep_ = false;
  bool chain_ = false;       // mode runIndex(): akhir langkah tidak mengerem
  bool chainFresh_ = true;   // runIndex() pertama sesudah routeReset()
  bool aborted_ = false;
  int curSpeed_ = 120;
  int32_t phEncL_ = 0, phEncR_ = 0;  // encoder saat fase mulai
  uint32_t phMs_ = 0, routeTickUs_ = 0;
  float ignoreMm_ = 0, toCenterMm_ = 0;
  uint32_t lostSinceMs_ = 0;
  bool endPending_ = false;
  bool brL_ = false, brR_ = false;
  bool encDead_ = false;
  LfStep single_ = {};
  volatile bool chainWdArmed_ = false;
  uint8_t blocked_[32] = {};  // pasangan x, y simpul terhalang
  uint8_t nBlocked_ = 0;

  // tombol
  uint8_t btnRaw_ = BTN_NONE;
  uint8_t btnStable_ = BTN_NONE;
  uint8_t btnClickPending_ = BTN_NONE;
  uint32_t btnChangedMs_ = 0;

  // baterai & motor
  bool voltageComp_ = true;
  uint16_t vbatMv_ = 0;
  uint32_t vbatReadMs_ = 0;
  bool vbatHave_ = false;

  // PID
  bool followStarted_ = false;
  uint32_t lastFollowUs_ = 0;
  int prevError_ = 0;
  int lastCorrection_ = 0;

  // sensor & kalibrasi
  uint16_t raw_[SENSOR_COUNT] = {};
  uint16_t val_[SENSOR_COUNT] = {};
  uint16_t calMin_[SENSOR_COUNT];
  uint16_t calMax_[SENSOR_COUNT];
  uint16_t workMin_[SENSOR_COUNT];
  uint16_t workMax_[SENSOR_COUNT];
  uint16_t calBadMask_ = 0;
  bool calibrated_ = false;
  bool blackLine_ = true;
  bool haveRead_ = false;
  uint32_t lastReadUs_ = 0;
  uint16_t pattern_ = 0;
  int position_ = 0;
  int lastSeenPos_ = 0;
  bool lineSeen_ = false;

  bool motorsEnabled_ = false;
  int lastLeft_ = 0, lastRight_ = 0;
};
