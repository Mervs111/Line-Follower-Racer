// LfRoute.cpp — path planning per indeks, gerak terukur encoder, dan rute terpendek grid.
// Mesin keadaan ini port dari Controller di simulasi/lfm_control.py (lulus uji 2D dan CoppeliaSim 26/10):
//   WATCH    ikut garis (PID) sambil menunggu pemicu indeks aktif
//   CHECK    cabang pertama terlihat: maju lurus 30 mm sambil mengumpulkan cabang kiri/kanan
//   SKIP     persimpangan ini bukan pemicu: lurus melewatinya, lalu WATCH lagi
//   CROSS    aksi lurus: lurus melewati garis melintang
//   APPROACH aksi belok/berhenti: maju sampai poros roda di tengah persimpangan
//   TURN     putar di tempat sampai sudut minimal (encoder) dan sensor tengah melihat garis
//   POST     ikut garis sejauh followMm (pemicu belum dicek), lalu indeks berikutnya
// Jarak diukur encoder. Kalau encoder tidak bergerak (rusak/belum tersambung), jarak diganti perkiraan waktu.
#include <math.h>

#include "LfEncoders.h"
#include "LineFollower.h"

static constexpr float RAD2DEG = 57.29578f;

// Perkiraan waktu tempuh (ms) untuk jarak mm pada PWM tertentu; dasar batas waktu cadangan.
static uint32_t expectMs(float mm, int pwm) {
  float mmps = (float)abs(pwm) / 255.0f * Config::MOTOR_MAX_MM_S;
  if (mmps < 50.0f) mmps = 50.0f;
  return (uint32_t)(fabsf(mm) / mmps * 1000.0f);
}

// Busur tiap roda (mm) saat putar di tempat sejauh deg derajat.
static float arcMm(float deg) { return deg / RAD2DEG * Config::WHEEL_TRACK_MM * 0.5f; }

// ==================================================================== bantu
void LineFollower::phaseBegin(Phase p) {
  phase_ = p;
  LfEncoders::read(phEncL_, phEncR_);
  phMs_ = millis();
}

float LineFollower::phaseMm() {
  int32_t l, r;
  LfEncoders::read(l, r);
  return (float)((l - phEncL_) + (r - phEncR_)) * 0.5f * Config::MM_PER_COUNT;
}

float LineFollower::phaseDeg() {
  int32_t l, r;
  LfEncoders::read(l, r);
  return (float)((r - phEncR_) - (l - phEncL_)) * Config::MM_PER_COUNT / Config::WHEEL_TRACK_MM * RAD2DEG;
}

void LineFollower::checkEncoderAlive() {
  // motor sudah diperintah jalan > 300 ms di fase ini tapi encoder hampir diam -> encoder dianggap mati
  if (encDead_ || millis() - phMs_ < 300) return;
  int32_t l, r;
  LfEncoders::read(l, r);
  if (abs(l - phEncL_) + abs(r - phEncR_) < 10) encDead_ = true;
}

bool LineFollower::reached(float targetMm, int pwm) {
  uint32_t el = millis() - phMs_;
  uint32_t ex = expectMs(targetMm, pwm);
  checkEncoderAlive();
  if (encDead_) return el >= ex * 13 / 10 + 50;               // tanpa encoder: perkiraan waktu
  return fabsf(phaseMm()) >= targetMm || el >= ex * 4 + 500;  // dengan encoder (+ batas pengaman)
}

void LineFollower::straight() {
  // lurus dengan menahan arah dari encoder (miring ke kiri -> roda kiri dipercepat)
  float c = Config::HEADING_KP * phaseDeg();
  c = constrain(c, -60.0f, 60.0f);
  motor(Config::APPROACH_PWM + (int)c, Config::APPROACH_PWM - (int)c);
}

void LineFollower::routeFail(const char* msg) {
  stop();
  routeState_ = ROUTE_FAILED;
  routeMsg_ = msg;
  if (chain_) aborted_ = true;
}

