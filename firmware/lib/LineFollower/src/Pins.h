// Pins.h — satu-satunya sumber kebenaran untuk pin map robot.
// Jangan tulis nomor GPIO di file lain; selalu pakai konstanta di sini.
#pragma once

#include <stdint.h>

namespace Pins {

// Sensor garis S1–S8 (semua di ADC1, aman dipakai bareng WiFi)
constexpr uint8_t SENSOR_COUNT = 8;
constexpr uint8_t SENSOR[SENSOR_COUNT] = {1, 2, 3, 4, 5, 6, 7, 8};

// Enable emitter IR (via MOSFET)
constexpr uint8_t IR_EMITTER = 9;

// Pembagi tegangan baterai 100k / 33k
constexpr uint8_t BATTERY = 10;

// TB6612FNG — motor kiri (A) dan kanan (B)
constexpr uint8_t MOTOR_PWMA = 11;
constexpr uint8_t MOTOR_AIN1 = 12;
constexpr uint8_t MOTOR_AIN2 = 13;
constexpr uint8_t MOTOR_PWMB = 14;
constexpr uint8_t MOTOR_BIN1 = 15;
constexpr uint8_t MOTOR_BIN2 = 16;
constexpr uint8_t MOTOR_STBY = 17;

// Tombol (aktif LOW)
constexpr uint8_t BUTTON_A = 0;   // tombol BOOT
constexpr uint8_t BUTTON_B = 18;

// UI
constexpr uint8_t BUZZER = 21;
constexpr uint8_t WS2812 = 48;

// Header I2C (OLED)
constexpr uint8_t I2C_SDA = 40;
constexpr uint8_t I2C_SCL = 41;

// Encoder (opsional)
constexpr uint8_t ENC_L_A = 38;
constexpr uint8_t ENC_L_B = 39;
constexpr uint8_t ENC_R_A = 42;
constexpr uint8_t ENC_R_B = 47;

}  // namespace Pins
