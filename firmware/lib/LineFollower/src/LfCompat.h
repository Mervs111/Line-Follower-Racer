// LfCompat.h — penanda versi Arduino-ESP32 core.
// Core 3.x (dan sesudahnya) mengganti API LEDC dan PCNT; core 1.x belum punya makro versi (dianggap core lama).
#pragma once

#include <Arduino.h>

#if defined(ESP_ARDUINO_VERSION_MAJOR) && ESP_ARDUINO_VERSION_MAJOR >= 3
#define LF_CORE3 1
#else
#define LF_CORE3 0
#endif

#if defined(ESP_ARDUINO_VERSION_MAJOR)
#define LF_HAS_ADC_MV 1  // analogReadMilliVolts() ada sejak core 2.0
#else
#define LF_HAS_ADC_MV 0
#endif