// ==================================================================== mulai / hentikan
void LineFollower::routeStart(const LfStep* steps, uint8_t count, bool chain) {
  steps_ = steps;
  routeCount_ = count;
  routeIdx_ = 0;
  chain_ = chain;
  routeMsg_ = "";
  if (count == 0 || steps == nullptr) {
    routeState_ = ROUTE_DONE;
    return;
  }
  if (!chain || chainFresh_) {
    curSpeed_ = steps[0].speed;
    encDead_ = false;
  }
  ignoreMm_ = 0;
  endPending_ = false;
  lostSinceMs_ = 0;
  routeTickUs_ = micros() - 1000;
  routeState_ = ROUTE_RUNNING;
  resetFollow();
  phaseBegin(PH_WATCH);
}

void LineFollower::routeBegin(const LfStep* steps, uint8_t count) { routeStart(steps, count, false); }

void LineFollower::routeStop() {
  stop();
  if (routeState_ == ROUTE_RUNNING) {
    routeState_ = ROUTE_IDLE;
    routeMsg_ = "Dihentikan";
  }
}

void LineFollower::routeReset() {
  aborted_ = false;
  chainFresh_ = true;
  routeState_ = ROUTE_IDLE;
  routeMsg_ = "";
}

// ==================================================================== aksi
void LineFollower::beginAction() {
  const LfStep& st = steps_[routeIdx_];
  if (routeBeep_) beep(30);
  if (st.action == ACT_FORWARD) {
    if (toCenterMm_ > 0) {
      phase_ = PH_CROSS;  // jarak tetap dihitung dari cabang pertama terlihat
    } else {
      startPost();
    }
    return;
  }
  if (toCenterMm_ > 0) {
    phase_ = PH_APPROACH;
    return;
  }
  // pemicu langsung / ujung garis: aksi di tempat
  if (st.action == ACT_STOP) {
    stop();
    routeIdx_ = routeCount_ - 1;
    routeState_ = ROUTE_DONE;
    routeMsg_ = "Selesai: berhenti";
    return;
  }
  stop();
  phaseBegin(PH_TURN);
}

void LineFollower::startPost() {
  const LfStep& st = steps_[routeIdx_];
  setLineColor(!st.whiteLine);
  curSpeed_ = st.speed;
  lostSinceMs_ = 0;
  resetFollow();
  phaseBegin(PH_POST);
}

void LineFollower::finishStep() {
  routeIdx_++;
  if (routeIdx_ >= routeCount_) {
    routeIdx_ = routeCount_ - 1;
    routeState_ = ROUTE_DONE;
    routeMsg_ = "Selesai";
    if (!chain_) stop();  // runIndex(): robot tetap jalan, indeks berikutnya menyambung
    return;
  }
  ignoreMm_ = 0;
  endPending_ = false;
  phaseBegin(PH_WATCH);
}

