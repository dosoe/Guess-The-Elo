# engine.py

import chess.engine
import os

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
        # Optionally, set engine options here
        engine.configure({"Threads": 1, "Hash": 128})  # Example configuration
        print("Stockfish engine initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize Stockfish engine: {e}")
        raise

def close_engine():
    """
    Closes the Stockfish engine instance.
    """
    global engine
    if engine:
        try:
            engine.close()
            engine.quit()
            print("Stockfish engine closed successfully.")
        except Exception as e:
            print(f"Failed to close Stockfish engine: {e}")
