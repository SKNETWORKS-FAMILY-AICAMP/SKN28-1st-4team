import sys
from loguru import logger

from ...env import load_application_settings , ApplicationSettings


_configuered  = False 

def configure_logger( config: ApplicationSettings | None = load_application_settings() ) :
    """
    Configure the logger based on the provided application settings.
    If no settings are provided, the default settings will be used from the environment variables
    """
    global _configuered

    if  _configuered:
        return logger
    
    # loguru recommendations
    logger.remove()

    logger.add(
        sys.stderr,
        level=config.env,
        format=config.format,   
        enqueue=True,
    )

    _configuered = True

    return logger

    def get_logger() -> Logger:
        return logger



