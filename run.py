from app import manager
from logging_config import configure_logger


if __name__ == "__main__":
    configure_logger('access.log')
    manager.run()
