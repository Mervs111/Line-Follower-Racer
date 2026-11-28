// SerialCommand.h — pembaca perintah baris dari Serial tanpa String dan tanpa alokasi dinamis.
// Satu baris (diakhiri Enter) dipecah per spasi menjadi argv[0..argc-1].
#pragma once

#include <Arduino.h>

class SerialCommand {
 public:
  static constexpr uint8_t MAX_LINE = 64;
  static constexpr uint8_t MAX_ARGS = 8;

  // Baca karakter yang tersedia. Return true kalau satu baris lengkap siap; argc/argv menunjuk ke buffer internal
  // yang berlaku sampai poll() berikutnya.
  bool poll(Stream& s, int& argc, char**& argv) {
    while (s.available() > 0) {
      char c = (char)s.read();
      if (c == '\r' || c == '\n') {
        if (len_ == 0) continue;  // baris kosong / pasangan \r\n
        line_[len_] = '\0';
        len_ = 0;
        argc = split();
        argv = args_;
        return argc > 0;
      }
      if (len_ < MAX_LINE - 1) line_[len_++] = c;
    }
    return false;
  }

 private:
  int split() {
    int n = 0;
    char* save = nullptr;
    for (char* tok = strtok_r(line_, " \t", &save); tok && n < MAX_ARGS; tok = strtok_r(nullptr, " \t", &save)) {
      args_[n++] = tok;
    }
    return n;
  }

  char line_[MAX_LINE];
  char* args_[MAX_ARGS];
  uint8_t len_ = 0;
};
