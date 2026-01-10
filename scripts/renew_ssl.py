"""
Скрипт для обновления SSL сертификата Let's Encrypt
Сертификаты Let's Encrypt действительны 90 дней, нужно обновлять
"""
import subprocess
import sys
from pathlib import Path
from config import settings

def renew_certificate():
    """Обновляет SSL сертификат"""
    print("="*70)
    print("🔄 ОБНОВЛЕНИЕ SSL СЕРТИФИКАТА")
    print("="*70)
    print()
    
    domain = settings.noip_hostname
    if not domain:
        print("❌ Ошибка: No-IP домен не настроен")
        sys.exit(1)
    
    print(f"🌐 Домен: {domain}")
    print()
    
    # Проверяем certbot
    try:
        result = subprocess.run(
            ["certbot", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        certbot_installed = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        certbot_installed = False
    
    if not certbot_installed:
        # Пробуем через Docker
        print("Используем certbot через Docker...")
        docker_cmd = [
            "docker", "run", "--rm",
            "-v", f"{Path.cwd()}/certs:/etc/letsencrypt",
            "-v", f"{Path.cwd()}/certs/lib:/var/lib/letsencrypt",
            "-p", "80:80",
            "certbot/certbot",
            "renew"
        ]
        
        try:
            result = subprocess.run(docker_cmd, check=True)
            if result.returncode == 0:
                print("✅ Сертификат успешно обновлен")
                return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("❌ Ошибка: certbot не найден")
            print("   Установите certbot или используйте Docker")
            return False
    
    # Используем локальный certbot
    try:
        print("Обновляем сертификат...")
        result = subprocess.run(
            ["certbot", "renew"],
            check=True
        )
        if result.returncode == 0:
            print("✅ Сертификат успешно обновлен")
            print()
            print("💡 Перезапустите веб-сервер для применения нового сертификата")
            return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при обновлении: {e}")
        return False
    except FileNotFoundError:
        print("❌ Ошибка: certbot не найден")
        return False
    
    return False

if __name__ == "__main__":
    if renew_certificate():
        print()
        print("✅ Готово!")
    else:
        print()
        print("❌ Не удалось обновить сертификат")
        sys.exit(1)

