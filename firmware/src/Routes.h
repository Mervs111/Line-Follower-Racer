// Routes.h — daftar rute (path planning per indeks) yang bisa dipilih dari menu atau perintah serial.
// Tambah / ubah rute untuk arena di Routes.cpp.
#pragma once

#include <LineFollower.h>

struct RouteDef {
  const char* name;
  const LfStep* steps;  // nullptr = dibuat saat dijalankan (rute terpendek grid)
  uint8_t count;
};

extern const RouteDef ROUTES[];
extern const uint8_t ROUTE_COUNT;

constexpr uint8_t MAX_STEPS = 64;

// Siapkan langkah rute ke buffer: speed 0 di tabel diganti kecepatan menu. Return jumlah langkah (0 = gagal).
uint8_t buildRoute(uint8_t routeNo, uint8_t speedPwm, LfStep* out, uint8_t maxSteps);
