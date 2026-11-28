// robot-lfm.chip.c — tiruan robot LFM X1 untuk menjalankan firmware ASLI di wokwi.com.
//
// Wokwi tidak punya mux CD74HC4067, sensor QRE1113, motor N20 + encoder, dan simulasi analognya tidak bisa
// menghitung tangga resistor. Chip ini menggantikan semuanya, dengan pin yang sama seperti robot asli:
//   - tombol: 5 pushbutton masuk ke chip, chip mengeluarkan tegangan tangga resistor ke GPIO34
//   - baterai: tegangan pembagi 100k/33k ke GPIO39 (slider "Baterai")
//   - motor: chip membaca STBY, AIN1/AIN2/BIN1/BIN2 dan memperkirakan duty PWMA/PWMB, lalu menggerakkan robot
//     tiruan di arena grid (garis hitam 2 cm)
//   - encoder: pulsa kuadratur ke GPIO13/14 (kiri) dan 23/19 (kanan), dibaca PCNT seperti di robot asli
//   - sensor: 12 sensor di koordinat busur PCB sensor rev B, tegangan kanal mux yang dipilih S0..S3 ke GPIO36
//   - layar chip: arena, robot, dan sensor yang melihat garis (merah)
// Angka-angka disalin dari firmware/lib/LineFollower/src/RobotConfig.h; ubah di sana dulu kalau robot berubah.

#include "wokwi-api.h"

#include <math.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#define N_SENSOR 12
#define N_BTN 5

// koordinat sensor dari garis tengah robot (mm, + = kanan) dan jarak di depan poros roda (mm)
static const float SENSOR_X[N_SENSOR] = {-41.39f, -35.26f, -28.01f, -20.19f, -12.22f, -4.25f,
                                         4.25f,   12.22f,  20.19f,  28.01f,  35.26f,  41.39f};
static const float SENSOR_Y[N_SENSOR] = {114.72f, 119.86f, 123.24f, 124.91f, 125.60f, 126.30f,
                                         126.30f, 125.60f, 124.91f, 123.24f, 119.86f, 114.72f};
// kepekaan tiap sensor sengaja sedikit beda (seperti sensor asli), supaya kalibrasi ada gunanya
static const float SENSOR_GAIN[N_SENSOR] = {0.92f, 1.05f, 0.97f, 1.08f, 0.95f, 1.02f,
                                            0.99f, 1.06f, 0.94f, 1.03f, 0.96f, 1.07f};

// tegangan tangga resistor (V), urutan pin KEMBALI, ATAS, OK, BAWAH, LANJUT (RobotConfig.h)
static const char *const BTN_NAMES[N_BTN] = {"KEMBALI", "ATAS", "OK", "BAWAH", "LANJUT"};
static const float BTN_V[N_BTN] = {1.49f, 0.30f, 2.12f, 0.93f, 2.63f};
#define BTN_RELEASED_V 3.30f

#define TICK_US 103          // 103 us: fase sampel PWM 20 kHz (periode 50 us) bergeser 3 us tiap tick
#define PHYS_EVERY 10        // fisika + sensor tiap 10 tick (+-1 ms)
#define DRAW_EVERY 970       // layar chip tiap +-100 ms
#define PWM_ALPHA 0.02f      // perata perkiraan duty PWM
#define MM_PER_COUNT (3.14159265f * 34.0f / 840.0f)  // roda O34, 840 hitungan per putaran roda
#define TRACK_MM 97.0f
#define MOTOR_MAX_MM_S 890.0f  // 500 RPM, roda O34, 6 V tanpa beban
#define MOTOR_NOMINAL_V 6.0f
#define LOAD_FACTOR 0.8f       // beban robot: kecepatan 80 % kecepatan tanpa beban
#define MOTOR_MIN_VBAT 4.0f    // di bawah ini (hanya USB) motor tidak bertenaga
#define TAU_DRIVE_S 0.03f
#define TAU_COAST_S 0.10f
#define V_FLOOR 0.35f          // tegangan sensor di lantai putih
#define V_LINE 2.60f           // tegangan sensor di garis hitam
#define LINE_HALF_MM 10.0f     // garis 2 cm
#define SPOT_MM 3.0f           // jari-jari bidang baca sensor
#define START_AHEAD_MM 20.0f   // poros 2 cm di depan simpul start (sama dengan simulasi CoppeliaSim)
#define VBAT_DIVIDER (133.0f / 33.0f)
#define PI_F 3.14159265f

