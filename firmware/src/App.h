// App.h — keadaan bersama program robot (menu OLED + perintah serial).
#pragma once

#include <Arduino.h>
#include <LineFollower.h>

extern LineFollower robot;

// Pengaturan yang disimpan di NVS (namespace "lfm_app")
struct Settings {
  uint8_t route = 0;       // rute terpilih (0..ROUTE_COUNT-1)
  int16_t kp1000 = 70;     // Kp x 1000 (0,070)
  int16_t kd10 = 35;       // Kd x 10 (3,5)
  int16_t speedPwm = 120;  // kecepatan dasar ikut garis (PWM 0..255, setara 6 V = 255)
  bool blackLine = true;   // garis hitam di lantai putih
};
extern Settings cfg;

float cfgKp();
float cfgKd();
int cfgSpeedPwm();
void saveSettings();
void applySettings();  // warna garis + PID ke library

// Mode kerja. Hanya satu yang jalan; loop() memanggil langkahnya terus tanpa delay().
enum AppMode : uint8_t { MODE_IDLE, MODE_FOLLOW, MODE_ROUTE, MODE_CALIB, MODE_MOTOR };
extern AppMode mode;

// Mulai / hentikan. Semua mengembalikan false kalau tidak bisa dimulai (alasannya di Serial).
bool startRoute(uint8_t routeNo);  // 0-based
bool startFollow();
void startCalibration(bool spin);
void finishCalibration();
void startMotorTest(int left, int right, uint32_t ms);
void stopAll(const char* why);

// Info rute terakhir untuk layar hasil
extern uint32_t runStartMs, runTimeMs;
extern uint8_t runIndexReached;
extern const char* runMessage;
extern bool calSpin;
extern uint32_t calStartMs;
extern uint16_t calDurationMs;

// Modul
void consoleBegin();
void consolePoll();
void uiBegin();
void uiUpdate();         // tombol + gambar layar (tidak menggambar saat robot berjalan)
void uiRouteFinished();  // dipanggil saat rute selesai / gagal / dihentikan
