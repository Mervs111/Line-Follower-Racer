// Contoh blok Mind+ "path planning per indeks" (dibuat gen_contoh.mjs dari func.js; jangan diedit manual)
// Rute slide 8 deck pitching (= SLIDE_PLAN simulasi, lulus CoppeliaSim; = rute "Slide 8" di menu OLED).
// Tiap indeks = pemicu -> aksi -> ikuti garis sekian mm. Tombol apa pun saat jalan = batal.
#include <LineFollower.h>

LineFollower robot;

void setup() {
  robot.begin();
  robot.setPID(0.07, 3.5);
  while (!robot.buttonPressed(BTN_OK)) {
    yield();
  }
  robot.routeReset();
  robot.runIndex(TRIG_LEFT, ACT_LEFT, 120, 80, false);  // indeks 1
  robot.runIndex(TRIG_JUNCTION, ACT_RIGHT, 120, 80, false);  // indeks 2
  robot.runIndex(TRIG_JUNCTION, ACT_LEFT, 120, 80, false);  // indeks 3
  robot.runIndex(TRIG_JUNCTION, ACT_RIGHT, 120, 80, false);  // indeks 4
  robot.runIndex(TRIG_JUNCTION, ACT_LEFT, 120, 80, false);  // indeks 5
  robot.runIndex(TRIG_JUNCTION, ACT_STOP, 120, 80, false);  // indeks 6
  robot.beep(500);
}

void loop() {

}
