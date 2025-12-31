"""
Some example classes for people who want to create a homemade bot.

With these classes, bot makers will not have to implement the UCI or XBoard interfaces themselves.
"""
import chess
from chess.engine import PlayResult, Limit
import random
from lib.engine_wrapper import MinimalEngine
from lib.lichess_types import MOVE, HOMEMADE_ARGS_TYPE
import logging
from engines.bot.main import get_move
import time

# Use this logger variable to print messages to the console or log files.
# logger.info("message") will always print "message" to the console or log file.
# logger.debug("message") will only print "message" if verbose logging is enabled.
logger = logging.getLogger(__name__)


class ExampleEngine(MinimalEngine):
    """An example engine that all homemade engines inherit."""

class PyBot(ExampleEngine):
    def search(self, board: chess.Board, time_limit: Limit, ponder: bool, draw_offered: bool, root_moves: MOVE) -> PlayResult:
        print("GETTING MOVE!")

        max_depth = 4
        start_time = time.time()

        # Determine time budget
        if isinstance(time_limit.time, (int, float)):
            budget = max(0.05, time_limit.time)
        elif board.turn == chess.WHITE:
            budget = max(0.05, (time_limit.white_clock or 0) + (time_limit.white_inc or 0))
        else:
            budget = max(0.05, (time_limit.black_clock or 0) + (time_limit.black_inc or 0))

        # Keep a small buffer so we return before the hard limit.
        time_limit_sec = max(0.05, budget * 0.9)

        best_move = None
        for depth in range(1, max_depth + 1):
            if time.time() - start_time >= time_limit_sec:
                break
            best_move = get_move(board, depth)

        return PlayResult(best_move, None)
    
