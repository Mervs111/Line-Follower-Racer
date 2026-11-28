// Contoh blok Mind+ "rute terpendek di grid" (dibuat gen_contoh.mjs dari func.js; jangan diedit manual)
// Grid 4 x 4 simpul, robot di (0,0) menghadap utara, tujuan (3,3), 3 simpul terhalang.
// Urutan indeks dibuat otomatis (Dijkstra, belok paling sedikit), lalu dijalankan.
#include <LineFollower.h>

LineFollower robot;

void setup() {
  robot.begin();
  robot.clearBlockedNodes();
  robot.blockNode(1, 0);
  robot.blockNode(2, 2);
  robot.blockNode(1, 2);
  while (!robot.buttonPressed(BTN_OK)) {
    yield();
  }
  robot.routeReset();
  robot.runShortestRoute(4, 4, 0, 0, 1, 3, 3, 120);
}

void loop() {

}
