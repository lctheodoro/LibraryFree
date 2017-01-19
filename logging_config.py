import logging
import logging.handlers

def configure_logger(log_file):
    """Accepts a fully-qualified filename to the log file.

    Returns a fully-configured logger object.
    """
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    handler = logging.FileHandler('flask.log')
    log.addHandler(handler)
    logger = logging.getLogger()
    log_formatter = logging.Formatter('%(levelname)s %(asctime)s %(message)s')
    file_handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=1024*1024*5)
    #file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(log_formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    return logger
