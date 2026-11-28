// LfEncoders.cpp — encoder lewat PCNT. Core lama (IDF 3.x/4.x) memakai driver/pcnt.h, core >= 3 (IDF >= 5)
// memakai driver/pulse_cnt.h. Penghitung hardware hanya 16 bit dan kembali ke 0 di batas, jadi esp_timer 200 Hz
// membaca keduanya dan menjumlahkan selisihnya ke penghitung 32 bit. Pada 500 RPM (±7.000 hitungan/s) selisih
// tiap 5 ms hanya ±35, jauh dari batas.
#include "LfEncoders.h"

#include <driver/gpio.h>
#include <esp_timer.h>

#include "LfCompat.h"
#include "Pins.h"
#include "RobotConfig.h"

#if LF_CORE3
#include <driver/pulse_cnt.h>
#else
#include <driver/pcnt.h>
#endif

namespace LfEncoders {

static constexpr int16_t LIMIT = 30000;
static constexpr uint32_t POLL_US = 5000;

static portMUX_TYPE lock = portMUX_INITIALIZER_UNLOCKED;
static int32_t total[2] = {0, 0};
static int16_t last[2] = {0, 0};
static bool ready = false;
static esp_timer_handle_t pollTimer = nullptr;

#if LF_CORE3
static pcnt_unit_handle_t units[2] = {nullptr, nullptr};

static bool setupUnit(uint8_t idx, uint8_t pinA, uint8_t pinB) {
  pcnt_unit_config_t uc = {};
  uc.low_limit = -LIMIT;
  uc.high_limit = LIMIT;
  if (pcnt_new_unit(&uc, &units[idx]) != ESP_OK) return false;
  pcnt_glitch_filter_config_t fc = {};
  fc.max_glitch_ns = 1000;
  pcnt_unit_set_glitch_filter(units[idx], &fc);

  pcnt_chan_config_t ca = {};
  ca.edge_gpio_num = pinA;
  ca.level_gpio_num = pinB;
  pcnt_channel_handle_t chA = nullptr, chB = nullptr;
  if (pcnt_new_channel(units[idx], &ca, &chA) != ESP_OK) return false;
  pcnt_chan_config_t cb = {};
  cb.edge_gpio_num = pinB;
  cb.level_gpio_num = pinA;
  if (pcnt_new_channel(units[idx], &cb, &chB) != ESP_OK) return false;
  // dekoder kuadratur x4 (contoh rotary encoder ESP-IDF)
  pcnt_channel_set_edge_action(chA, PCNT_CHANNEL_EDGE_ACTION_DECREASE, PCNT_CHANNEL_EDGE_ACTION_INCREASE);
  pcnt_channel_set_level_action(chA, PCNT_CHANNEL_LEVEL_ACTION_KEEP, PCNT_CHANNEL_LEVEL_ACTION_INVERSE);
  pcnt_channel_set_edge_action(chB, PCNT_CHANNEL_EDGE_ACTION_INCREASE, PCNT_CHANNEL_EDGE_ACTION_DECREASE);
  pcnt_channel_set_level_action(chB, PCNT_CHANNEL_LEVEL_ACTION_KEEP, PCNT_CHANNEL_LEVEL_ACTION_INVERSE);

  pcnt_unit_enable(units[idx]);
  pcnt_unit_clear_count(units[idx]);
  pcnt_unit_start(units[idx]);
  return true;
}

static int16_t rawCount(uint8_t idx) {
  int v = 0;
  pcnt_unit_get_count(units[idx], &v);
  return (int16_t)v;
}

static void clearHw(uint8_t idx) { pcnt_unit_clear_count(units[idx]); }

#else
static const pcnt_unit_t units[2] = {PCNT_UNIT_0, PCNT_UNIT_1};

static bool setupUnit(uint8_t idx, uint8_t pinA, uint8_t pinB) {
  pcnt_config_t c = {};
  c.pulse_gpio_num = pinA;
  c.ctrl_gpio_num = pinB;
  c.channel = PCNT_CHANNEL_0;
  c.unit = units[idx];
  c.pos_mode = PCNT_COUNT_DEC;
  c.neg_mode = PCNT_COUNT_INC;
  c.lctrl_mode = PCNT_MODE_REVERSE;
  c.hctrl_mode = PCNT_MODE_KEEP;
  c.counter_h_lim = LIMIT;
  c.counter_l_lim = -LIMIT;
  if (pcnt_unit_config(&c) != ESP_OK) return false;
  c.pulse_gpio_num = pinB;
  c.ctrl_gpio_num = pinA;
  c.channel = PCNT_CHANNEL_1;
  c.pos_mode = PCNT_COUNT_INC;
  c.neg_mode = PCNT_COUNT_DEC;
  if (pcnt_unit_config(&c) != ESP_OK) return false;
  pcnt_set_filter_value(units[idx], 100);  // 100 siklus APB = 1,25 us
  pcnt_filter_enable(units[idx]);
  pcnt_counter_pause(units[idx]);
  pcnt_counter_clear(units[idx]);
  pcnt_counter_resume(units[idx]);
  return true;
}

static int16_t rawCount(uint8_t idx) {
  int16_t v = 0;
  pcnt_get_counter_value(units[idx], &v);
  return v;
}

static void clearHw(uint8_t idx) { pcnt_counter_clear(units[idx]); }
#endif

// Selisih hitungan sejak bacaan terakhir. Penghitung kembali ke 0 di +-LIMIT; kalau ternyata hardware membungkus
// di +-32768, lompatan +-65536 juga dikenali.
static int32_t unwrap(int32_t d) {
  if (d < -45000) return d + 65536;
  if (d < -LIMIT / 2) return d + LIMIT;
  if (d > 45000) return d - 65536;
  if (d > LIMIT / 2) return d - LIMIT;
  return d;
}

static void pollLocked() {
  for (uint8_t i = 0; i < 2; i++) {
    int16_t now = rawCount(i);
    total[i] += unwrap((int32_t)now - last[i]);
    last[i] = now;
  }
}

static void pollTask(void*) {
  portENTER_CRITICAL(&lock);
  pollLocked();
  portEXIT_CRITICAL(&lock);
}

bool begin() {
  if (ready) return true;
  bool ok = setupUnit(0, Pins::ENC_L_A, Pins::ENC_L_B) && setupUnit(1, Pins::ENC_R_A, Pins::ENC_R_B);
  if (!ok) return false;
  // pull-up internal (encoder hall N20 biasanya open collector)
  const uint8_t pins[] = {Pins::ENC_L_A, Pins::ENC_L_B, Pins::ENC_R_A, Pins::ENC_R_B};
  for (uint8_t p : pins) gpio_pullup_en((gpio_num_t)p);

  esp_timer_create_args_t args = {};
  args.callback = &pollTask;
  args.name = "lf_enc";
  if (esp_timer_create(&args, &pollTimer) != ESP_OK) return false;
  esp_timer_start_periodic(pollTimer, POLL_US);
  ready = true;
  return true;
}

void read(int32_t& left, int32_t& right) {
  if (!ready) {
    left = right = 0;
    return;
  }
  portENTER_CRITICAL(&lock);
  pollLocked();
  left = total[0];
  right = total[1];
  portEXIT_CRITICAL(&lock);
  if (Config::ENC_L_INVERT) left = -left;
  if (Config::ENC_R_INVERT) right = -right;
}

void reset() {
  if (!ready) return;
  portENTER_CRITICAL(&lock);
  for (uint8_t i = 0; i < 2; i++) {
    clearHw(i);
    total[i] = 0;
    last[i] = 0;
  }
  portEXIT_CRITICAL(&lock);
}

}  // namespace LfEncoders
