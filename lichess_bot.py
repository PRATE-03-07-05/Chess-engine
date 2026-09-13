import argparse
import json
import logging
import os
import time

import requests

from board import Board
from search import Search

try:
    import chess
except ImportError:
    chess = None


BASE_URL = "https://lichess.org"
FAST_SPEEDS = {"ultraBullet", "bullet", "blitz"}

PROMOTION_TO_ENGINE = {
    "n": 2,
    "b": 3,
    "r": 4,
    "q": 5,
}

ENGINE_TO_PROMOTION = {
    2: "n",
    3: "b",
    4: "r",
    5: "q",
}

CHESS_TO_ENGINE_PIECE = {
    "p": 1,
    "n": 2,
    "b": 3,
    "r": 4,
    "q": 5,
    "k": 6,
}


def require_python_chess():
    if chess is None:
        raise RuntimeError(
            "Missing dependency: python-chess. Run `python -m pip install -r requirements.txt`."
        )


def square_to_row_col(square_name):
    col = ord(square_name[0]) - ord("a")
    row = 8 - int(square_name[1])
    return row, col


def row_col_to_square(row, col):
    return f"{chr(ord('a') + col)}{8 - row}"


def uci_to_engine_move(uci):
    start_row, start_col = square_to_row_col(uci[:2])
    end_row, end_col = square_to_row_col(uci[2:4])
    promotion_piece = None

    if len(uci) == 5:
        promotion_piece = PROMOTION_TO_ENGINE[uci[4].lower()]

    return start_row, start_col, end_row, end_col, promotion_piece


def engine_move_to_uci(move):
    start_row, start_col, end_row, end_col, promotion_piece = move
    uci = row_col_to_square(start_row, start_col) + row_col_to_square(end_row, end_col)

    if promotion_piece is not None:
        uci += ENGINE_TO_PROMOTION[promotion_piece]

    return uci


def chess_square_to_row_col(square):
    require_python_chess()
    return 7 - chess.square_rank(square), chess.square_file(square)


def chess_board_from_moves(initial_fen, moves):
    require_python_chess()

    if not initial_fen or initial_fen == "startpos":
        board = chess.Board()
    else:
        board = chess.Board(initial_fen)

    for uci in moves.split():
        board.push_uci(uci)

    return board


def engine_board_from_chess(chess_board):
    require_python_chess()

    engine_board = Board()
    engine_board.state = [[0 for _ in range(8)] for _ in range(8)]

    for square, piece in chess_board.piece_map().items():
        row, col = chess_square_to_row_col(square)
        value = CHESS_TO_ENGINE_PIECE[piece.symbol().lower()]
        engine_board.state[row][col] = value if piece.color == chess.WHITE else -value

    if chess_board.ep_square is not None:
        row, col = chess_square_to_row_col(chess_board.ep_square)
        if engine_board.state[row][col] == 0:
            engine_board.state[row][col] = 7 if chess_board.turn == chess.BLACK else -7

    white_can_castle = (
        chess_board.has_kingside_castling_rights(chess.WHITE)
        or chess_board.has_queenside_castling_rights(chess.WHITE)
    )
    black_can_castle = (
        chess_board.has_kingside_castling_rights(chess.BLACK)
        or chess_board.has_queenside_castling_rights(chess.BLACK)
    )

    engine_board.white_king_moved = not white_can_castle
    engine_board.black_king_moved = not black_can_castle
    engine_board.white_rook_h_moved = not chess_board.has_kingside_castling_rights(chess.WHITE)
    engine_board.white_rook_a_moved = not chess_board.has_queenside_castling_rights(chess.WHITE)
    engine_board.black_rook_h_moved = not chess_board.has_kingside_castling_rights(chess.BLACK)
    engine_board.black_rook_a_moved = not chess_board.has_queenside_castling_rights(chess.BLACK)

    return engine_board


def side_to_engine_team(chess_board):
    require_python_chess()
    return 1 if chess_board.turn == chess.WHITE else -1


