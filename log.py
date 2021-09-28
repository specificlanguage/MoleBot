import datetime
import logging
import os


def init_logger():
    """Initializes the log files upon startup."""
    if not os.path.exists("logs/"):
        os.makedirs("logs/")

    logger = logging.getLogger()
    logger.setLevel(level=logging.INFO)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] - %(message)s", "%Y-%m-%d %H:%M:%S")
    date = datetime.date.today()

    # Creates debug file.
    if os.environ.get("debug", False):
        logger.setLevel(level=logging.DEBUG)
        handler = logging.FileHandler(filename=date.strftime("logs/%Y-%m-%d-debug.log"))
        handler.setLevel(level=logging.DEBUG)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Creates INFO stream.
    fhandler = logging.StreamHandler()
    fhandler.setLevel(level=logging.INFO)
    fhandler.setFormatter(formatter)
    logger.addHandler(fhandler)

    # Creates generic log file
    lhandler = logging.FileHandler(filename=date.strftime("logs/%Y-%m-%d.log"))
    lhandler.setLevel(level=logging.INFO)
    lhandler.setFormatter(formatter)
    logger.addHandler(lhandler)
