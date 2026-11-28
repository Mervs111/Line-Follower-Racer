// LineFollower.cpp — implementasi library LFM X1. Penjelasan tiap fungsi ada di LineFollower.h.
#include "LineFollower.h"

#include <esp_timer.h>

// ==================================================================== buzzer
// Buzzer dimatikan oleh esp_timer sekali jalan, jadi beep() tidak pernah menahan loop.
static esp_timer_handle_t buzzerTimer = nullptr;

static void buzzerOff(void*) { digitalWrite(Pins::BUZZER, LOW); }

void LineFollower::beep(uint16_t ms) {
  if (ms == 0) return;
  if (buzzerTimer == nullptr) return;  // begin() belum dipanggil
  esp_timer_stop(buzzerTimer);         // bunyi sebelumnya diganti yang baru
  digitalWrite(Pins::BUZZER, HIGH);
  esp_timer_start_once(buzzerTimer, (uint64_t)ms * 1000ULL);
}

// ==================================================================== begin
void LineFollower::begin() {
  // Motor mati dulu: STBY LOW, semua input driver LOW (coast)
  pinMode(Pins::MOTOR_STBY, OUTPUT);
  digitalWrite(Pins::MOTOR_STBY, LOW);
  const uint8_t motorPins[] = {Pins::MOTOR_AIN1, Pins::MOTOR_AIN2, Pins::MOTOR_BIN1, Pins::MOTOR_BIN2,
                               Pins::MOTOR_PWMA, Pins::MOTOR_PWMB};
  for (uint8_t p : motorPins) {
    pinMode(p, OUTPUT);
    digitalWrite(p, LOW);
  }

  // Buzzer
  pinMode(Pins::BUZZER, OUTPUT);
  digitalWrite(Pins::BUZZER, LOW);
  if (buzzerTimer == nullptr) {
    esp_timer_create_args_t args = {};
    args.callback = &buzzerOff;
    args.name = "lf_buzzer";
    esp_timer_create(&args, &buzzerTimer);
  }
}
