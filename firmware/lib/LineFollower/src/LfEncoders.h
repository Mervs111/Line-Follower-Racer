// LfEncoders.h — pembacaan encoder kuadratur kedua motor lewat PCNT (penghitung pulsa hardware ESP32).
// Bagian dalam library LineFollower; dari program pakai LineFollower::encoderLeft()/encoderRight().
#pragma once

#include <stdint.h>

namespace LfEncoders {

// Siapkan 2 unit PCNT (x4: kedua tepi A dan B) + timer 200 Hz yang mengumpulkan hitungan ke 32 bit.
bool begin();
// Hitungan sejak begin()/reset(), sudah memperhitungkan arah di RobotConfig.h (+ = maju).
void read(int32_t& left, int32_t& right);
void reset();

}  // namespace LfEncoders
