from loguru import logger
import sys

logger.remove()
# logger.add(
#     "history.log",
#     format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} - {message}",
#     rotation="1 MB",
# )
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>",
    colorize=True,
)