typedef struct {
  pin_t btn[N_BTN], btn_out, vbat, sel[4], sig;
  pin_t stby, in1[2], in2[2], pwm[2];
  pin_t enc_a[2], enc_b[2];
  uint32_t a_battery, a_shift, a_grid, a_spacing, a_sx, a_sy, a_sh, a_reset, a_scale;
  float watch[6];        // nilai terakhir atribut yang membuat robot ditaruh ulang di start
  float duty[2];         // perkiraan duty PWM kiri/kanan (0..1)
  float speed[2];        // kecepatan roda kiri/kanan (mm/s)
  float x, y, th;        // pose poros roda (mm); th = 0 menghadap timur, + berlawanan jarum jam
  double count_target[2];
  int32_t count_out[2];
  uint8_t quad[2];
  float cover[N_SENSOR]; // seberapa tertutup garis tiap sensor (0..1)
  float volt[N_SENSOR];  // tegangan tiap sensor sebelum diskalakan ke ADC Wokwi
  uint32_t tick;
  uint32_t rng;
  buffer_t fb;
  uint32_t fb_w, fb_h;
  uint8_t *pix;
} chip_t;

// ------------------------------------------------------------------ bantu
static float clampf(float v, float lo, float hi) { return v < lo ? lo : (v > hi ? hi : v); }

static float rand01(chip_t *c) {
  c->rng = c->rng * 1664525u + 1013904223u;
  return (float)(c->rng >> 8) / 16777216.0f;
}

// Wokwi: ADC virtual memakai acuan 5 V untuk semua MCU. Tegangan robot asli (3,3 V) diskalakan ke situ.
static float adc_scale(chip_t *c) { return attr_read_float(c->a_scale) / 3.3f; }

static int grid_n(chip_t *c) { return (int)clampf(roundf(attr_read_float(c->a_grid)), 2.0f, 8.0f); }
static float spacing(chip_t *c) { return clampf(attr_read_float(c->a_spacing), 50.0f, 2000.0f); }

// ------------------------------------------------------------------ keluaran analog
static void write_buttons(chip_t *c) {
  float v = BTN_RELEASED_V;
  for (int i = 0; i < N_BTN; i++) {
    if (pin_read(c->btn[i]) == LOW && BTN_V[i] < v) v = BTN_V[i];  // tombol beresistor terkecil menang
  }
  pin_dac_write(c->btn_out, v * adc_scale(c));
}

static void write_battery(chip_t *c) {
  float b = clampf(attr_read_float(c->a_battery), 0.0f, 9.0f);
  pin_dac_write(c->vbat, b / VBAT_DIVIDER * adc_scale(c));
}

static void write_sig(chip_t *c) {
  int ch = 0;
  for (int k = 0; k < 4; k++) {
    if (pin_read(c->sel[k]) == HIGH) ch |= 1 << k;
  }
  int idx = ch - 2;  // S1..S12 = kanal I2..I13; kanal lain tidak tersambung
  float v = (idx >= 0 && idx < N_SENSOR) ? c->volt[idx] : 0.0f;
  pin_dac_write(c->sig, v * adc_scale(c));
}

static void on_button(void *user_data, pin_t pin, uint32_t value) {
  (void)pin;
  (void)value;
  write_buttons((chip_t *)user_data);
}

static void on_select(void *user_data, pin_t pin, uint32_t value) {
  (void)pin;
  (void)value;
  write_sig((chip_t *)user_data);
}

// ------------------------------------------------------------------ arena + robot
static void reset_pose(chip_t *c) {
  int n = grid_n(c);
  float d = spacing(c);
  int sx = (int)clampf(roundf(attr_read_float(c->a_sx)), 0.0f, (float)(n - 1));
  int sy = (int)clampf(roundf(attr_read_float(c->a_sy)), 0.0f, (float)(n - 1));
  int h = (int)clampf(roundf(attr_read_float(c->a_sh)), 0.0f, 3.0f);
  c->th = (float)h * PI_F * 0.5f;
  c->x = (float)sx * d + cosf(c->th) * START_AHEAD_MM;
  c->y = (float)sy * d + sinf(c->th) * START_AHEAD_MM;
  c->speed[0] = c->speed[1] = 0.0f;
}

