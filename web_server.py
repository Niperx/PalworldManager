"""
Веб-сервер для Mini App Telegram бота
"""
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from palworld_api import PalworldAPI
from config import settings
import logging
import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Подавляем предупреждения asyncio о разорванных соединениях (нормальное поведение на Windows)
class AsyncioConnectionResetFilter(logging.Filter):
    """Фильтр для подавления ConnectionResetError в asyncio"""
    def filter(self, record):
        # Подавляем ошибки ConnectionResetError в asyncio
        if record.name == 'asyncio':
            msg = str(record.getMessage())
            exc_info = record.exc_info
            exc_text = ''
            
            # Проверяем traceback, если есть
            if exc_info and exc_info[1]:
                exc_text = str(exc_info[1])
            
            # Проверяем сообщение и traceback на наличие ConnectionResetError
            if ('ConnectionResetError' in msg or 'ConnectionResetError' in exc_text or
                'WinError 10054' in msg or 'WinError 10054' in exc_text or
                'Удаленный хост принудительно разорвал' in msg or
                'Удаленный хост принудительно разорвал' in exc_text or
                '_call_connection_lost' in msg or '_call_connection_lost' in exc_text):
                return False
        return True

# Применяем фильтр к логгеру asyncio
asyncio_logger = logging.getLogger('asyncio')
asyncio_logger.addFilter(AsyncioConnectionResetFilter())
asyncio_logger.setLevel(logging.CRITICAL)  # Устанавливаем CRITICAL, чтобы скрыть все кроме критических ошибок

app = FastAPI(title="Palworld Mini App")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Обслуживание статических файлов
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Инициализация API клиента
palworld_api = PalworldAPI(
    server_url=settings.palworld_server_url,
    admin_password=settings.palworld_admin_password
)

# Глобальное состояние автоматического выключения
auto_shutdown_state = {
    "active": False,
    "minutes": 30,
    "start_time": None,
    "target_time": None
}
auto_shutdown_lock = asyncio.Lock()



