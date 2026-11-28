// Contoh blok Mind+ "ikuti garis sampai persimpangan" (dibuat gen_contoh.mjs dari func.js; jangan diedit manual)
// Tekan OK, robot mengikuti garis hitam; berhenti + bunyi di persimpangan pertama.
#include <LineFollower.h>

LineFollower robot;

void setup() {
  robot.begin();
  robot.setLineColor(true);
  if (!robot.isCalibrated()) {
    robot.calibrate(3000, true);
  }
  while (!robot.buttonPressed(BTN_OK)) {
    yield();
  }
}

void loop() {
  robot.follow(120, 0.07, 3.5);
  if (robot.junction()) {
    robot.stop();
    robot.beep(300);
    while (!robot.buttonPressed(BTN_OK)) {
      yield();
    }
    robot.forwardMm(90, 40);
  }
}
