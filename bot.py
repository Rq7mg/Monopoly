import os
import json
import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters,
)

TOKEN = os.environ.get("TOKEN")
ADMIN_IDS = [6563936773, 6030484208]

BOARD = [
    "🏠 Başlangıç", "🛣️ Cadde1", "🛣️ Cadde2", "💰 Vergi", "🏢 Cadde3",
    "🎲 Şans", "🏢 Cadde4", "🏢 Cadde5", "🛣️ Cadde6", "🎲 Kasa",
    "🏠 Hapis", "🏢 Cadde7", "🛣️ Cadde8", "💰 Vergi", "🏢 Cadde9",
    "🎲 Şans", "🏢 Cadde10", "🏢 Cadde11", "🛣️ Cadde12", "🎲 Kasa",
    "🏠 Özel", "🏢 Cadde13", "🛣️ Cadde14", "💰 Vergi", "🏢 Cadde15",
    "🎲 Şans", "🏢 Cadde16", "🏢 Cadde17", "🛣️ Cadde18", "🎲 Kasa",
    "🏠 Hapis", "🏢 Cadde19", "🛣️ Cadde20", "💰 Vergi", "🏢 Cadde21",
    "🎲 Şans", "🏢 Cadde22", "🏢 Cadde23", "🛣️ Cadde24", "🎲 Kasa"
]

DATA_FILE = "game_data.json"

def load_game():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "players": {},
        "turn_order": [],
        "current_turn_index": 0,
        "board": BOARD,
        "started": False
    }

def save_game(game):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(game, f, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎲 Monopoly Bot Hazır!\n\n"
        "Komutlar:\n"
        ".join → Oyuna katıl\n"
        ".startgame → Admin oyunu başlatır\n"
        ".roll → Zar at / Hamleni yap\n"
        ".end → Admin oyunu bitir ve skorları göster"
    )

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = str(user.id)
    username = user.username or f"user{user_id}"

    game = load_game()

    if game["started"]:
        await update.message.reply_text("❌ Oyun zaten başladı!")
        return

    if user_id in game["players"]:
        await update.message.reply_text("❌ Zaten oyuna katıldın!")
        return

    game["players"][user_id] = {
        "username": username,
        "position": 0,
        "money": 1500,
        "properties": []
    }
    game["turn_order"].append(user_id)
    save_game(game)
    await update.message.reply_text(f"✅ {username} oyuna katıldı!")

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Sadece admin başlatabilir!")
        return

    game = load_game()
    if len(game["players"]) < 2:
        await update.message.reply_text("❌ En az 2 oyuncu olmalı!")
        return

    if game["started"]:
        await update.message.reply_text("❌ Oyun zaten başladı!")
        return

    game["started"] = True
    save_game(game)

    current_player_id = game["turn_order"][game["current_turn_index"]]
    current_player = game["players"][current_player_id]["username"]

    await update.message.reply_text(f"🎮 Oyun başladı! Sıra: @{current_player}")

async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = str(user.id)
    game = load_game()

    if not game["started"]:
        await update.message.reply_text("❌ Oyun başlamadı!")
        return

    current_player_id = game["turn_order"][game["current_turn_index"]]
    if user_id != current_player_id:
        await update.message.reply_text("❌ Sıra sende değil!")
        return

    roll_value = random.randint(1,6) + random.randint(1,6)
    player = game["players"][user_id]
    player["position"] = (player["position"] + roll_value) % len(BOARD)
    pos_name = BOARD[player["position"]]

    # Basit kira / sokak mantığı
    # Eğer başka biri mülk sahipse kira öde
    rent_paid = ""
    for pid, pdata in game["players"].items():
        if pid != user_id and pos_name in pdata["properties"]:
            player["money"] -= 50
            pdata["money"] += 50
            rent_paid = f" 💸 Kira ödendi @ {pdata['username']}"

    # Otomatik satın alma
    if pos_name.startswith("🏢") or pos_name.startswith("🛣️"):
        if pos_name not in player["properties"]:
            player["properties"].append(pos_name)
            player["money"] -= 100
            purchase_text = f" ✅ Sokak alındı: {pos_name}"
        else:
            purchase_text = ""
    else:
        purchase_text = ""

    # Tahta görünümü
    board_line = ""
    for i, square in enumerate(BOARD):
        token = ""
        for pid, pdata in game["players"].items():
            if pdata["position"] == i:
                token += f"👤"
        board_line += f"{square}{token} | "

    save_game(game)

    await update.message.reply_text(
        f"🎲 @{player['username']} zar attı: {roll_value}\n"
        f"Sıra: {BOARD[player['position']]} {rent_paid}{purchase_text}\n\n"
        f"{board_line}"
    )

    # Sıradaki oyuncuya geç
    game["current_turn_index"] = (game["current_turn_index"] + 1) % len(game["turn_order"])
    save_game(game)
    next_player_id = game["turn_order"][game["current_turn_index"]]
    next_player_name = game["players"][next_player_id]["username"]
    await update.message.reply_text(f"🕐 Sıra: @{next_player_name}")

async def end_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Sadece admin bitirebilir!")
        return

    game = load_game()
    if not game["started"]:
        await update.message.reply_text("❌ Oyun başlamadı!")
        return

    game["started"] = False
    save_game(game)

    scores = [(pdata["username"], pdata["money"]) for pdata in game["players"].values()]
    scores.sort(key=lambda x: x[1], reverse=True)
    msg = "🏆 Monopoly Sonuçları:\n\n"
    for i, (name, money) in enumerate(scores, 1):
        msg += f"{i}. {name} — {money}$\n"

    await update.message.reply_text(msg)

# ---------- MAIN ----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, join))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, roll))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start_game))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, end_game))
    print("🤖 Monopoly bot çalışıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()