// ==================================================================== satu siklus (1 kHz)
LfRouteState LineFollower::routeUpdate() {
  if (routeState_ != ROUTE_RUNNING) return routeState_;
  uint32_t now = micros();
  if ((uint32_t)(now - routeTickUs_) < 1000) return routeState_;
  routeTickUs_ = now;

  const LfStep& st = steps_[routeIdx_];
  refreshSensors();

  // ikut garis + cek garis hilang (dipakai WATCH dan POST)
  auto followLine = [&]() {
    follow(curSpeed_, kp_, kd_);
    if (lineSeen_) {
      lostSinceMs_ = 0;
    } else if (lostSinceMs_ == 0) {
      lostSinceMs_ = millis() | 1;
    } else if (millis() - lostSinceMs_ >= Config::LOST_FAIL_MS) {
      routeFail("Gagal: garis hilang");
    }
  };

  switch (phase_) {
    case PH_WATCH: {
      if (ignoreMm_ > 0) {
        if (!reached(ignoreMm_, curSpeed_)) {
          followLine();
          break;
        }
        ignoreMm_ = 0;
      }
      if (st.trigger == TRIG_DIRECT) {
        toCenterMm_ = 0;
        beginAction();
        break;
      }
      if (st.trigger == TRIG_END) {
        if (lineSeen_) {
          endPending_ = false;
          followLine();
          break;
        }
        if (!endPending_) {
          endPending_ = true;
          phaseBegin(PH_WATCH);
        }
        if (reached(Config::END_CONFIRM_MM, Config::APPROACH_PWM)) {
          toCenterMm_ = 0;
          beginAction();
        } else {
          straight();
        }
        break;
      }
      bool left = (pattern_ & 0x0007) != 0, right = (pattern_ & 0x0E00) != 0;
      if (left || right) {
        // tengah persimpangan = y sensor lengan terdepan yang melihat + setengah lebar garis, di depan poros
        float y = 0;
        for (uint8_t i = 0; i < 3; i++) {
          if (left && val_[i] >= Config::LINE_THRESHOLD) y = fmaxf(y, Config::SENSOR_Y_MM[i]);
          uint8_t j = SENSOR_COUNT - 1 - i;
          if (right && val_[j] >= Config::LINE_THRESHOLD) y = fmaxf(y, Config::SENSOR_Y_MM[j]);
        }
        toCenterMm_ = y + Config::LINE_WIDTH_MM * 0.5f + Config::APPROACH_OFFSET_MM;
        brL_ = left;
        brR_ = right;
        phaseBegin(PH_CHECK);
        straight();
        break;
      }
      followLine();
      break;
    }

    case PH_CHECK: {
      // lurus tanpa PID (garis melintang mengacaukan posisi) sambil mengumpulkan cabang
      brL_ |= (pattern_ & 0x0007) != 0;
      brR_ |= (pattern_ & 0x0E00) != 0;
      if (!reached(Config::CHECK_MM, Config::APPROACH_PWM)) {
        straight();
        break;
      }
      bool match = st.trigger == TRIG_JUNCTION || (st.trigger == TRIG_LEFT && brL_) ||
                   (st.trigger == TRIG_RIGHT && brR_) || (st.trigger == TRIG_BOTH && brL_ && brR_);
      if (match) {
        beginAction();
      } else {
        phase_ = PH_SKIP;  // bukan pemicu indeks ini: lewati
        straight();
      }
      break;
    }

    case PH_SKIP:
    case PH_CROSS:
      if (!reached(Config::CROSS_MM, Config::APPROACH_PWM)) {
        straight();
        break;
      }
      if (phase_ == PH_CROSS) {
        startPost();
      } else {
        ignoreMm_ = Config::SKIP_IGNORE_MM;
        resetFollow();
        phaseBegin(PH_WATCH);
      }
      break;

    case PH_APPROACH:
      if (!reached(toCenterMm_, Config::APPROACH_PWM)) {
        straight();
        break;
      }
      stop();
      if (st.action == ACT_STOP) {
        routeState_ = ROUTE_DONE;
        routeMsg_ = "Selesai: berhenti di tujuan";
        break;
      }
      phaseBegin(PH_TURN);
      break;

    case PH_TURN: {
      bool uturn = st.action == ACT_UTURN;
      float need = uturn ? Config::UTURN_MIN_DEG : Config::TURN_MIN_DEG;
      float maxDeg = uturn ? Config::UTURN_MAX_DEG : Config::TURN_MAX_DEG;
      uint32_t el = millis() - phMs_;
      checkEncoderAlive();
      bool angleOk, tooFar;
      if (encDead_) {
        angleOk = el >= expectMs(arcMm(need), Config::TURN_PWM) * 13 / 10;
        tooFar = el >= expectMs(arcMm(maxDeg), Config::TURN_PWM) * 13 / 10 + 300;
      } else {
        float ang = fabsf(phaseDeg());
        angleOk = ang >= need;
        tooFar = ang >= maxDeg || el >= expectMs(arcMm(maxDeg), Config::TURN_PWM) * 4 + 1000;
      }
      bool centerSees = val_[5] >= Config::LINE_THRESHOLD || val_[6] >= Config::LINE_THRESHOLD;
      if (angleOk && centerSees) {
        stop();
        startPost();
        break;
      }
      if (tooFar) {
        routeFail("Gagal: garis tidak ketemu saat belok");
        break;
      }
      int pwm = angleOk ? Config::TURN_PWM * 6 / 10 : Config::TURN_PWM;  // melambat saat mencari garis
      int s = (st.action == ACT_RIGHT) ? -1 : 1;                          // kiri & putar balik: CCW
      motor(-s * pwm, s * pwm);
      break;
    }

    case PH_POST:
      if (st.followMm == 0 || reached(st.followMm, curSpeed_)) {
        finishStep();
      } else {
        followLine();
      }
      break;
  }
  return routeState_;
}

