# -*- coding: utf-8 -*-
"""
Локальный сервер для портфолио.
Запуск:  py server.py        (или python server.py)
         py server.py 9000   — указать другой порт
"""
import os
import sys
import webbrowser
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765


CODE_EXT = (".html", ".css", ".js")
MEDIA_EXT = (".mp4", ".mov", ".webm", ".m4v", ".png", ".jpg", ".jpeg", ".webp", ".gif")


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        path = self.path.split("?")[0].lower()
        if path.endswith(CODE_EXT) or path.endswith("/"):
            # код всегда ревалидируется → правки видны без Ctrl+F5
            # (no-cache != no-store: при отсутствии изменений вернётся быстрый 304)
            self.send_header("Cache-Control", "no-cache")
        elif path.endswith(MEDIA_EXT):
            # тяжёлые медиа кешируем — не перекачиваем при каждом заходе
            self.send_header("Cache-Control", "public, max-age=86400")
        super().end_headers()

    def log_message(self, fmt, *args):
        pass  # тихий лог


def main():
    os.chdir(ROOT)
    url = f"http://localhost:{PORT}"
    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), partial(Handler, directory=ROOT))

    print("\n  Портфолио запущено")
    print(f"  Открой:   {url}")
    print("  Остановить — Ctrl+C\n")

    try:
        webbrowser.open(url)
    except Exception:
        pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Остановлено.")
        httpd.server_close()


if __name__ == "__main__":
    main()
