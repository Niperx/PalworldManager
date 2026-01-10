"""
Скрипт для настройки SSL сертификата Let's Encrypt
"""
import subprocess
import sys
import os
from pathlib import Path
from config import settings

def check_certbot_installed():
    """Проверяет, установлен ли certbot"""
    try:
        result = subprocess.run(
            ["certbot", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def install_certbot_instructions():
    """Выводит инструкции по установке certbot"""
    print("="*70)
    print("📥 УСТАНОВКА CERTBOT")
    print("="*70)
    print()
    print("Certbot не установлен. Выберите способ установки:")
    print()
    print("Вариант 1: Через WSL (Windows Subsystem for Linux)")
    print("  1. Установите WSL: wsl --install")
    print("  2. В WSL выполните: sudo apt update && sudo apt install certbot")
    print()
    print("Вариант 2: Через Docker")
    print("  1. Установите Docker Desktop")
    print("  2. Используйте команду из скрипта (автоматически)")
    print()
    print("Вариант 3: Вручную на Linux сервере")
    print("  sudo apt update && sudo apt install certbot")
    print()
    print("="*70)

def get_certificate_standalone(domain, email=None):
    """
    Получает SSL сертификат через certbot в standalone режиме
    
    Args:
        domain: Домен для сертификата
        email: Email для уведомлений (опционально)
    
    Returns:
        bool: True если успешно
    """
    if not domain:
        print("❌ Ошибка: домен не указан")
        return False
    
    print(f"🔐 Получение SSL сертификата для {domain}...")
    print()
    print("⚠️  ВАЖНО:")
    print("  1. Убедитесь, что порт 80 открыт и доступен из интернета")
    print("  2. Остановите веб-сервер на время получения сертификата")
    print("  3. Домен должен указывать на ваш IP адрес")
    print()
    
    # Проверяем certbot
    if not check_certbot_installed():
        # Пробуем через Docker
        print("Пробуем использовать certbot через Docker...")
        docker_cmd = [
            "docker", "run", "--rm",
            "-v", f"{Path.cwd()}/certs:/etc/letsencrypt",
            "-v", f"{Path.cwd()}/certs/lib:/var/lib/letsencrypt",
            "-p", "80:80",
            "certbot/certbot",
            "certonly",
            "--standalone",
            "--non-interactive",
            "--agree-tos",
            "-d", domain
        ]
        
        if email:
            docker_cmd.extend(["--email", email])
        else:
            docker_cmd.append("--register-unsafely-without-email")
        
        try:
            print(f"Выполняем: {' '.join(docker_cmd)}")
            result = subprocess.run(docker_cmd, check=True)
            if result.returncode == 0:
                print("✅ Сертификат успешно получен через Docker")
                return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка при получении сертификата через Docker: {e}")
            install_certbot_instructions()
            return False
        except FileNotFoundError:
            print("❌ Docker не установлен")
            install_certbot_instructions()
            return False
    
    # Используем локальный certbot
    certbot_cmd = [
        "certbot",
        "certonly",
        "--standalone",
        "--non-interactive",
        "--agree-tos",
        "-d", domain
    ]
    
    if email:
        certbot_cmd.extend(["--email", email])
    else:
        certbot_cmd.append("--register-unsafely-without-email")
    
    try:
        print(f"Выполняем: {' '.join(certbot_cmd)}")
        result = subprocess.run(certbot_cmd, check=True)
        if result.returncode == 0:
            print("✅ Сертификат успешно получен")
            return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при получении сертификата: {e}")
        return False
    except FileNotFoundError:
        install_certbot_instructions()
        return False
    
    return False

def get_certificate_paths(domain):
    """Возвращает пути к сертификатам"""
    if not domain:
        return None, None
    
    # Сначала проверяем локальную папку archive (для Docker на Windows)
    # В Let's Encrypt файлы в live - это симлинки на archive
    # На Windows симлинки могут не работать, поэтому проверяем archive напрямую
    local_archive_dir = Path("certs") / "archive" / domain
    if local_archive_dir.exists():
        fullchain = local_archive_dir / "fullchain1.pem"
        privkey = local_archive_dir / "privkey1.pem"
        
        if fullchain.exists() and privkey.exists():
            return fullchain, privkey
    
    # Пробуем через live (может работать если симлинки поддерживаются)
    local_live_dir = Path("certs") / "live" / domain
    if local_live_dir.exists():
        cert_file = local_live_dir / "fullchain.pem"
        key_file = local_live_dir / "privkey.pem"
        try:
            if cert_file.exists() and key_file.exists():
                return cert_file, key_file
        except (OSError, PermissionError):
            pass
    
    # Стандартные пути Let's Encrypt на Linux
    cert_dir = Path("/etc/letsencrypt/live") / domain
    if cert_dir.exists():
        cert_file = cert_dir / "fullchain.pem"
        key_file = cert_dir / "privkey.pem"
        return cert_file, key_file
    
    # Возвращаем пути к archive (даже если файлы не найдены)
    return local_archive_dir / "fullchain1.pem", local_archive_dir / "privkey1.pem"

def main():
    """Главная функция"""
    print("="*70)
    print("🔐 НАСТРОЙКА SSL СЕРТИФИКАТА LET'S ENCRYPT")
    print("="*70)
    print()
    
    # Получаем домен из настроек No-IP
    domain = settings.noip_hostname
    
    if not domain:
        print("❌ Ошибка: No-IP домен не настроен")
        print("\n📝 Настройте в .env файле:")
        print("   NOIP_HOSTNAME=yourhostname.ddns.net")
        sys.exit(1)
    
    print(f"🌐 Домен: {domain}")
    print()
    
    # Запрашиваем email (опционально)
    email = input("Введите email для уведомлений (Enter для пропуска): ").strip()
    if not email:
        email = None
    
    print()
    print("⚠️  Перед продолжением:")
    print("  1. Убедитесь, что веб-сервер остановлен")
    print("  2. Порт 80 должен быть открыт и доступен из интернета")
    print("  3. Домен должен указывать на ваш IP адрес")
    print()
    
    confirm = input("Продолжить? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Отменено")
        sys.exit(0)
    
    print()
    
    # Получаем сертификат
    if get_certificate_standalone(domain, email):
        # Даем время на синхронизацию файлов из Docker
        import time
        time.sleep(2)
        
        # Пробуем найти сертификаты в разных местах
        cert_file, key_file = None, None
        
        # Используем функцию для поиска сертификатов (она проверит и live, и archive)
        cert_file, key_file = get_certificate_paths(domain)
        
        # Проверяем существование с обработкой ошибок доступа (симлинки на Windows)
        cert_exists = False
        key_exists = False
        try:
            if cert_file:
                cert_exists = cert_file.exists()
            if key_file:
                key_exists = key_file.exists()
        except (OSError, PermissionError) as e:
            # Если ошибка доступа (симлинки), проверяем archive напрямую
            archive_dir = Path("certs") / "archive" / domain
            if archive_dir.exists():
                fullchain_archive = archive_dir / "fullchain1.pem"
                privkey_archive = archive_dir / "privkey1.pem"
                if fullchain_archive.exists() and privkey_archive.exists():
                    cert_file = fullchain_archive
                    key_file = privkey_archive
                    cert_exists = True
                    key_exists = True
        
        if cert_file and key_file and cert_exists and key_exists:
            print()
            print("="*70)
            print("✅ СЕРТИФИКАТ УСПЕШНО ПОЛУЧЕН")
            print("="*70)
            print(f"📄 Сертификат: {cert_file}")
            print(f"🔑 Ключ: {key_file}")
            print()
            print("💡 Теперь можно запустить веб-сервер с SSL:")
            print("   python run_with_noip.py")
            print()
            print("🔄 Сертификат нужно обновлять каждые 90 дней")
            print("   Запустите: python scripts/renew_ssl.py")
        else:
            print()
            print("⚠️  Сертификат получен, но файлы не найдены в ожидаемом месте")
            print(f"   Проверьте папку: {Path('certs') / 'live' / domain}")
            print()
            print("💡 Сертификаты должны быть в:")
            print(f"   {Path('certs') / 'live' / domain / 'fullchain.pem'}")
            print(f"   {Path('certs') / 'live' / domain / 'privkey.pem'}")
            print()
            print("   Если файлы там есть, можно запустить веб-сервер:")
            print("   python run_with_noip.py")
    else:
        print()
        print("❌ Не удалось получить сертификат")
        print("   Проверьте настройки и попробуйте снова")

if __name__ == "__main__":
    main()