// ==================================================================== versi menunggu (blok Mind+)
void LineFollower::syncButtons() {
  btnRaw_ = btnStable_ = readButton();
  btnChangedMs_ = millis();
  btnClickPending_ = BTN_NONE;
}

bool LineFollower::waitAbort() {
  static uint32_t lastCheck = 0;
  uint32_t now = millis();
  if (now - lastCheck < 10) return false;
  lastCheck = now;
  if (buttonClicked() == BTN_NONE) return false;
  stop();
  aborted_ = true;
  routeState_ = ROUTE_FAILED;
  routeMsg_ = "Dibatalkan tombol";
  return true;
}

bool LineFollower::runIndex(uint8_t trigger, uint8_t action, int speed, int followMm, bool whiteLine) {
  if (aborted_) return false;
  disarmChainWatchdog();
  if (chainFresh_) syncButtons();  // tombol yang ditekan untuk memulai program tidak dianggap batal
  single_.trigger = trigger;
  single_.action = action;
  single_.speed = (uint8_t)constrain(speed, 0, 255);
  single_.followMm = (uint16_t)constrain(followMm, 0, 65535);
  single_.whiteLine = whiteLine;
  routeStart(&single_, 1, true);
  chainFresh_ = false;
  while (routeUpdate() == ROUTE_RUNNING) {
    if (waitAbort()) return false;
    yield();
  }
  if (routeState_ != ROUTE_DONE) return false;
  if (action == ACT_STOP) {
    chainFresh_ = true;  // rute selesai; runIndex berikutnya mulai rute baru
  } else {
    armChainWatchdog();  // kalau program tidak memanggil motor/indeks lagi, robot berhenti sendiri
  }
  return true;
}

bool LineFollower::forwardMm(int speed, int mm) {
  if (aborted_) return false;
  syncButtons();
  speed = abs(speed);
  int dir = mm >= 0 ? 1 : -1;
  float target = (float)abs(mm);
  encDead_ = false;
  phaseBegin(PH_CROSS);
  uint32_t lastUs = micros() - 1000;
  while (!reached(target, speed)) {
    if ((uint32_t)(micros() - lastUs) >= 1000) {
      lastUs = micros();
      float c = constrain(Config::HEADING_KP * phaseDeg(), -80.0f, 80.0f);
      motor(dir * speed + (int)c, dir * speed - (int)c);
    }
    if (waitAbort()) return false;
    yield();
  }
  stop();
  return true;
}

bool LineFollower::turnDegrees(int speed, int deg) {
  if (aborted_) return false;
  syncButtons();
  speed = abs(speed);
  int s = deg >= 0 ? 1 : -1;
  float target = (float)abs(deg);
  encDead_ = false;
  phaseBegin(PH_TURN);
  for (;;) {
    checkEncoderAlive();
    bool done = encDead_ ? (millis() - phMs_ >= expectMs(arcMm(target), speed))
                         : (fabsf(phaseDeg()) >= target ||
                            millis() - phMs_ >= expectMs(arcMm(target), speed) * 4 + 500);
    if (done) break;
    motor(-s * speed, s * speed);
    if (waitAbort()) return false;
    yield();
  }
  stop();
  return true;
}

bool LineFollower::turnToLine(bool left, int speed) {
  if (aborted_) return false;
  syncButtons();
  speed = abs(speed);
  int s = left ? 1 : -1;
  encDead_ = false;
  phaseBegin(PH_TURN);
  for (;;) {
    refreshSensors();
    checkEncoderAlive();
    uint32_t el = millis() - phMs_;
    bool angleOk = encDead_ ? el >= expectMs(arcMm(Config::TURN_MIN_DEG), speed) * 13 / 10
                            : fabsf(phaseDeg()) >= Config::TURN_MIN_DEG;
    bool tooFar = encDead_ ? el >= expectMs(arcMm(Config::TURN_MAX_DEG), speed) * 13 / 10 + 300
                           : (fabsf(phaseDeg()) >= Config::TURN_MAX_DEG ||
                              el >= expectMs(arcMm(Config::TURN_MAX_DEG), speed) * 4 + 1000);
    if (angleOk && (val_[5] >= Config::LINE_THRESHOLD || val_[6] >= Config::LINE_THRESHOLD)) break;
    if (tooFar) {
      stop();
      return false;
    }
    motor(-s * speed, s * speed);
    if (waitAbort()) return false;
    yield();
  }
  stop();
  resetFollow();
  return true;
}