@app.get("/", response_class=HTMLResponse)
@app.head("/")
async def read_root():
    """Главная страница Mini App (поддерживает GET и HEAD запросы)"""
    import json
    with open("static/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
        
        # Вставляем список администраторов в JavaScript
        admin_usernames = settings.get_admin_usernames()
        admin_usernames_json = json.dumps(admin_usernames)  # Правильное преобразование в JSON
        
        # Заменяем константу ADMIN_USERNAMES в JavaScript
        html_content = html_content.replace(
            'const ADMIN_USERNAMES = [];',
            f'const ADMIN_USERNAMES = {admin_usernames_json};'
        )
        
        return HTMLResponse(content=html_content)


@app.get("/style.css")
async def get_css():
    """CSS файл"""
    return FileResponse("static/style.css", media_type="text/css")


@app.get("/app.js")
async def get_js():
    """JavaScript файл"""
    return FileResponse("static/app.js", media_type="application/javascript")


@app.get("/favicon.ico")
async def get_favicon():
    """Favicon"""
    return FileResponse("static/favicon.ico", media_type="image/x-icon")


@app.get("/api/server-info")
async def get_server_info():
    """API: Получить информацию о сервере"""
    try:
        info = await palworld_api.get_server_info()
        metrics = await palworld_api.get_metrics()
        players = await palworld_api.get_players()
        
        # Обработка данных - проверяем разные возможные структуры ответа
        # Иногда данные могут быть вложены в другие поля
        if isinstance(info, dict) and 'data' in info:
            info = info['data']
        if isinstance(metrics, dict) and 'data' in metrics:
            metrics = metrics['data']
        
        # Обработка списка игроков - такая же, как в get_players
        if isinstance(players, dict):
            if 'data' in players:
                players = players['data']
            elif 'players' in players:
                players = players['players']
            elif 'result' in players:
                players = players['result']
        
        # Убеждаемся, что players - это список
        if not isinstance(players, list):
            if isinstance(players, dict):
                # Если это словарь, пробуем извлечь значения
                players = list(players.values()) if players else []
            else:
                players = []
        
        return JSONResponse({
            "success": True,
            "data": {
                "info": info,
                "metrics": metrics,
                "players_count": len(players),
                "players": players
            }
        })
    except Exception as e:
        logger.error(f"Ошибка при получении информации о сервере: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )


@app.get("/api/players")
async def get_players():
    """API: Получить список игроков"""
    try:
        players = await palworld_api.get_players()
        
        # Обработка разных форматов ответа
        if isinstance(players, dict):
            if 'data' in players:
                players = players['data']
            elif 'players' in players:
                players = players['players']
            elif 'result' in players:
                players = players['result']
        
        if not isinstance(players, list):
            players = []
        
        return JSONResponse({
            "success": True,
            "data": players
        })
    except Exception as e:
        logger.error(f"Ошибка при получении списка игроков: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )


@app.post("/api/announce")
async def announce(request: Request):
    """API: Отправить объявление"""
    try:
        data = await request.json()
        message = data.get("message", "")
        
        if not message:
            return JSONResponse(
                {"success": False, "error": "Сообщение не может быть пустым"},
                status_code=400
            )
        
        await palworld_api.announce(message)
        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"Ошибка при отправке объявления: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )


@app.post("/api/kick")
async def kick_player(request: Request):
    """API: Выгнать игрока"""
    try:
        data = await request.json()
        userid = data.get("userid", "")
        message = data.get("message", "")
        
        if not userid:
            return JSONResponse(
                {"success": False, "error": "ID игрока не указан"},
                status_code=400
            )
        
        await palworld_api.kick_player(userid, message)
        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"Ошибка при кике игрока: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )


@app.post("/api/ban")
async def ban_player(request: Request):
    """API: Забанить игрока"""
    try:
        data = await request.json()
        userid = data.get("userid", "")
        
        if not userid:
            return JSONResponse(
                {"success": False, "error": "ID игрока не указан"},
                status_code=400
            )
        
        await palworld_api.ban_player(userid)
        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"Ошибка при бане игрока: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )


@app.post("/api/unban")
async def unban_player(request: Request):
    """API: Разбанить игрока"""
    try:
        data = await request.json()
        userid = data.get("userid", "")
        
        if not userid:
            return JSONResponse(
                {"success": False, "error": "ID игрока не указан"},
                status_code=400
            )
        
        await palworld_api.unban_player(userid)
        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"Ошибка при разбане игрока: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )


@app.post("/api/save")
async def save_world():
    """API: Сохранить мир"""
    try:
        await palworld_api.save_world()
        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"Ошибка при сохранении мира: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )


@app.post("/api/shutdown")
async def shutdown(request: Request):
    """API: Остановить сервер"""
    try:
        data = await request.json()
        waittime = data.get("waittime", 10)
        message = data.get("message", "")
        
        await palworld_api.shutdown(waittime=waittime, message=message)
        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"Ошибка при остановке сервера: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )


@app.post("/api/auto-shutdown")
async def set_auto_shutdown(request: Request):
    """API: Активировать/деактивировать автоматическое выключение"""
    try:
        data = await request.json()
        active = data.get("active", False)
        
        async with auto_shutdown_lock:
            if active:
                minutes = data.get("minutes", 30)
                if minutes < 1:
                    return JSONResponse(
                        {"success": False, "error": "Количество минут должно быть не менее 1"},
                        status_code=400
                    )
                
                auto_shutdown_state["active"] = True
                auto_shutdown_state["minutes"] = minutes
                auto_shutdown_state["start_time"] = datetime.now()
                auto_shutdown_state["target_time"] = datetime.now() + timedelta(minutes=minutes)
                
                logger.info(f"Автоматическое выключение активировано: {minutes} минут")
            else:
                auto_shutdown_state["active"] = False
                auto_shutdown_state["start_time"] = None
                auto_shutdown_state["target_time"] = None
                
                logger.info("Автоматическое выключение деактивировано")
        
        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"Ошибка при управлении автоматическим выключением: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )


@app.get("/api/auto-shutdown/status")
async def get_auto_shutdown_status():
    """API: Получить статус автоматического выключения"""
    try:
        async with auto_shutdown_lock:
            state = auto_shutdown_state.copy()
            
            # Преобразуем datetime объекты в строки или timestamps для JSON сериализации
            result_data = {
                "active": state["active"],
                "minutes": state["minutes"],
                "remaining_seconds": None
            }
            
            if state["active"] and state["target_time"]:
                remaining = (state["target_time"] - datetime.now()).total_seconds()
                if remaining < 0:
                    remaining = 0
                result_data["remaining_seconds"] = int(remaining)
            else:
                result_data["remaining_seconds"] = None
        
        return JSONResponse({
            "success": True,
            "data": result_data
        })
    except Exception as e:
        logger.error(f"Ошибка при получении статуса автоматического выключения: {e}")
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )


async def check_auto_shutdown():
    """Фоновая задача для проверки условий автоматического выключения"""
    while True:
        try:
            await asyncio.sleep(10)  # Проверяем каждые 10 секунд
            
            async with auto_shutdown_lock:
                if not auto_shutdown_state["active"]:
                    continue
                
                if not auto_shutdown_state["target_time"]:
                    continue
                
                # Проверяем наличие игроков
                try:
                    players = await palworld_api.get_players()
                    
                    # Обработка разных форматов ответа
                    if isinstance(players, dict):
                        if 'data' in players:
                            players = players['data']
                        elif 'players' in players:
                            players = players['players']
                        elif 'result' in players:
                            players = players['result']
                    
                    if not isinstance(players, list):
                        players = []
                    
                    # Если есть игроки, сбрасываем таймер (начинаем отсчёт заново)
                    if len(players) > 0:
                        logger.debug(f"Автоматическое выключение: на сервере {len(players)} игроков, таймер сброшен")
                        auto_shutdown_state["target_time"] = datetime.now() + timedelta(minutes=auto_shutdown_state["minutes"])
                        continue
                    
                    # Если игроков нет, проверяем, истекло ли время
                    if datetime.now() >= auto_shutdown_state["target_time"]:
                        logger.info("Автоматическое выключение: игроков нет, время истекло, выключаем сервер")
                        await palworld_api.shutdown(waittime=10, message="Автоматическое выключение: на сервере нет игроков")
                        
                        # Деактивируем автоматическое выключение
                        auto_shutdown_state["active"] = False
                        auto_shutdown_state["start_time"] = None
                        auto_shutdown_state["target_time"] = None
                    else:
                        # Игроков нет, но время ещё не истекло - просто ждём
                        remaining = (auto_shutdown_state["target_time"] - datetime.now()).total_seconds()
                        logger.debug(f"Автоматическое выключение: игроков нет, осталось {int(remaining)} секунд")
                except Exception as e:
                    logger.error(f"Ошибка при проверке игроков для автоматического выключения: {e}")
        except Exception as e:
            logger.error(f"Ошибка в фоновой задаче автоматического выключения: {e}")
            await asyncio.sleep(60)  # При ошибке ждём минуту перед следующей попыткой


@app.on_event("startup")
async def startup_event():
    """Запуск фоновых задач при старте приложения"""
    asyncio.create_task(check_auto_shutdown())






if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.web_server_host,
        port=settings.web_server_port
    )

