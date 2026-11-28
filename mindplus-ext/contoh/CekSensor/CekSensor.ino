// Contoh blok Mind+ "cek sensor dan baterai lewat serial" (dibuat gen_contoh.mjs dari func.js; jangan diedit manual)
// Kirim posisi garis, cabang kiri/kanan, dan tegangan baterai ke Serial Monitor (115200) tiap 0,1 s.
#include <LineFollower.h>

LineFollower robot;

void setup() {
  robot.begin();
  Serial.begin(115200);
}

void loop() {
  Serial.print(robot.position());
  Serial.print(" kiri=");
  Serial.print(robot.branchLeft());
  Serial.print(" kanan=");
  Serial.print(robot.branchRight());
  Serial.print(" S6=");
  Serial.print(robot.sensorValue(6));
  Serial.print(" bat=");
  Serial.println(robot.batteryVoltage());
  if (robot.batteryLow()) {
    robot.beep(50);
  }
  delay(100);
}