def choose_best_uci(chess_board, depth=3, verbose_search=False, quiescence_depth=4):
    require_python_chess()

    legal_moves = list(chess_board.legal_moves)
    if not legal_moves:
        return None, None

    team = side_to_engine_team(chess_board)
    engine_board = engine_board_from_chess(chess_board)
    search = Search(verbose=verbose_search, quiescence_depth=quiescence_depth)

    move_pairs = [(legal_move, uci_to_engine_move(legal_move.uci())) for legal_move in legal_moves]
    move_pairs.sort(key=lambda pair: search.move_order_score(engine_board, pair[1]), reverse=True)

    scored_moves = []
    for legal_move, engine_move in move_pairs:
        child_board = search.copy_board(engine_board)
        child_board.move_piece(*engine_move)

        score, _ = search.minmax(child_board, -team, max(0, depth - 1))

        if score is not None:
            scored_moves.append((score, legal_move.uci()))

    if not scored_moves:
        return legal_moves[0].uci(), None

    if team == 1:
        score, uci = max(scored_moves, key=lambda item: item[0])
    else:
        score, uci = min(scored_moves, key=lambda item: item[0])

    return uci, score


def iter_ndjson(response):
    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue

        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            logging.warning("Skipping invalid NDJSON line from Lichess: %s", line)


class LichessBot:
    def __init__(
        self,
        token,
        depth=3,
        quiescence_depth=4,
        allow_rated=False,
        allow_fast=False,
        base_url=BASE_URL,
        verbose_search=False,
    ):
        self.depth = depth
        self.quiescence_depth = quiescence_depth
        self.allow_rated = allow_rated
        self.allow_fast = allow_fast
        self.base_url = base_url.rstrip("/")
        self.verbose_search = verbose_search
        self.bot_id = None

        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def request(self, method, path, stream=False, **kwargs):
        headers = kwargs.pop("headers", {})
        if stream:
            headers["Accept"] = "application/x-ndjson"

        response = self.session.request(
            method,
            f"{self.base_url}{path}",
            headers=headers,
            stream=stream,
            timeout=(10, None) if stream else 30,
            **kwargs,
        )
        response.raise_for_status()
        return response

    def get_account(self):
        response = self.request("GET", "/api/account")
        return response.json()

    def upgrade_account(self):
        response = self.request("POST", "/api/bot/account/upgrade")
        return response.json()

    def run_forever(self):
        account = self.get_account()
        self.bot_id = account["id"].lower()
        logging.info("Logged in as %s", account.get("username", self.bot_id))

        while True:
            try:
                logging.info("Listening for Lichess challenges and game starts")
                with self.request("GET", "/api/stream/event", stream=True) as response:
                    for event in iter_ndjson(response):
                        self.handle_event(event)
            except KeyboardInterrupt:
                raise
            except requests.RequestException as exc:
                logging.warning("Event stream disconnected: %s. Reconnecting in 5 seconds.", exc)
                time.sleep(5)

    def handle_event(self, event):
        event_type = event.get("type")

        if event_type == "challenge":
            self.handle_challenge(event["challenge"])
        elif event_type == "gameStart":
            game_id = event.get("game", {}).get("id")
            if game_id:
                self.play_game(game_id)

    def handle_challenge(self, challenge):
        challenge_id = challenge["id"]
        challenger = challenge.get("challenger", {}).get("name", "unknown")
        accept, reason = self.should_accept_challenge(challenge)

        if accept:
            self.request("POST", f"/api/challenge/{challenge_id}/accept")
            logging.info("Accepted challenge from %s", challenger)
        else:
            data = {"reason": reason} if reason else None
            self.request("POST", f"/api/challenge/{challenge_id}/decline", data=data)
            logging.info("Declined challenge from %s: %s", challenger, reason or "generic")

    def should_accept_challenge(self, challenge):
        variant = challenge.get("variant", {}).get("key")
        if variant != "standard":
            return False, "variant"

        if challenge.get("rated") and not self.allow_rated:
            return False, "casual"

        if challenge.get("speed") in FAST_SPEEDS and not self.allow_fast:
            return False, "tooFast"

        return True, None

    def play_game(self, game_id):
        logging.info("Starting game %s", game_id)

        initial_fen = "startpos"
        bot_team = None
        played_positions = set()

        try:
            with self.request("GET", f"/api/bot/game/stream/{game_id}", stream=True) as response:
                for event in iter_ndjson(response):
                    event_type = event.get("type")
                    state = None

                    if event_type == "gameFull":
                        initial_fen = event.get("initialFen") or "startpos"
                        bot_team = self.get_bot_team(event)
                        state = event.get("state", {})

                        if bot_team is None:
                            logging.error("Bot account was not found in game %s", game_id)
                            return

                    elif event_type == "gameState":
                        state = event

                    if state is not None and bot_team is not None:
                        if self.game_is_finished(state):
                            logging.info("Game %s finished with status %s", game_id, state.get("status"))
                            return

                        self.play_if_my_turn(game_id, initial_fen, state, bot_team, played_positions)

        except requests.RequestException as exc:
            logging.warning("Game stream for %s disconnected: %s", game_id, exc)

    def get_bot_team(self, game_full_event):
        white_id = self.player_id(game_full_event.get("white", {}))
        black_id = self.player_id(game_full_event.get("black", {}))

        if white_id == self.bot_id:
            return 1
        if black_id == self.bot_id:
            return -1

        return None

    @staticmethod
    def player_id(player):
        return str(player.get("id") or player.get("name") or "").lower()

    @staticmethod
    def game_is_finished(state):
        status = state.get("status")
        return status not in (None, "created", "started")

    def play_if_my_turn(self, game_id, initial_fen, state, bot_team, played_positions):
        moves = state.get("moves", "")
        if moves in played_positions:
            return

        try:
            chess_board = chess_board_from_moves(initial_fen, moves)
        except Exception:
            logging.exception("Could not rebuild board for game %s", game_id)
            return

        if chess_board.is_game_over():
            return

        if side_to_engine_team(chess_board) != bot_team:
            return

        played_positions.add(moves)
        uci, score = choose_best_uci(
            chess_board,
            self.depth,
            self.verbose_search,
            self.quiescence_depth,
        )

        if uci is None:
            logging.info("No legal move available in game %s", game_id)
            return

        try:
            self.request("POST", f"/api/bot/game/{game_id}/move/{uci}")
            score_text = "unknown" if score is None else f"{score:.2f}"
            logging.info("Played %s in game %s with evaluation %s", uci, game_id, score_text)
        except requests.RequestException as exc:
            played_positions.discard(moves)
            logging.warning("Failed to play %s in game %s: %s", uci, game_id, exc)


