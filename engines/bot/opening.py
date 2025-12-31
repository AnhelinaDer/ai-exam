import pandas as pd
import chess
import chess.pgn
import random
import os

_BOOK_CACHE = None


def play_opening(board):
    # Use cached opening book; return a weighted random book move if available.
    book = _load_opening_book()
    if not book:
        return None

    key = _book_key(board)
    next_moves = book.get(key)
    if not next_moves:
        return None

    weighted_moves = []
    weights = []
    for san, count in next_moves.items():
        try:
            uci = board.parse_san(san).uci()
        except Exception:
            continue
        weighted_moves.append(uci)
        weights.append(count)

    if not weighted_moves:
        return None

    return random.choices(weighted_moves, weights=weights, k=1)[0]

def _load_opening_book():
    # Build a mapping from position FEN to SAN move counts. FEN is a position; SAN is a move notation
    global _BOOK_CACHE
    if _BOOK_CACHE is not None:
        return _BOOK_CACHE

    current_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_directory, "openings.csv")

    chess_openings = pd.read_csv(file_path)
    moves_list = chess_openings["moves"].tolist()

    book = {}
    for opening in moves_list:
        moves_in_opening = opening.split()
        new_board = chess.Board()
        for move in moves_in_opening:
            key = _book_key(new_board)
            book.setdefault(key, {})
            book[key][move] = book[key].get(move, 0) + 1
            try:
                new_board.push_san(move)
            except Exception:
                break

    _BOOK_CACHE = book
    return _BOOK_CACHE

def _book_key(board):
    # Exclude move counters so keys match real-game positions.
    return f"{board.board_fen()} {board.turn} {board.castling_xfen()} {board.ep_square}"