static void check_reset(chip_t *c) {
  const uint32_t ids[6] = {c->a_grid, c->a_spacing, c->a_sx, c->a_sy, c->a_sh, c->a_reset};
  bool changed = false;
  for (int i = 0; i < 6; i++) {
    float v = attr_read_float(ids[i]);
    if (v != c->watch[i]) {
      c->watch[i] = v;
      changed = true;
    }
  }
  if (changed) reset_pose(c);
}

// jarak titik (px, py) ke garis terdekat di grid n x n simpul berjarak d (garis berujung di simpul tepi)
static float grid_dist(chip_t *c, float px, float py) {
  int n = grid_n(c);
  float d = spacing(c);
  float len = (float)(n - 1) * d;
  float i = clampf(roundf(px / d), 0.0f, (float)(n - 1));
  float dx = px - i * d;
  float dy = py < 0.0f ? -py : (py > len ? py - len : 0.0f);
  float dv = sqrtf(dx * dx + dy * dy);
  float j = clampf(roundf(py / d), 0.0f, (float)(n - 1));
  float dy2 = py - j * d;
  float dx2 = px < 0.0f ? -px : (px > len ? px - len : 0.0f);
  float dh = sqrtf(dx2 * dx2 + dy2 * dy2);
  return dv < dh ? dv : dh;
}

static void sensor_world(chip_t *c, int i, float shift, float *wx, float *wy) {
  float fx = cosf(c->th), fy = sinf(c->th);  // arah depan
  float rx = fy, ry = -fx;                   // arah kanan
  float lx = SENSOR_X[i] + shift, ly = SENSOR_Y[i];
  *wx = c->x + fx * ly + rx * lx;
  *wy = c->y + fy * ly + ry * lx;
}

static void update_sensors(chip_t *c) {
  float shift = attr_read_float(c->a_shift);
  for (int i = 0; i < N_SENSOR; i++) {
    float wx, wy;
    sensor_world(c, i, shift, &wx, &wy);
    float dist = grid_dist(c, wx, wy);
    float cov = clampf((LINE_HALF_MM + SPOT_MM - dist) / (2.0f * SPOT_MM), 0.0f, 1.0f);
    c->cover[i] = cov;
    float noise = (rand01(c) - 0.5f) * 0.02f;
    c->volt[i] = clampf(V_FLOOR + (V_LINE - V_FLOOR) * cov * SENSOR_GAIN[i] + noise, 0.0f, 3.3f);
  }
}

// kecepatan roda yang dituju dari pin TB6612 (IN1/IN2 = arah, H/H = rem, L/L = lepas)
static float wheel_target(chip_t *c, int w, float bat, bool *coast) {
  *coast = false;
  if (pin_read(c->stby) == LOW || bat < MOTOR_MIN_VBAT) {
    *coast = true;
    return 0.0f;
  }
  uint32_t a = pin_read(c->in1[w]), b = pin_read(c->in2[w]);
  float dir;
  if (a == HIGH && b == LOW) dir = 1.0f;
  else if (a == LOW && b == HIGH) dir = -1.0f;
  else {
    *coast = (a == LOW);  // L/L lepas, H/H rem
    return 0.0f;
  }
  return dir * c->duty[w] * (bat / MOTOR_NOMINAL_V) * MOTOR_MAX_MM_S * LOAD_FACTOR;
}

static void physics(chip_t *c, float dt) {
  float bat = attr_read_float(c->a_battery);
  for (int w = 0; w < 2; w++) {
    bool coast;
    float target = wheel_target(c, w, bat, &coast);
    float k = clampf(dt / (coast ? TAU_COAST_S : TAU_DRIVE_S), 0.0f, 1.0f);
    c->speed[w] += (target - c->speed[w]) * k;
    c->count_target[w] += (double)(c->speed[w] * dt / MM_PER_COUNT);
  }
  float v = 0.5f * (c->speed[0] + c->speed[1]);
  float om = (c->speed[1] - c->speed[0]) / TRACK_MM;
  c->th += om * dt;
  if (c->th > PI_F) c->th -= 2.0f * PI_F;
  if (c->th < -PI_F) c->th += 2.0f * PI_F;
  c->x += v * cosf(c->th) * dt;
  c->y += v * sinf(c->th) * dt;
}

