// LineFollower.h — library utama robot line follower ESP32-S3.
// Fungsi di sini akan dipanggil langsung oleh blok Mind+ (1 blok = 1 fungsi).
#pragma once

#include <Arduino.h>

#include "Pins.h"

class LineFollower {
 public:
  // Inisialisasi semua pin. Panggil sekali di setup().
  void begin();

  // Nyalakan LED WS2812 dengan warna R, G, B (0–255). led(0, 0, 0) = mati.
  void led(uint8_t r, uint8_t g, uint8_t b);
};
