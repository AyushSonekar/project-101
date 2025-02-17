import os
import logging

logger = logging.getLogger(__name__)

REQUIRED_DIRECTORIES = [
    'uploads',
    'barcodes',
    'clothing',
    'features'
]

def create_directories():
    """Create all required directories if they don't exist."""
    for directory in REQUIRED_DIRECTORIES:
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"Created directory: {directory}")
        except Exception as e:
            logger.error(f"Error creating directory {directory}: {str(e)}")
