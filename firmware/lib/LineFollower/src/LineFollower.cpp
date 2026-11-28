// LineFollower.cpp — implementasi library LFM X1. Penjelasan tiap fungsi ada di LineFollower.h.
#include "LineFollower.h"

#include <Preferences.h>
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

// ==================================================================== kalibrasi (min/max mentah, NVS)
static const char* const NVS_NAMESPACE = "lfm";

void LineFollower::calibrationStart() {
  for (uint8_t i = 0; i < SENSOR_COUNT; i++) {
    workMin_[i] = 4095;
    workMax_[i] = 0;
  }
}

void LineFollower::calibrationUpdate() {
  readRaw(raw_);
  for (uint8_t i = 0; i < SENSOR_COUNT; i++) {
    if (raw_[i] < workMin_[i]) workMin_[i] = raw_[i];
    if (raw_[i] > workMax_[i]) workMax_[i] = raw_[i];
  }
  // tampilan bar tetap hidup selama kalibrasi: normalisasi dengan rentang yang sedang dikumpulkan
  for (uint8_t i = 0; i < SENSOR_COUNT; i++) {
    int32_t range = (int32_t)workMax_[i] - workMin_[i];
    int32_t v = range > 0 ? ((int32_t)raw_[i] - workMin_[i]) * 1000 / range : 0;
    val_[i] = (uint16_t)constrain(v, 0, 1000);
  }
}

bool LineFollower::calibrationFinish(bool save) {
  // Sensor yang rentangnya cukup memakai hasil baru; yang gagal tetap memakai nilai lama.
  calBadMask_ = 0;
  for (uint8_t i = 0; i < SENSOR_COUNT; i++) {
    if (workMax_[i] > workMin_[i] && workMax_[i] - workMin_[i] >= Config::MIN_CAL_RANGE) {
      calMin_[i] = workMin_[i];
      calMax_[i] = workMax_[i];
    } else {
      calBadMask_ |= (uint16_t)(1u << i);
    }
  }
  calibrated_ = (calBadMask_ == 0);
  if (calibrated_ && save) saveCalibration();
  haveRead_ = false;  // bacaan berikutnya memakai kalibrasi baru
  return calibrated_;
}

bool LineFollower::calibrate(uint16_t durationMs, bool spin) {
  calibrationStart();
  uint32_t t0 = millis();
  for (;;) {
    uint32_t t = millis() - t0;
    if (t >= durationMs) break;
    if (spin) {
      // ayun: kanan 1 bagian, kiri 2 bagian, kanan 1 bagian -> kembali ke arah awal tiap siklus
      uint32_t phase = (t / Config::CAL_SWING_MS) % 4;
      int dir = (phase == 0 || phase == 3) ? 1 : -1;
      motor(dir * Config::CAL_SPIN_PWM, -dir * Config::CAL_SPIN_PWM);
    }
    calibrationUpdate();
    yield();
  }
  if (spin) stop();
  return calibrationFinish(true);
}

bool LineFollower::saveCalibration() {
  Preferences prefs;
  if (!prefs.begin(NVS_NAMESPACE, false)) return false;
  size_t a = prefs.putBytes("cmin", calMin_, sizeof(calMin_));
  size_t b = prefs.putBytes("cmax", calMax_, sizeof(calMax_));
  prefs.end();
  return a == sizeof(calMin_) && b == sizeof(calMax_);
}

bool LineFollower::loadCalibration() {
  Preferences prefs;
  if (!prefs.begin(NVS_NAMESPACE, true)) return false;  // namespace belum ada = belum pernah kalibrasi
  uint16_t mn[SENSOR_COUNT], mx[SENSOR_COUNT];
  bool ok = prefs.getBytesLength("cmin") == sizeof(mn) && prefs.getBytesLength("cmax") == sizeof(mx) &&
            prefs.getBytes("cmin", mn, sizeof(mn)) == sizeof(mn) && prefs.getBytes("cmax", mx, sizeof(mx)) == sizeof(mx);
  prefs.end();
  if (!ok) return false;
  for (uint8_t i = 0; i < SENSOR_COUNT; i++) {
    if (mx[i] <= mn[i] || mx[i] - mn[i] < Config::MIN_CAL_RANGE) return false;
  }
  memcpy(calMin_, mn, sizeof(mn));
  memcpy(calMax_, mx, sizeof(mx));
  calibrated_ = true;
  calBadMask_ = 0;
  haveRead_ = false;
  return true;
}

// ==================================================================== garis & posisi
void LineFollower::setLineColor(bool blackOnWhite) {
  blackLine_ = blackOnWhite;
  haveRead_ = false;
}

void LineFollower::readSensors() {
  readRaw(raw_);
  lastReadUs_ = micros();
  haveRead_ = true;

  int32_t num = 0;  // jumlah nilai x posisi x (0,01 mm)
  int32_t den = 0;
  uint16_t pattern = 0;
  for (uint8_t i = 0; i < SENSOR_COUNT; i++) {
    int32_t range = (int32_t)calMax_[i] - calMin_[i];
    int32_t v = range > 0 ? ((int32_t)raw_[i] - calMin_[i]) * 1000 / range : 0;
    v = constrain(v, 0, 1000);
    if (!blackLine_) v = 1000 - v;  // garis putih: yang terang jadi 1000
    val_[i] = (uint16_t)v;
    if (v >= Config::LINE_THRESHOLD) pattern |= (uint16_t)(1u << i);
    if (v > Config::NOISE_FLOOR) {
      num += v * Config::SENSOR_X_CMM[i];
      den += v;
    }
  }
  pattern_ = pattern;

  if (den < Config::LOST_SUM) {
    lineSeen_ = false;
    position_ = lastSeenPos_ >= 0 ? 1000 : -1000;
  } else {
    const int32_t xOuter = Config::SENSOR_X_CMM[SENSOR_COUNT - 1];
    int32_t p = (num / den) * 1000 / xOuter;
    position_ = (int)constrain(p, -1000, 1000);
    lastSeenPos_ = position_;
    lineSeen_ = true;
  }
}

void LineFollower::refreshSensors() {
  if (!haveRead_ || (uint32_t)(micros() - lastReadUs_) >= Config::SENSOR_CACHE_US) readSensors();
}

uint16_t LineFollower::sensorValue(uint8_t n) {
  if (n < 1 || n > SENSOR_COUNT) return 0;
  refreshSensors();
  return val_[n - 1];
}

uint16_t LineFollower::sensorPattern() {
  refreshSensors();
  return pattern_;
}

int LineFollower::position() {
  refreshSensors();
  return position_;
}

bool LineFollower::lineDetected() {
  refreshSensors();
  return lineSeen_;
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

  // Kalibrasi bawaan sebelum ada data: rentang ADC penuh. Lalu coba muat hasil kalibrasi terakhir dari NVS.
  for (uint8_t i = 0; i < SENSOR_COUNT; i++) {
    calMin_[i] = 0;
    calMax_[i] = 4095;
  }
  calibrated_ = false;
  loadCalibration();

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