// ==================================================================== rute terpendek grid (Dijkstra)
uint8_t LineFollower::planGridRoute(uint8_t cols, uint8_t rows, uint8_t startX, uint8_t startY, uint8_t heading,
                                    uint8_t goalX, uint8_t goalY, const uint8_t* blocked, uint8_t nBlocked,
                                    LfStep* out, uint8_t maxSteps, uint8_t speed, uint16_t followMm) {
  constexpr uint8_t MAXN = 8;
  constexpr uint16_t NSTATE = MAXN * MAXN * 4;
  static const int8_t DX[4] = {1, 0, -1, 0};  // timur, utara, barat, selatan
  static const int8_t DY[4] = {0, 1, 0, -1};
  static uint32_t dist[NSTATE];
  static int16_t prev[NSTATE];
  static bool done[NSTATE];

  if (cols < 2 || rows < 1 || cols > MAXN || rows > MAXN || heading > 3 || out == nullptr || maxSteps == 0)
    return 0;
  if (startX >= cols || startY >= rows || goalX >= cols || goalY >= rows) return 0;
  if (startX == goalX && startY == goalY) return 0;

  auto isBlocked = [&](int x, int y) {
    for (uint8_t i = 0; i < nBlocked; i++)
      if (blocked[2 * i] == x && blocked[2 * i + 1] == y) return true;
    return false;
  };
  auto stateOf = [&](int x, int y, int h) { return (uint16_t)((y * cols + x) * 4 + h); };

  const uint16_t n = (uint16_t)cols * rows * 4;
  for (uint16_t i = 0; i < n; i++) {
    dist[i] = UINT32_MAX;
    prev[i] = -1;
    done[i] = false;
  }
  // ruas pertama wajib searah heading (robot sudah menghadap ke sana)
  int fx = startX + DX[heading], fy = startY + DY[heading];
  if (fx < 0 || fy < 0 || fx >= cols || fy >= rows || isBlocked(fx, fy)) return 0;
  uint16_t first = stateOf(fx, fy, heading);
  dist[first] = 1000;

  int16_t goalState = -1;
  for (;;) {
    uint32_t best = UINT32_MAX;
    int16_t u = -1;
    for (uint16_t i = 0; i < n; i++)
      if (!done[i] && dist[i] < best) {
        best = dist[i];
        u = (int16_t)i;
      }
    if (u < 0) break;
    done[u] = true;
    int node = u / 4, h = u % 4, x = node % cols, y = node / cols;
    if (x == goalX && y == goalY) {
      goalState = u;
      break;
    }
    for (int d = 0; d < 4; d++) {
      if (d == (h + 2) % 4) continue;  // tidak putar balik
      int nx = x + DX[d], ny = y + DY[d];
      if (nx < 0 || ny < 0 || nx >= cols || ny >= rows || isBlocked(nx, ny)) continue;
      uint16_t v = stateOf(nx, ny, d);
      uint32_t c = best + 1000 + (d != h ? 1 : 0);  // sama panjang -> belok paling sedikit
      if (c < dist[v]) {
        dist[v] = c;
        prev[v] = u;
      }
    }
  }
  if (goalState < 0) return 0;

  // runut balik: urutan state dari simpul pertama sesudah start sampai tujuan
  static int16_t path[NSTATE];
  uint16_t len = 0;
  for (int16_t s = goalState; s >= 0; s = prev[s]) path[len++] = s;
  if (len > maxSteps) return 0;
  uint8_t count = 0;
  for (int k = len - 1; k >= 0; k--) {
    LfStep st = {};
    st.trigger = TRIG_JUNCTION;
    st.speed = speed;
    st.followMm = followMm;
    if (k == 0) {
      st.action = ACT_STOP;
    } else {
      int hin = path[k] % 4, hout = path[k - 1] % 4;
      if (hout == hin) st.action = ACT_FORWARD;
      else if (hout == (hin + 1) % 4) st.action = ACT_LEFT;  // timur -> utara = kiri
      else if (hout == (hin + 3) % 4) st.action = ACT_RIGHT;
      else st.action = ACT_UTURN;
    }
    out[count++] = st;
  }
  return count;
}
