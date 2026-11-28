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
