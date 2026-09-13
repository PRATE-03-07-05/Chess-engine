## Installation

Run the following commands in a terminal:

```bash
git clone https://github.com/commonLuke/chess_engine.git
cd chess_engine
pip install -r requirements.txt
python game.py
```

## Lichess Bot

Use a separate Lichess account for the bot. Do not use engine assistance on
your normal human account games.

1. Create a Lichess API token with the `bot:play` scope:
   https://lichess.org/account/oauth/token

2. In PowerShell, set the token for the current terminal:

```powershell
$env:LICHESS_TOKEN = "paste_your_token_here"
```

3. Upgrade the separate account to a BOT account. This is irreversible:

```powershell
python lichess_bot.py --upgrade --yes-i-understand
```

4. Start the bot:

```powershell
python lichess_bot.py --depth 3 --quiescence-depth 4
```

By default, the bot accepts only casual standard chess challenges. To allow
rated challenges later, run:

```powershell
python lichess_bot.py --depth 3 --quiescence-depth 4 --allow-rated
```

Higher depth is stronger but slower. For quick games, try `--depth 2`; for slower
games, try `--depth 4`.
