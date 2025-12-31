Lichess Bot Search Pipeline and Evaluation with Minimax algorithm

Pipeline overview

    openings.csv
        |
        v
  Opening book (weighted)  -->  Alpha-beta search  -->  Evaluation
                                      |                    |
                                      |                    v
                                      |            material + PST
                                      |            + mobility
                                      |            + pawn structure
                                      |            + king safety
                                      |            + bishop pair
                                      v
                               Quiescence (captures)
                               + Transposition table

How the pipeline works (step-by-step)
- Opening book: at each move, the bot tries to match the current FEN against a
  cached book built from openings.csv. If a match is found, it chooses a book
  move weighted by frequency, otherwise it falls back to search.
- Search: the engine runs alpha-beta minimax. At the root it orders moves using
  a simple MVV-LVA + promotion + check heuristic so strong moves are searched first.
- Quiescence: when the normal depth limit is reached, the engine keeps searching
  only capture moves. This prevents "noisy" leaf nodes (tactical exchanges) from
  being evaluated too early.
- Evaluation: leaf positions are scored using material, piece-square tables, and
  strategic bonuses/penalties (mobility, pawn structure, king safety, bishop pair).
  Mate scores are depth-sensitive to prefer faster wins and delay losses.

How the minimax algorithm was improved (and why)
- Alpha-beta pruning: reduces the number of nodes searched by cutting off lines
  that cannot improve the current best score, enabling deeper search.
- Move ordering: searching likely best moves first increases alpha-beta cutoffs,
  which speeds up search and makes the same depth stronger.
- Quiescence search: extends tactical capture sequences at leaf nodes, reducing
  horizon effects and preventing unstable evaluations.
- Transposition table: caches evaluations of repeated positions so the engine
  does not re-search the same subtree multiple times.
- Depth-aware mate scoring: prefers faster mates and delays losses, improving
  practical play in tactical positions.

Concrete horizon-effect example (depth-4 vs quiescence)

Position (White to move):
FEN: r1bqk2r/pppp1ppp/2n2n2/4p3/1bB1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w kq - 4 6

Line (illustrative):
1. Bxf7+ Kxf7 2. Nxe5+ Nxe5 3. Qh5+ g6 4. Qxe5

Why depth-4 can fail:
- A depth-4 search can stop after 2...Nxe5 (the 4th ply), treating 1.Bxf7+ as
  favorable because the leaf evaluation still "looks" good for White.
- The true tactical outcome depends on the follow-up capture sequence that starts
  with 3.Qh5+ and 4.Qxe5. If the evaluation happens at a noisy capture node, the
  static score can be misleading.

How quiescence helps:
- At depth 0, quiescence extends the line through capture sequences, so it will
  continue after the noisy capture and account for the recaptures and material
  swing before returning a score. This reduces the horizon effect.

Evaluation terms (current)
- Material: primary measure of advantage; drives basic tactical correctness.
- Piece-square tables: rewards good piece placement and activity by square.
- Mobility: counts legal moves; active positions are usually stronger.
- Bishop pair: two bishops cooperate well in open positions.
- Pawn structure:
  - Isolated pawn penalty: weak pawns are hard to defend.
  - Doubled pawn penalty: reduced pawn mobility and structural weakness.
  - Passed pawn bonus: passed pawns can decide endgames.
- King safety:
  - Castling bonus: safer king, faster rook activation.
  - Pawn shield bonus: intact pawns in front of a castled king reduce threats.
- Mate scoring with depth: prefers faster mates and delays losing mates.

Improvement ideas
- Opening book weighting: use a frequency column or stronger source data.
- Evaluation tuning: adjust weights with self-play or external test suites.
- Endgame tables: add tablebases for exact results in 5-7 piece endings.