// satu langkah kuadratur per roda per tick. Urutan naik (A mendahului B): 00 -> 10 -> 11 -> 01.
// Roda kanan terpasang cermin (ENC_R_INVERT = true): maju = hitungan mentah turun.
static void emit_encoders(chip_t *c) {
  for (int w = 0; w < 2; w++) {
    int32_t target = (int32_t)floor(c->count_target[w]);
    int step = target > c->count_out[w] ? 1 : (target < c->count_out[w] ? -1 : 0);
    if (step == 0) continue;
    c->count_out[w] += step;
    int q = (int)c->quad[w] + (w == 0 ? step : -step);
    c->quad[w] = (uint8_t)(q & 3);
    pin_write(c->enc_a[w], (c->quad[w] == 1 || c->quad[w] == 2) ? HIGH : LOW);
    pin_write(c->enc_b[w], (c->quad[w] == 2 || c->quad[w] == 3) ? HIGH : LOW);
  }
}

// ------------------------------------------------------------------ layar chip
static void put(chip_t *c, int x, int y, uint8_t r, uint8_t g, uint8_t b) {
  if (x < 0 || y < 0 || x >= (int)c->fb_w || y >= (int)c->fb_h) return;
  uint8_t *p = c->pix + ((uint32_t)y * c->fb_w + (uint32_t)x) * 4;
  p[0] = r;
  p[1] = g;
  p[2] = b;
  p[3] = 255;
}

static void fill_rect(chip_t *c, int x0, int y0, int x1, int y1, uint8_t r, uint8_t g, uint8_t b) {
  for (int y = y0; y <= y1; y++)
    for (int x = x0; x <= x1; x++) put(c, x, y, r, g, b);
}

static void fill_circle(chip_t *c, int cx, int cy, int rad, uint8_t r, uint8_t g, uint8_t b) {
  for (int y = -rad; y <= rad; y++)
    for (int x = -rad; x <= rad; x++)
      if (x * x + y * y <= rad * rad) put(c, cx + x, cy + y, r, g, b);
}

static void draw(chip_t *c) {
  if (c->pix == NULL) return;
  int n = grid_n(c);
  float d = spacing(c);
  float len = (float)(n - 1) * d;
  float margin = 0.6f * d;
  float s = (float)(c->fb_w - 1) / (len + 2.0f * margin);  // piksel per mm
  int h = (int)c->fb_h;
#define PX(wx) ((int)lroundf(((wx) + margin) * s))
#define PY(wy) (h - 1 - (int)lroundf(((wy) + margin) * s))

  fill_rect(c, 0, 0, (int)c->fb_w - 1, h - 1, 236, 236, 228);  // lantai
  int half = (int)fmaxf(1.0f, LINE_HALF_MM * s);
  for (int i = 0; i < n; i++) {
    float p = (float)i * d;
    fill_rect(c, PX(p) - half, PY(len), PX(p) + half, PY(0), 25, 25, 25);  // garis utara-selatan
    fill_rect(c, PX(0), PY(p) - half, PX(len), PY(p) + half, 25, 25, 25);  // garis timur-barat
  }
  // simpul start (hijau)
  int sx = (int)clampf(roundf(attr_read_float(c->a_sx)), 0.0f, (float)(n - 1));
  int sy = (int)clampf(roundf(attr_read_float(c->a_sy)), 0.0f, (float)(n - 1));
  fill_rect(c, PX((float)sx * d) - 3, PY((float)sy * d) - 3, PX((float)sx * d) + 3, PY((float)sy * d) + 3, 30, 170, 70);

  // robot: badan (biru), roda (abu tua), sensor (merah = lihat garis)
  float fx = cosf(c->th), fy = sinf(c->th);
  float rx = fy, ry = -fx;
  for (int k = 0; k <= 10; k++) {
    float t = 125.0f * (float)k / 10.0f;
    fill_circle(c, PX(c->x + fx * t), PY(c->y + fy * t), (int)fmaxf(2.0f, 30.0f * s), 40, 110, 220);
  }
  for (int sgn = -1; sgn <= 1; sgn += 2) {
    float wx = c->x + rx * (float)sgn * TRACK_MM * 0.5f, wy = c->y + ry * (float)sgn * TRACK_MM * 0.5f;
    fill_circle(c, PX(wx), PY(wy), (int)fmaxf(2.0f, 15.0f * s), 70, 70, 70);
  }
  float shift = attr_read_float(c->a_shift);
  for (int i = 0; i < N_SENSOR; i++) {
    float wx, wy;
    sensor_world(c, i, shift, &wx, &wy);
    if (c->cover[i] > 0.5f) fill_circle(c, PX(wx), PY(wy), 2, 230, 30, 30);
    else fill_circle(c, PX(wx), PY(wy), 1, 255, 200, 0);
  }
#undef PX
#undef PY
  buffer_write(c->fb, 0, c->pix, c->fb_w * c->fb_h * 4);
}

