from .eval import get_evaluation
import chess
import numpy as np

_PIECE_VALUES = {
  chess.PAWN: 100,
  chess.KNIGHT: 320,
  chess.BISHOP: 330,
  chess.ROOK: 500,
  chess.QUEEN: 900,
  chess.KING: 20000,
}

def _move_score(board, move):
  # Simple MVV-LVA (Most Valuable Victim - Least Valuable Attacker) + promotions + checks to improve alpha-beta cutoffs.
  score = 0

  if board.is_capture(move): 
    if board.is_en_passant(move): # python check for the special pawn capture where a pawn captures an adjacent pawn that just advanced two squares
      captured = chess.PAWN
    else:
      # Get the captured piece type.
      captured_piece = board.piece_at(move.to_square)
      captured = captured_piece.piece_type if captured_piece else chess.PAWN
    mover_piece = board.piece_at(move.from_square) # Get the moving piece type.
    mover = mover_piece.piece_type if mover_piece else chess.PAWN
    score += 1000 + _PIECE_VALUES[captured] - _PIECE_VALUES[mover]  # example: capturing a queen with a knight is worth 1000 + 900 - 320 = 1580

  # example: promotion to queen is worth 800 + 900 = 1700
  if move.promotion:
    score += 800 + _PIECE_VALUES[move.promotion]

  if board.gives_check(move):
    score += 50

  return score

def order_moves(board, moves):
  # Order moves high-to-low so strong moves are searched first.
  return sorted(moves, key=lambda move: _move_score(board, move), reverse=True)

_TT = {}

# Transposition table for caching previously searched positions.
def _tt_key(board):
  # Support different python-chess versions by falling back to a safe key.
  if hasattr(board, "transposition_key"):
    return board.transposition_key()
  if hasattr(board, "zobrist_hash"):
    return board.zobrist_hash()
  return board.fen()

def _tt_lookup(board, depth, alpha, beta):
  # Return cached bounds if this position was already searched.
  key = _tt_key(board)
  entry = _TT.get(key)
  if entry and entry["depth"] >= depth:
    if entry["flag"] == "exact":
      return entry["value"], alpha, beta, True
    if entry["flag"] == "lower":
      alpha = max(alpha, entry["value"])
    elif entry["flag"] == "upper":
      beta = min(beta, entry["value"])
    if alpha >= beta:
      return entry["value"], alpha, beta, True
  return None, alpha, beta, False

def _tt_store(board, depth, value, alpha, beta):
  # Store as exact value or a bound depending on the search window.
  if value <= alpha:
    flag = "upper"
  elif value >= beta:
    flag = "lower"
  else:
    flag = "exact"
  _TT[_tt_key(board)] = {
    "depth": depth,
    "value": value,
    "flag": flag,
  }

def quiescence(board, alpha, beta, maximizing_player, ply):
  # Extend search through capture sequences to avoid horizon effects.
  stand_pat = get_evaluation(board, ply)

  if maximizing_player:
    if stand_pat >= beta:
      return beta
    if stand_pat > alpha:
      alpha = stand_pat
  else:
    if stand_pat <= alpha:
      return alpha
    if stand_pat < beta:
      beta = stand_pat

  # Only search captures in quiescence to keep the tree small.
  capture_moves = [move for move in board.legal_moves if board.is_capture(move)]
  for move in order_moves(board, capture_moves):
    board.push(move)
    score = quiescence(board, alpha, beta, not maximizing_player, ply + 1)
    board.pop()

    if maximizing_player:
      if score > alpha:
        alpha = score
      if alpha >= beta:
        break
    else:
      if score < beta:
        beta = score
      if beta <= alpha:
        break

  return alpha if maximizing_player else beta

def minimax(board, depth, alpha, beta, maximizing_player, ply):
  # Alpha-beta minimax with a transposition table and quiescence at leaf nodes.
  if board.is_game_over():
    return get_evaluation(board, ply)
  if depth == 0:
    return quiescence(board, alpha, beta, maximizing_player, ply)

  cached, alpha, beta, hit = _tt_lookup(board, depth, alpha, beta)
  if hit:
    return cached
  
  if maximizing_player:
    alpha_orig = alpha
    beta_orig = beta
    max_eval = -np.inf
    for move in order_moves(board, board.legal_moves):
      board.push(move)
      eval = minimax(board, depth - 1, alpha, beta, False, ply + 1)
      board.pop()
      max_eval = max(max_eval, eval)
      alpha = max(alpha, eval)
      if beta <= alpha:
        break
    _tt_store(board, depth, max_eval, alpha_orig, beta_orig)
    return max_eval
  else:
    alpha_orig = alpha
    beta_orig = beta
    min_eval = np.inf
    for move in order_moves(board, board.legal_moves):
      board.push(move)
      eval = minimax(board, depth - 1, alpha, beta, True, ply + 1)
      board.pop()
      min_eval = min(min_eval, eval)
      beta = min(beta, eval)
      if beta <= alpha:
        break
    _tt_store(board, depth, min_eval, alpha_orig, beta_orig)
    return min_eval
