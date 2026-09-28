#include "LineFollower.h"

#include <esp_arduino_version.h>

void LineFollower::begin() {
  led(0, 0, 0);
}

void LineFollower::led(uint8_t r, uint8_t g, uint8_t b) {
  // Core 3.x mengganti nama neopixelWrite() jadi rgbLedWrite().
  // Pakai fungsi bawaan core supaya tidak butuh library tambahan.
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  rgbLedWrite(Pins::WS2812, r, g, b);
#else
  neopixelWrite(Pins::WS2812, r, g, b);
#endif
}