// ------------------------------------------------------------------ jam utama
static void on_tick(void *user_data) {
  chip_t *c = (chip_t *)user_data;
  c->tick++;
  for (int w = 0; w < 2; w++) {
    float d = pin_read(c->pwm[w]) == HIGH ? 1.0f : 0.0f;
    c->duty[w] += PWM_ALPHA * (d - c->duty[w]);
  }
  emit_encoders(c);
  if (c->tick % PHYS_EVERY == 0) {
    check_reset(c);
    physics(c, (float)(PHYS_EVERY * TICK_US) * 1e-6f);
    update_sensors(c);
    write_sig(c);
    write_battery(c);
    write_buttons(c);
  }
  if (c->tick % DRAW_EVERY == 0) draw(c);
}

void chip_init(void) {
  chip_t *c = (chip_t *)calloc(1, sizeof(chip_t));
  for (int i = 0; i < N_BTN; i++) c->btn[i] = pin_init(BTN_NAMES[i], INPUT_PULLUP);
  c->btn_out = pin_init("BTN", ANALOG);
  c->vbat = pin_init("VBAT", ANALOG);
  c->sel[0] = pin_init("S0", INPUT);
  c->sel[1] = pin_init("S1", INPUT);
  c->sel[2] = pin_init("S2", INPUT);
  c->sel[3] = pin_init("S3", INPUT);
  c->sig = pin_init("SIG", ANALOG);
  c->stby = pin_init("STBY", INPUT);
  c->in1[0] = pin_init("AIN1", INPUT);
  c->in2[0] = pin_init("AIN2", INPUT);
  c->pwm[0] = pin_init("PWMA", INPUT);
  c->in1[1] = pin_init("BIN1", INPUT);
  c->in2[1] = pin_init("BIN2", INPUT);
  c->pwm[1] = pin_init("PWMB", INPUT);
  c->enc_a[0] = pin_init("ENC_LA", OUTPUT_LOW);
  c->enc_b[0] = pin_init("ENC_LB", OUTPUT_LOW);
  c->enc_a[1] = pin_init("ENC_RA", OUTPUT_LOW);
  c->enc_b[1] = pin_init("ENC_RB", OUTPUT_LOW);

  c->a_battery = attr_init_float("battery", 7.6f);
  c->a_shift = attr_init_float("shift", 0.0f);
  c->a_grid = attr_init_float("gridSize", 4.0f);
  c->a_spacing = attr_init_float("nodeSpacing", 300.0f);
  c->a_sx = attr_init_float("startX", 0.0f);
  c->a_sy = attr_init_float("startY", 0.0f);
  c->a_sh = attr_init_float("startHeading", 0.0f);
  c->a_reset = attr_init_float("reset", 0.0f);
  c->a_scale = attr_init_float("adcFullScale", 5.0f);
  c->rng = 12345u;

  const uint32_t ids[6] = {c->a_grid, c->a_spacing, c->a_sx, c->a_sy, c->a_sh, c->a_reset};
  for (int i = 0; i < 6; i++) c->watch[i] = attr_read_float(ids[i]);
  reset_pose(c);

  pin_watch_config_t btn_watch = {.edge = BOTH, .pin_change = on_button, .user_data = c};
  for (int i = 0; i < N_BTN; i++) pin_watch(c->btn[i], &btn_watch);
  pin_watch_config_t sel_watch = {.edge = BOTH, .pin_change = on_select, .user_data = c};
  for (int k = 0; k < 4; k++) pin_watch(c->sel[k], &sel_watch);

  c->fb = framebuffer_init(&c->fb_w, &c->fb_h);
  c->pix = (uint8_t *)malloc(c->fb_w * c->fb_h * 4);

  update_sensors(c);
  write_sig(c);
  write_battery(c);
  write_buttons(c);
  draw(c);

  timer_config_t tc = {.callback = on_tick, .user_data = c};
  timer_t t = timer_init(&tc);
  timer_start(t, TICK_US, true);
}
