# engine.py

import chess.engine
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Global variable for the engine in each worker
engine = None

def init_engine(stockfish_path):
    """
    Initializer for each worker process. Starts the Stockfish engine.
    
    Parameters:
    - stockfish_path (str): Path to the Stockfish executable.
    """
    global engine
    if not os.path.exists(stockfish_path):
        raise FileNotFoundError(f"Stockfish executable not found at {stockfish_path}")
    try:
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        # Set engine options here
        engine.configure({"Threads": 1, "Hash": 128})  # Example configuration
        logger.info("Stockfish engine initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Stockfish engine: {e}")
        raise

def close_engine():
    """
    Closes the Stockfish engine instance.
    """
    global engine
    if engine:
        try:
            engine.close()
            logger.info("Stockfish engine closed successfully.")
        except Exception as e:
            logger.error(f"Failed to close Stockfish engine: {e}")
        finally:
            engine = None
