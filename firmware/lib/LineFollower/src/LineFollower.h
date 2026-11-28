// LineFollower.h — library utama robot line follower LFM X1 (ESP32 DevKit, 12 sensor QRE1113 + mux, TB6612FNG).
// Fungsi di sini dipanggil langsung oleh blok Mind+ (1 blok = 1 fungsi), jadi namanya dijaga tetap.
// Aturan: tanpa delay() dan String di jalur kendali; kompatibel Arduino-ESP32 core 2.x dan 3.x.
#pragma once

#include <Arduino.h>

#include "Pins.h"
#include "RobotConfig.h"

// Core 3.x mengganti API LEDC dan PCNT; core 1.x belum punya makro versi.
#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
#define LF_CORE3 1
#else
#define LF_CORE3 0
#endif

#define LF_VERSION "0.1.0"

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

  // ---------------------------------------------------------------- motor
  // Kecepatan motor kiri dan kanan -255..255 (+ = maju, 0 = rem). Arah tiap motor bisa dibalik di RobotConfig.h.
  void motor(int left, int right);
  // Rem kedua motor (short brake TB6612).
  void stop();
  // Lepas kedua motor (STBY LOW, roda bebas). motor() berikutnya menyalakan lagi.
  void release();

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

 private:
  void driveRaw(int left, int right);
  void refreshSensors();

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