def parse_args():
    parser = argparse.ArgumentParser(description="Run this chess engine as a Lichess bot.")
    parser.add_argument("--token", default=os.getenv("LICHESS_TOKEN"), help="Lichess API token with bot:play scope.")
    parser.add_argument("--depth", type=int, default=int(os.getenv("ENGINE_DEPTH", "3")), help="Search depth.")
    parser.add_argument(
        "--quiescence-depth",
        type=int,
        default=int(os.getenv("ENGINE_QUIESCENCE_DEPTH", "4")),
        help="Capture-search extension depth used at leaf nodes.",
    )
    parser.add_argument("--allow-rated", action="store_true", help="Accept rated challenges. Default is casual only.")
    parser.add_argument("--allow-fast", action="store_true", help="Accept blitz, bullet, and ultraBullet challenges.")
    parser.add_argument("--upgrade", action="store_true", help="Upgrade the token's account to a Lichess BOT account.")
    parser.add_argument(
        "--yes-i-understand",
        action="store_true",
        help="Required with --upgrade because Lichess BOT account upgrades are irreversible.",
    )
    parser.add_argument("--base-url", default=os.getenv("LICHESS_BASE_URL", BASE_URL), help="Lichess API base URL.")
    parser.add_argument("--verbose-search", action="store_true", help="Print every searched move and evaluation.")
    parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"), help="Python logging level.")
    return parser.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    if not args.token:
        raise SystemExit("Set LICHESS_TOKEN or pass --token with a Lichess token that has bot:play scope.")

    if args.depth < 1:
        raise SystemExit("--depth must be at least 1.")

    if args.quiescence_depth < 0:
        raise SystemExit("--quiescence-depth must be at least 0.")

    if chess is None:
        raise SystemExit("Missing dependency: python-chess. Run `python -m pip install -r requirements.txt`.")

    bot = LichessBot(
        token=args.token,
        depth=args.depth,
        quiescence_depth=args.quiescence_depth,
        allow_rated=args.allow_rated,
        allow_fast=args.allow_fast,
        base_url=args.base_url,
        verbose_search=args.verbose_search,
    )

    if args.upgrade:
        if not args.yes_i_understand:
            raise SystemExit("Add --yes-i-understand to confirm the irreversible Lichess BOT upgrade.")

        result = bot.upgrade_account()
        print(result)
        return

    bot.run_forever()


if __name__ == "__main__":
    main()
