"""Find the chat ID to paste into Account -> Telegram chat ID (read-only).

Telegram will not reveal a chat id until a chat exists, so:

  1. Message your bot once (anything; `/start` is fine).
  2. Run this.

It calls the bot API's `getUpdates` and prints one line per chat that has
spoken to the bot. **The token is read from `TELEGRAM_BOT_TOKEN` and never
printed** - not in the output, not in an error, not in a traceback, because
this script's whole job is to be run while someone is watching the screen.

`getUpdates` returns only recent, undelivered updates and is mutually
exclusive with a webhook. If nothing appears, message the bot again and rerun.

Run:  .venv\\Scripts\\python scripts\\telegram_chat_id.py
"""

import os
import sys

import httpx
from dotenv import load_dotenv

API = "https://api.telegram.org/bot{token}/{method}"


def main() -> int:
    load_dotenv()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("TELEGRAM_BOT_TOKEN is not set - add it to .env (it is gitignored).")
        return 1

    try:
        who = httpx.get(API.format(token=token, method="getMe"), timeout=15)
        who.raise_for_status()
    except httpx.HTTPStatusError as exc:
        # The URL carries the token, so never let the default message through.
        print(f"bot API rejected the token (HTTP {exc.response.status_code}). "
              f"Check TELEGRAM_BOT_TOKEN in .env.")
        return 1
    except httpx.HTTPError:
        print("could not reach the bot API - network or DNS.")
        return 1

    bot = who.json().get("result", {})
    print(f"bot: @{bot.get('username')} ({bot.get('first_name')})\n")

    updates = httpx.get(API.format(token=token, method="getUpdates"), timeout=15)
    results = updates.json().get("result", [])
    seen = {}
    for update in results:
        message = (update.get("message") or update.get("edited_message")
                   or update.get("channel_post") or {})
        chat = message.get("chat") or {}
        if chat.get("id") is not None:
            seen[chat["id"]] = chat

    if not seen:
        print("No chats yet. Send your bot a message, then run this again.")
        print("(getUpdates only returns recent updates, and returns none at all "
              "while a webhook is registered.)")
        return 1

    print(f"{'chat id':>16}  {'type':<10} who")
    for chat_id, chat in seen.items():
        who_name = (chat.get("username") and f"@{chat['username']}") or " ".join(
            filter(None, [chat.get("first_name"), chat.get("last_name")])) or chat.get("title", "")
        print(f"{chat_id:>16}  {chat.get('type', ''):<10} {who_name}")
    print("\nPaste the chat id into Account -> Telegram chat ID, choose Telegram "
          "as the channel, tick opt-in, and save.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
