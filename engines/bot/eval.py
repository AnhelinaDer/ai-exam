from .material import get_material
import chess
from . import positions

MATE_SCORE = 100000

_MOBILITY_WEIGHT = 5
_BISHOP_PAIR_BONUS = 30
_CASTLE_BONUS = 20
_PAWN_SHIELD_BONUS = 5
_ISOLATED_PAWN_PENALTY = 10
_DOUBLED_PAWN_PENALTY = 15
_PASSED_PAWN_BONUS = 15

def _count_mobility(board, color):
    # Temporarily switch side-to-move to measure legal-move count.
    original_turn = board.turn
    board.turn = color
    mobility = board.legal_moves.count()
    board.turn = original_turn
    return mobility

def _pawn_files(pawn_squares):
    # Count pawns per file to detect doubled/isolated pawns.
    files = [0] * 8
    for sq in pawn_squares:
        files[chess.square_file(sq)] += 1
    return files

def _passed_pawns(board, color, pawn_squares, enemy_pawn_squares):
    # Passed pawn: no opposing pawn ahead on same/adjacent files.
    enemy_by_file = {}
    for sq in enemy_pawn_squares:
        file = chess.square_file(sq)
        enemy_by_file.setdefault(file, []).append(chess.square_rank(sq))

    passed = 0
    for sq in pawn_squares:
        file = chess.square_file(sq)
        rank = chess.square_rank(sq)
        forward = range(rank + 1, 8) if color == chess.WHITE else range(rank - 1, -1, -1)
        blocked = False
        for f in (file - 1, file, file + 1):
            if f < 0 or f > 7:
                continue
            ranks = enemy_by_file.get(f, [])
            for enemy_rank in ranks:
                if enemy_rank in forward:
                    blocked = True
                    break
            if blocked:
                break
        if not blocked:
            passed += 1

    return passed

def _pawn_structure_score(board):
    # Simple pawn structure terms: doubled/isolated penalties and passed bonuses.
    white_pawns = list(board.pieces(chess.PAWN, chess.WHITE))
    black_pawns = list(board.pieces(chess.PAWN, chess.BLACK))

    white_files = _pawn_files(white_pawns)
    black_files = _pawn_files(black_pawns)

    white_doubled = sum(max(0, count - 1) for count in white_files)
    black_doubled = sum(max(0, count - 1) for count in black_files)

    white_isolated = 0
    for file, count in enumerate(white_files):
        if count == 0:
            continue
        left = white_files[file - 1] if file > 0 else 0
        right = white_files[file + 1] if file < 7 else 0
        if left == 0 and right == 0:
            white_isolated += count

    black_isolated = 0
    for file, count in enumerate(black_files):
        if count == 0:
            continue
        left = black_files[file - 1] if file > 0 else 0
        right = black_files[file + 1] if file < 7 else 0
        if left == 0 and right == 0:
            black_isolated += count

    white_passed = _passed_pawns(board, chess.WHITE, white_pawns, black_pawns)
    black_passed = _passed_pawns(board, chess.BLACK, black_pawns, white_pawns)

    score = 0
    score -= white_doubled * _DOUBLED_PAWN_PENALTY
    score += black_doubled * _DOUBLED_PAWN_PENALTY
    score -= white_isolated * _ISOLATED_PAWN_PENALTY
    score += black_isolated * _ISOLATED_PAWN_PENALTY
    score += white_passed * _PASSED_PAWN_BONUS
    score -= black_passed * _PASSED_PAWN_BONUS
    return score

def _pawn_shield_bonus(board, color):
    # Award pawns in front of a castled king (basic pawn shield).
    king_square = board.king(color)
    if king_square is None:
        return 0

    if color == chess.WHITE:
        if king_square == chess.G1:
            shield_squares = [chess.F2, chess.G2, chess.H2]
        elif king_square == chess.C1:
            shield_squares = [chess.B2, chess.C2, chess.D2]
        else:
            shield_squares = []
    else:
        if king_square == chess.G8:
            shield_squares = [chess.F7, chess.G7, chess.H7]
        elif king_square == chess.C8:
            shield_squares = [chess.B7, chess.C7, chess.D7]
        else:
            shield_squares = []

    pawns = board.pieces(chess.PAWN, color)
    return sum(1 for sq in shield_squares if sq in pawns) # Number of pawns in shield squares

def _king_safety_score(board):
    # Castled king and pawn shield bonuses.
    score = 0
    white_king = board.king(chess.WHITE)
    black_king = board.king(chess.BLACK)

    if white_king in (chess.G1, chess.C1):
        score += _CASTLE_BONUS
    if black_king in (chess.G8, chess.C8):
        score -= _CASTLE_BONUS

    score += _pawn_shield_bonus(board, chess.WHITE) * _PAWN_SHIELD_BONUS
    score -= _pawn_shield_bonus(board, chess.BLACK) * _PAWN_SHIELD_BONUS
    return score

def get_evaluation(board, ply):
    # Positive scores favor White, negative scores favor Black.

    # Check for checkmate of the opponent
    if board.is_checkmate():
        if board.turn:
            return -MATE_SCORE + ply
        else:
            return MATE_SCORE - ply
    if board.is_stalemate():
            return 0
    if board.is_insufficient_material():
            return 0

    total_material = get_material(board)

    pawnsq = sum([positions.pawn[i] for i in board.pieces(chess.PAWN, chess.WHITE)])
    pawnsq = pawnsq + sum([-positions.pawn[chess.square_mirror(i)]
                        for i in board.pieces(chess.PAWN, chess.BLACK)])
    knightsq = sum([positions.knight[i] for i in board.pieces(chess.KNIGHT, chess.WHITE)])
    knightsq = knightsq + sum([-positions.knight[chess.square_mirror(i)]
                            for i in board.pieces(chess.KNIGHT, chess.BLACK)])
    bishopsq = sum([positions.bishop[i] for i in board.pieces(chess.BISHOP, chess.WHITE)])
    bishopsq = bishopsq + sum([-positions.bishop[chess.square_mirror(i)]
                            for i in board.pieces(chess.BISHOP, chess.BLACK)])
    rooksq = sum([positions.rook[i] for i in board.pieces(chess.ROOK, chess.WHITE)])
    rooksq = rooksq + sum([-positions.rook[chess.square_mirror(i)]
                        for i in board.pieces(chess.ROOK, chess.BLACK)])
    queensq = sum([positions.queen[i] for i in board.pieces(chess.QUEEN, chess.WHITE)])
    queensq = queensq + sum([-positions.queen[chess.square_mirror(i)]
                            for i in board.pieces(chess.QUEEN, chess.BLACK)])
    kingsq = sum([positions.king[i] for i in board.pieces(chess.KING, chess.WHITE)])
    kingsq = kingsq + sum([-positions.king[chess.square_mirror(i)]
                        for i in board.pieces(chess.KING, chess.BLACK)])

    mobility = (_count_mobility(board, chess.WHITE) - _count_mobility(board, chess.BLACK)) * _MOBILITY_WEIGHT
    bishop_pair = _BISHOP_PAIR_BONUS if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2 else 0
    bishop_pair -= _BISHOP_PAIR_BONUS if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2 else 0
    pawn_structure = _pawn_structure_score(board)
    king_safety = _king_safety_score(board)

    # Material + piece-square tables plus lightweight strategic terms.
    eval = total_material + pawnsq + knightsq + bishopsq + rooksq + queensq + kingsq
    eval += mobility + bishop_pair + pawn_structure + king_safety

    return eval
