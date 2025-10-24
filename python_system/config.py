import logging

logger = logging.getLogger(__name__)

logging.basicConfig(
    filename='system.log',
    level=logging.INFO,
    filemode='w',
)
