// RobotConfig.h — konstanta mekanik, arah, dan ambang robot LFM X1.
// Nilai bertanda (UKUR) masih dari rancangan/perkiraan: cek di robot jadi lalu ubah di sini saja.
#pragma once

#include <stdint.h>

namespace Config {

// ---------------------------------------------------------------- mekanik
constexpr float WHEEL_DIAMETER_MM = 34.0f;  // velg cetak + ban TPU (UKUR sesudah ban dipasang)
constexpr float WHEEL_TRACK_MM = 97.0f;     // jarak tengah ban kiri-kanan, konsep v18 (UKUR)
constexpr uint16_t ENCODER_PPR = 7;         // pulsa per putaran poros motor (asumsi, tanya penjual / UKUR)
constexpr uint16_t GEAR_RATIO = 30;         // N20 500 RPM, listing MTR-0239
constexpr uint32_t ENCODER_CPR = (uint32_t)ENCODER_PPR * GEAR_RATIO * 4;  // hitungan per putaran roda (x4) = 840
constexpr float MM_PER_COUNT = 3.14159265f * WHEEL_DIAMETER_MM / ENCODER_CPR;
constexpr float MOTOR_MAX_MM_S = 890.0f;    // 500 RPM di roda O34 tanpa beban; dipakai untuk batas waktu cadangan

// ---------------------------------------------------------------- arah (cek dengan perintah serial)
// "m 100 100" harus membuat kedua roda maju; kalau ada yang mundur, balik flag motornya.
constexpr bool MOTOR_L_INVERT = false;
constexpr bool MOTOR_R_INVERT = false;
// Sesudah motor benar, "enc" saat maju harus naik di kedua roda; kalau turun, balik flag encodernya.
constexpr bool ENC_L_INVERT = false;
constexpr bool ENC_R_INVERT = true;         // motor kanan terpasang cermin terhadap kiri (UKUR)
// "raw" sambil menggeser garis dari kiri ke kanan: S1 harus bereaksi duluan. Kalau terbalik, set true.
constexpr bool SENSOR_REVERSED = false;

// ---------------------------------------------------------------- sensor (PCB sensor rev B/C)
constexpr uint8_t SENSOR_COUNT = 12;
// x tiap sensor dari garis tengah robot (0,01 mm, + = kanan), S1..S12 kiri -> kanan.
constexpr int16_t SENSOR_X_CMM[SENSOR_COUNT] = {-4139, -3526, -2801, -2019, -1222, -425,
                                                425,   1222,  2019,  2801,  3526,  4139};
// y tiap sensor di depan poros roda (mm), dari koordinat KiCad PCB sensor (Y = 180,55 - y robot).
constexpr float SENSOR_Y_MM[SENSOR_COUNT] = {114.72f, 119.86f, 123.24f, 124.91f, 125.60f, 126.30f,
                                             126.30f, 125.60f, 124.91f, 123.24f, 119.86f, 114.72f};
constexpr float LINE_WIDTH_MM = 20.0f;      // garis hitam 2 cm (guidebook IARC XII)

constexpr uint8_t MUX_SETTLE_US = 4;        // jeda sesudah ganti kanal mux sebelum ADC dibaca
constexpr uint16_t SENSOR_CACHE_US = 500;   // bacaan sensor dipakai ulang kalau umurnya di bawah ini
constexpr uint16_t LINE_THRESHOLD = 500;    // nilai ternormalisasi (0-1000) yang dianggap "lihat garis"
constexpr uint16_t NOISE_FLOOR = 150;       // nilai di bawah ini tidak ikut rata-rata posisi
constexpr uint16_t LOST_SUM = 300;          // jumlah nilai di atas NOISE_FLOOR di bawah ini = garis hilang
constexpr uint16_t MIN_CAL_RANGE = 100;     // selisih max-min mentah minimal supaya sensor dianggap terkalibrasi
constexpr uint8_t CAL_SPIN_PWM = 70;        // kecepatan ayun saat kalibrasi otomatis
constexpr uint16_t CAL_SWING_MS = 150;      // lama tiap seperempat ayunan (kanan, kiri, kiri, kanan) (UKUR)

// ---------------------------------------------------------------- motor
constexpr uint32_t PWM_FREQ_HZ = 20000;     // aturan firmware: 20 kHz, 8 bit
constexpr uint8_t PWM_BITS = 8;
constexpr uint16_t MOTOR_NOMINAL_MV = 6000; // motor N20 6 V: PWM dikompensasi 6,0 V / V_baterai
constexpr uint16_t COMP_MIN_VBAT_MV = 5000; // di bawah ini (mis. hanya USB) kompensasi dimatikan

// ---------------------------------------------------------------- kendali
constexpr uint16_t FOLLOW_HZ = 1000;        // laju PID follow()

// ---------------------------------------------------------------- baterai (Li-ion 2S)
constexpr float VBAT_DIVIDER = 133.0f / 33.0f;  // 100k / 33k
constexpr uint16_t VBAT_LOW_MV = 6800;          // 3,4 V per sel: peringatan
constexpr uint16_t VBAT_FULL_MV = 8400;
constexpr uint16_t VBAT_EMPTY_MV = 6400;
constexpr uint16_t VBAT_PRESENT_MV = 4000;      // di bawah ini dianggap baterai tidak terpasang
constexpr float VBAT_TRIM = 1.0f;               // koreksi pembacaan ADC (UKUR: V multimeter / V terbaca)

// ---------------------------------------------------------------- tombol (tegangan BTN, pull-up 10k)
// ATAS 1k = 0,30 V, BAWAH 3k9 = 0,93 V, KEMBALI 8k2 = 1,49 V, OK 18k = 2,12 V, LANJUT 39k = 2,63 V, lepas 3,3 V.
// Batas = titik tengah antar tegangan.
constexpr uint16_t BTN_EDGE_UP_MV = 615;
constexpr uint16_t BTN_EDGE_DOWN_MV = 1210;
constexpr uint16_t BTN_EDGE_BACK_MV = 1805;
constexpr uint16_t BTN_EDGE_OK_MV = 2375;
constexpr uint16_t BTN_EDGE_NEXT_MV = 2965;
constexpr uint16_t BTN_DEBOUNCE_MS = 20;

}  // namespace Config
