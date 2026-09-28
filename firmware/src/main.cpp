// main.cpp — test harness + perintah serial.
// M0: cek serial jalan dan LED WS2812 berkedip.
#include <Arduino.h>
#include <LineFollower.h>

LineFollower robot;

const uint32_t BLINK_INTERVAL_MS = 500;
uint32_t lastBlinkMs = 0;
bool ledOn = false;

void setup() {
  Serial.begin(115200);
  robot.begin();
  Serial.println("Line follower siap (M0). Ketik apa saja, akan dibalas.");
}

void loop() {
  // Kedip LED hijau tanpa delay()
  uint32_t now = millis();
  if (now - lastBlinkMs >= BLINK_INTERVAL_MS) {
    lastBlinkMs = now;
    ledOn = !ledOn;
    if (ledOn) {
      robot.led(0, 40, 0);
    } else {
      robot.led(0, 0, 0);
    }
  }

  // Echo serial: bukti komunikasi dua arah jalan
  while (Serial.available() > 0) {
    char c = Serial.read();
    Serial.write(c);
  }
}
