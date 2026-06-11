import sys
from pathlib import Path
from loguru import logger

# Путь к логам: lwk/logs/lwk.log
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "lwk.log"

# Настраиваем loguru
logger.remove()  # Убираем стандартный вывод

# Вывод в консоль (для разработки)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
)

# Вывод в файл (для production)
logger.add(
    LOG_FILE,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="INFO",
    rotation="10 MB",  # Ротация при достижении 10 MB
    retention="7 days",  # Хранить логи 7 дней
    compression="zip",  # Сжимать старые логи
    encoding="utf-8",
)