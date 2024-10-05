# utils.py

import math
import numpy as np  # For harmonic mean calculation

def eval_to_score(eval):
    """
    Converts a chess.engine.Score object to a centipawn score.
    Handles mate evaluations by assigning large positive or negative values.
    """
    if eval.is_mate():
        mate_in = eval.mate()
        # Assign a large positive or negative value for mate scores
        if mate_in > 0:
            return 100000  # Mate in N moves (winning)
        else:
            return -100000  # Getting mated in N moves (losing)
    else:
        return eval.score()

def winning_chances(cp):
    """
    Convert centipawn evaluation to a value between -1 and 1 representing win chances.
    Positive cp favors White; negative cp favors Black.
    """
    MULTIPLIER = -0.00368208  # Derived from empirical data
    value = 2 / (1 + math.exp(MULTIPLIER * cp)) - 1
    value = max(-1, min(1, value))  # Clamp between -1 and +1
    return value

def win_percent(cp):
    """
    Convert centipawn evaluation to win percentage between 0% and 100%.
    """
    chances = winning_chances(cp)
    win_percentage = 50 + 50 * chances
    win_percentage = max(0, min(100, win_percentage))  # Clamp between 0% and 100%
    return win_percentage

def accuracy_from_win_percents(before_win_percent, after_win_percent):
    """
    Compute the accuracy percentage for a move based on the change in win percentages.
    Uses an exponential decay function derived from Lichess's model.
    """
    if after_win_percent >= before_win_percent:
        return 100.0  # Perfect accuracy if the win percent did not decrease
    else:
        win_diff = before_win_percent - after_win_percent
        # Constants derived from Lichess's curve fitting
        a = 103.1668100711649
        k = 0.04354415386753951
        b = -3.166924740191411
        raw_accuracy = a * math.exp(-k * win_diff) + b + 1  # +1 uncertainty bonus
        accuracy = max(0.0, min(100.0, raw_accuracy))  # Clamp between 0 and 100
        return accuracy

def harmonic_mean(data):
    """
    Compute the harmonic mean of a list of numbers.
    Returns 0 if data is empty or contains zeros (to avoid division by zero).
    """
    if not data or any(a == 0 for a in data):
        return 0
    n = len(data)
    return n / sum(1 / a for a in data)
