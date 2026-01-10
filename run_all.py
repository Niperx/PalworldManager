"""
Запуск веб-сервера + Telegram бота (без No-IP логики).

Используется, когда:
- у вас уже есть белый IP и/или настроенный домен,
- вы НЕ хотите автоматически обновлять No-IP и URL бота.
"""
import multiprocessing
import signal
import sys
import time
from pathlib import Path

import uvicorn

from config import settings


def run_web_server():
    """Запуск веб-сервера (с SSL, если указаны пути в .env)."""
    ssl_keyfile = None
    ssl_certfile = None

    if settings.ssl_cert_path and settings.ssl_key_path:
        cert_path = Path(settings.ssl_cert_path)
        key_path = Path(settings.ssl_key_path)
        if cert_path.exists() and key_path.exists():
            ssl_certfile = str(cert_path)
            ssl_keyfile = str(key_path)

    ssl_kwargs = {}
    if ssl_keyfile and ssl_certfile:
        ssl_kwargs = {
            "ssl_keyfile": ssl_keyfile,
            "ssl_certfile": ssl_certfile,
        }

    uvicorn.run(
        "web_server:app",
        host=settings.web_server_host,
        port=settings.web_server_port,
        log_level="info",
        **ssl_kwargs,
    )


def run_bot():
    """Запуск Telegram бота без изменения URL (использует WEB_SERVER_URL из .env)."""
    from bot.main import main

    main()


def main():
    print("=" * 70)
    print("🚀 ЗАПУСК ВЕБ-СЕРВЕРА + БОТА (БЕЗ NO-IP)")
    print("=" * 70)
    print()

    processes: dict[str, multiprocessing.Process] = {}

    def cleanup(signum=None, frame=None):
        print("\n\n🛑 Остановка сервисов...")
        for name, process in processes.items():
            if process and process.is_alive():
                print(f"   Остановка {name}...")
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        # Шаг 1: веб-сервер
        print("📡 Шаг 1/2: Запуск веб-сервера...")
        processes["web"] = multiprocessing.Process(target=run_web_server, daemon=True)
        processes["web"].start()

        print(f"   Ожидание запуска сервера на порту {settings.web_server_port}...")
        time.sleep(3)

        if not processes["web"].is_alive():
            print("❌ Ошибка: веб-сервер не запустился")
            cleanup()
            return

        print(f"✅ Веб-сервер запущен на порту {settings.web_server_port}")
        print()

        # Шаг 2: бот
        print("🤖 Шаг 2/2: Запуск Telegram бота...")
        processes["bot"] = multiprocessing.Process(target=run_bot, daemon=True)
        processes["bot"].start()

        time.sleep(2)

        if not processes["bot"].is_alive():
            print("❌ Ошибка: бот не запустился")
            cleanup()
            return

        print("✅ Бот запущен")
        print()
        print("=" * 70)
        print("✅ ВСЁ ЗАПУЩЕНО УСПЕШНО!")
        print("=" * 70)
        print()
        print(f"🌐 Веб-сервер: {settings.web_server_url}")
        print("🤖 Telegram бот: запущен и работает")
        print()
        print("Нажмите Ctrl+C для остановки")
        print()

        while True:
            time.sleep(1)
            if processes["web"] and not processes["web"].is_alive():
                print("⚠️  Веб-сервер остановился")
                cleanup()
            if processes["bot"] and not processes["bot"].is_alive():
                print("⚠️  Бот остановился")
                cleanup()

    except KeyboardInterrupt:
        cleanup()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback

        traceback.print_exc()
        cleanup()


if __name__ == "__main__":
    main()


