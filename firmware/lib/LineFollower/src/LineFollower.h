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

  // Inisialisasi semua pin. Panggil sekali di setup(). Motor tetap mati (STBY LOW) sampai motor() dipanggil.
  void begin();

  // ---------------------------------------------------------------- sensor mentah
  // Baca 12 sensor lewat mux ke out[0..11] (S1 paling kiri .. S12 paling kanan), nilai ADC 0-4095.
  // QRE1113 dengan pull-up: makin gelap permukaan, makin besar nilainya.
  void readRaw(uint16_t out[]);

  // ---------------------------------------------------------------- motor
  // Kecepatan motor kiri dan kanan -255..255 (+ = maju, 0 = rem). Arah tiap motor bisa dibalik di RobotConfig.h.
  void motor(int left, int right);
  // Rem kedua motor (short brake TB6612).
  void stop();
  // Lepas kedua motor (STBY LOW, roda bebas). motor() berikutnya menyalakan lagi.
  void release();

  // ---------------------------------------------------------------- buzzer
  // Bunyikan buzzer selama ms milidetik. Tidak menunggu: buzzer dimatikan oleh timer.
  void beep(uint16_t ms);

 private:
  void driveRaw(int left, int right);

  bool motorsEnabled_ = false;
  int lastLeft_ = 0, lastRight_ = 0;
};
