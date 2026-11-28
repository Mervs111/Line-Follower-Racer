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

// ==================================================================== sensor mentah (mux CD74HC4067)
static inline void muxSelect(uint8_t ch) {
  digitalWrite(Pins::MUX_S0, ch & 0x1);
  digitalWrite(Pins::MUX_S1, (ch >> 1) & 0x1);
  digitalWrite(Pins::MUX_S2, (ch >> 2) & 0x1);
  digitalWrite(Pins::MUX_S3, (ch >> 3) & 0x1);
}

void LineFollower::readRaw(uint16_t out[]) {
  for (uint8_t i = 0; i < SENSOR_COUNT; i++) {
    uint8_t s = Config::SENSOR_REVERSED ? (SENSOR_COUNT - 1 - i) : i;
    muxSelect(Pins::MUX_FIRST_CHANNEL + s);
    delayMicroseconds(Config::MUX_SETTLE_US);  // beberapa us saja, bukan delay() ms
    out[i] = analogRead(Pins::MUX_SIG);
  }
}

// ==================================================================== motor (TB6612FNG)
// PWM LEDC 20 kHz 8 bit. Core 3.x memakai nomor pin, core 2.x memakai nomor kanal.
static constexpr uint8_t PWM_CH_LEFT = 0;
static constexpr uint8_t PWM_CH_RIGHT = 1;

static void pwmInit(uint8_t pin, uint8_t ch) {
#if LF_CORE3
  (void)ch;
  ledcAttach(pin, Config::PWM_FREQ_HZ, Config::PWM_BITS);
#else
  ledcSetup(ch, Config::PWM_FREQ_HZ, Config::PWM_BITS);
  ledcAttachPin(pin, ch);
#endif
}

static void pwmWrite(uint8_t pin, uint8_t ch, uint32_t duty) {
#if LF_CORE3
  (void)ch;
  ledcWrite(pin, duty);
#else
  (void)pin;
  ledcWrite(ch, duty);
#endif
}

// Satu kanal TB6612: IN1/IN2 menentukan arah, PWM besarnya. v == 0 -> IN1 = IN2 = HIGH = rem.
static void driveChannel(uint8_t in1, uint8_t in2, uint8_t pwmPin, uint8_t ch, int v) {
  if (v > 0) {
    digitalWrite(in1, HIGH);
    digitalWrite(in2, LOW);
  } else if (v < 0) {
    digitalWrite(in1, LOW);
    digitalWrite(in2, HIGH);
  } else {
    digitalWrite(in1, HIGH);
    digitalWrite(in2, HIGH);
  }
  pwmWrite(pwmPin, ch, (uint32_t)abs(v));
}

void LineFollower::driveRaw(int left, int right) {
  if (Config::MOTOR_L_INVERT) left = -left;
  if (Config::MOTOR_R_INVERT) right = -right;
  left = constrain(left, -255, 255);
  right = constrain(right, -255, 255);
  driveChannel(Pins::MOTOR_AIN1, Pins::MOTOR_AIN2, Pins::MOTOR_PWMA, PWM_CH_LEFT, left);
  driveChannel(Pins::MOTOR_BIN1, Pins::MOTOR_BIN2, Pins::MOTOR_PWMB, PWM_CH_RIGHT, right);
  if (!motorsEnabled_) {
    digitalWrite(Pins::MOTOR_STBY, HIGH);
    motorsEnabled_ = true;
  }
}

void LineFollower::motor(int left, int right) {
  lastLeft_ = constrain(left, -255, 255);
  lastRight_ = constrain(right, -255, 255);
  driveRaw(lastLeft_, lastRight_);
}

void LineFollower::stop() { motor(0, 0); }

void LineFollower::release() {
  driveChannel(Pins::MOTOR_AIN1, Pins::MOTOR_AIN2, Pins::MOTOR_PWMA, PWM_CH_LEFT, 0);
  driveChannel(Pins::MOTOR_BIN1, Pins::MOTOR_BIN2, Pins::MOTOR_PWMB, PWM_CH_RIGHT, 0);
  digitalWrite(Pins::MOTOR_STBY, LOW);
  motorsEnabled_ = false;
  lastLeft_ = lastRight_ = 0;
}

// ==================================================================== begin
void LineFollower::begin() {
  // Motor mati dulu: STBY LOW, arah LOW, PWM 0
  pinMode(Pins::MOTOR_STBY, OUTPUT);
  digitalWrite(Pins::MOTOR_STBY, LOW);
  motorsEnabled_ = false;
  const uint8_t dirPins[] = {Pins::MOTOR_AIN1, Pins::MOTOR_AIN2, Pins::MOTOR_BIN1, Pins::MOTOR_BIN2};
  for (uint8_t p : dirPins) {
    pinMode(p, OUTPUT);
    digitalWrite(p, LOW);
  }
  pwmInit(Pins::MOTOR_PWMA, PWM_CH_LEFT);
  pwmInit(Pins::MOTOR_PWMB, PWM_CH_RIGHT);
  pwmWrite(Pins::MOTOR_PWMA, PWM_CH_LEFT, 0);
  pwmWrite(Pins::MOTOR_PWMB, PWM_CH_RIGHT, 0);

  // Mux + ADC1 (atenuasi 11 dB: rentang sampai ±3,1 V)
  const uint8_t muxPins[] = {Pins::MUX_S0, Pins::MUX_S1, Pins::MUX_S2, Pins::MUX_S3};
  for (uint8_t p : muxPins) {
    pinMode(p, OUTPUT);
    digitalWrite(p, LOW);
  }
  analogReadResolution(12);
  analogSetPinAttenuation(Pins::MUX_SIG, ADC_11db);
  analogSetPinAttenuation(Pins::VBAT_SENSE, ADC_11db);
  analogSetPinAttenuation(Pins::BUTTONS, ADC_11db);

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
