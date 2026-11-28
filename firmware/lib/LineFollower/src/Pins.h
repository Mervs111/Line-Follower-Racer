// Pins.h — satu-satunya sumber kebenaran pin map robot LFM X1 (ESP32 DevKit 30 pin).
// Sumber: tabel pin CLAUDE.md / docs/skematik-v1.md / skematik PCB utama rev B (hardware/tools/gen_sch_utama.py).
// Jangan tulis nomor GPIO di file lain; selalu pakai konstanta di sini.
#pragma once

#include <stdint.h>

namespace Pins {

// ---- Sensor garis: 12 QRE1113GR lewat mux CD74HC4067 di PCB sensor (kabel JST XH 8 pin)
// S1..S12 (kiri -> kanan) = kanal I2..I13; I0, I1, I14, I15 tidak tersambung.
constexpr uint8_t MUX_SIG = 36;            // ADC1_CH0 (SENSOR_VP)
constexpr uint8_t MUX_S0 = 26;
constexpr uint8_t MUX_S1 = 25;
constexpr uint8_t MUX_S2 = 33;
constexpr uint8_t MUX_S3 = 32;
constexpr uint8_t MUX_FIRST_CHANNEL = 2;   // S1 = I2

// ---- Baterai: pembagi 100k / 33k + C 100 nF
constexpr uint8_t VBAT_SENSE = 39;         // ADC1_CH3 (SENSOR_VN)

// ---- TB6612FNG: kanal A = motor kiri (J2), kanal B = motor kanan (J3)
constexpr uint8_t MOTOR_PWMA = 18;
constexpr uint8_t MOTOR_AIN1 = 5;
constexpr uint8_t MOTOR_AIN2 = 17;
constexpr uint8_t MOTOR_PWMB = 16;
constexpr uint8_t MOTOR_BIN1 = 4;
constexpr uint8_t MOTOR_BIN2 = 15;
constexpr uint8_t MOTOR_STBY = 2;          // LOW saat boot (GPIO2 strapping)

// ---- Encoder motor N20 (dibaca PCNT)
constexpr uint8_t ENC_L_A = 13;
constexpr uint8_t ENC_L_B = 14;
constexpr uint8_t ENC_R_A = 23;
constexpr uint8_t ENC_R_B = 19;

// ---- Board interface (J6): 5 tombol tangga resistor + pin cadangan
constexpr uint8_t BUTTONS = 34;            // ADC1_CH6, pull-up 10k (R5) di PCB utama
constexpr uint8_t AUX = 35;                // cadangan, belum dipakai

// ---- Buzzer aktif lewat S8050 (R4 pull-down, LOW saat boot; GPIO12 strapping)
constexpr uint8_t BUZZER = 12;

// ---- I2C (hanya OLED SSD1306 0,96")
constexpr uint8_t I2C_SDA = 21;
constexpr uint8_t I2C_SCL = 22;

// ---- Tidak dipakai lagi (LED IR selalu nyala)
constexpr uint8_t IR_EN = 27;

}  // namespace Pins
