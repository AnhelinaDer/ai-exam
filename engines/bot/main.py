import chess
import numpy as np

from .opening import play_opening
from .minimax import minimax, order_moves


def get_move(board, depth):
    # Opening book first; fall back to search if no book move is available.
    opening_move = play_opening(board)
    if opening_move:
        print("PLAYING OPENING MOVE: ", opening_move)
        return opening_move

    top_move = None

    # Opposite of our minimax
    if board.turn == chess.WHITE:
      top_eval = -np.inf
    else:
      top_eval = np.inf

    # Root search: score every legal move and keep the best by side to move.
    for move in order_moves(board, board.legal_moves):
        board.push(move)

        # WHEN WE ARE BLACK, WE WANT TRUE AND TO GRAB THE SMALLEST VALUE
        eval = minimax(board, depth - 1, -np.inf, np.inf, board.turn, 1)

        board.pop()

        if board.turn == chess.WHITE:
            if eval > top_eval:
                top_move = move
                top_eval = eval
        else:
            if eval < top_eval:
                top_move = move
                top_eval = eval

    print("CHOSEN MOVE: ", top_move, "WITH EVAL: ", top_eval)
    return top_move
