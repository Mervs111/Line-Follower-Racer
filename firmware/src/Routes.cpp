// Routes.cpp — tabel rute. Tiap baris = satu indeks: {pemicu, aksi, kecepatan, ikuti_mm, garis_putih}.
//   pemicu: TRIG_JUNCTION (persimpangan apa saja), TRIG_LEFT, TRIG_RIGHT, TRIG_BOTH, TRIG_END (ujung garis),
//           TRIG_DIRECT (langsung)
//   aksi:   ACT_FORWARD, ACT_LEFT, ACT_RIGHT, ACT_UTURN, ACT_STOP
//   kecepatan 0 = pakai kecepatan dari menu "Atur PID"
// Rute untuk arena IARC dibuat sesudah ukuran arena asli diketahui (jarak antar simpang belum tertulis di guidebook).
#include "Routes.h"

// Uji pertama: ikuti garis sampai persimpangan pertama, berhenti dengan poros di tengahnya.
static const LfStep R_TEST[] = {
    {TRIG_JUNCTION, ACT_STOP, 0, 0, false},
};

// Rute slide 8 deck pitching (sama dengan SLIDE_PLAN di simulasi/lfm_control.py, lulus di CoppeliaSim).
static const LfStep R_SLIDE[] = {
    {TRIG_LEFT, ACT_LEFT, 0, 80, false},      {TRIG_JUNCTION, ACT_RIGHT, 0, 80, false},
    {TRIG_JUNCTION, ACT_LEFT, 0, 80, false},  {TRIG_JUNCTION, ACT_RIGHT, 0, 80, false},
    {TRIG_JUNCTION, ACT_LEFT, 0, 80, false},  {TRIG_JUNCTION, ACT_STOP, 0, 80, false},
};

// Keliling kotak: belok kiri di 4 persimpangan berikutnya lalu berhenti di persimpangan sesudahnya.
static const LfStep R_SQUARE[] = {
    {TRIG_JUNCTION, ACT_LEFT, 0, 80, false}, {TRIG_JUNCTION, ACT_LEFT, 0, 80, false},
    {TRIG_JUNCTION, ACT_LEFT, 0, 80, false}, {TRIG_JUNCTION, ACT_LEFT, 0, 80, false},
    {TRIG_JUNCTION, ACT_STOP, 0, 80, false},
};

// Sampai ujung garis, putar balik, kembali sampai persimpangan, berhenti.
static const LfStep R_END_BACK[] = {
    {TRIG_END, ACT_UTURN, 0, 100, false},
    {TRIG_JUNCTION, ACT_STOP, 0, 0, false},
};

const RouteDef ROUTES[] = {
    {"Uji simpang", R_TEST, sizeof(R_TEST) / sizeof(R_TEST[0])},
    {"Slide 8", R_SLIDE, sizeof(R_SLIDE) / sizeof(R_SLIDE[0])},
    {"Kotak kiri", R_SQUARE, sizeof(R_SQUARE) / sizeof(R_SQUARE[0])},
    {"Ujung balik", R_END_BACK, sizeof(R_END_BACK) / sizeof(R_END_BACK[0])},
    {"Terpendek 4x4", nullptr, 0},
};
const uint8_t ROUTE_COUNT = sizeof(ROUTES) / sizeof(ROUTES[0]);

// Rute terpendek: grid 4 x 4, start (0,0) menghadap utara, tujuan (3,3), simpul (1,0) (2,2) (1,2) terhalang
// (contoh "BFS dengan halangan" simulasi, lulus di CoppeliaSim 26/10). Hasil: lurus, lurus, kanan, lurus, lurus,
// berhenti (lewat tepi kiri lalu atas).
static const uint8_t BFS_BLOCKED[] = {1, 0, 2, 2, 1, 2};

uint8_t buildRoute(uint8_t routeNo, uint8_t speedPwm, LfStep* out, uint8_t maxSteps) {
  if (routeNo >= ROUTE_COUNT) return 0;
  const RouteDef& r = ROUTES[routeNo];
  if (r.steps == nullptr) {
    return LineFollower::planGridRoute(4, 4, 0, 0, 1, 3, 3, BFS_BLOCKED, sizeof(BFS_BLOCKED) / 2, out, maxSteps,
                                       speedPwm, 80);
  }
  if (r.count > maxSteps) return 0;
  for (uint8_t i = 0; i < r.count; i++) {
    out[i] = r.steps[i];
    if (out[i].speed == 0) out[i].speed = speedPwm;
  }
  return r.count;
}
