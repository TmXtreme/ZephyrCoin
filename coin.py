import telebot
from telebot import types
from telebot.types import Message
import sqlite3
from flask import Flask, request
import threading

API_TOKEN = '7096464205:AAFbLbhSBEUtOucFAgJ7mpf-_HXjnan6K1Q'
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

@app.route('/')
def index():
    return 'Bot is running!'
    
# Database setup
conn = sqlite3.connect('zephyrcoin_users.db', check_same_thread=False)
cursor = conn.cursor()

# Create users table if it doesn't exist
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER,
    referrals INTEGER,
    referral_link TEXT,
    wallet_address TEXT
)''')
conn.commit()

# Constants
referral_bonus = 50
welcome_bonus = 100

# Placeholder function for checking if a user has joined the required channels/groups
def has_joined_required_channels(user_id):
    # Simulate a real check. Replace this with actual logic.
    # E.g., Use a database or a third-party service to check membership status.
    return True

# Function to initialize a user in the database
def init_user(user_id, referrer_id=None):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    if not user:
        referral_link = f'https://t.me/ZephyrCoinbot?start={user_id}'
        cursor.execute("INSERT INTO users (user_id, balance, referrals, referral_link, wallet_address) VALUES (?, ?, ?, ?, ?)",
                       (user_id, welcome_bonus, 0, referral_link, None))
        if referrer_id:
            cursor.execute("SELECT * FROM users WHERE user_id=?", (referrer_id,))
            referrer = cursor.fetchone()
            if referrer:
                new_balance = referrer[1] + referral_bonus
                new_referrals = referrer[2] + 1
                cursor.execute("UPDATE users SET balance=?, referrals=? WHERE user_id=?", (new_balance, new_referrals, referrer_id))
        conn.commit()

# Start command handler
@bot.message_handler(commands=['start'])
def referral_start(message):
    chat_id = message.chat.id
    referrer_id = message.text.split()[1] if len(message.text.split()) > 1 else None

    init_user(chat_id, referrer_id)

    bot.send_message(chat_id, "Welcome to the ZephyrCoin Airdrop Bot! Before joining the airdrop, you must join the following links:\n\n1. Join our [Telegram Channel](https://t.me/Zephyr_Coin)\n2. Join Our [Telegram Community](https://t.me/ZephyrCoin_chat)\n3. Follow us on: [Twitter or X](https://x.com/Zephyr_Coin)\n\nAfter joining, click the 'Joined' button below and get 100 ZephyrCoin for free.\n\nOne more thing that you can do is refer your friends or family to mine *ZephyrCoin*.", parse_mode='Markdown')

    markup = types.InlineKeyboardMarkup()
    join_button = types.InlineKeyboardButton("JOINED 🟢", callback_data='joined')
    markup.add(join_button)
    bot.send_message(chat_id, "Click the button once you have joined all the channels.", reply_markup=markup)

# Airdrop command handler
@bot.message_handler(commands=['airdrop'])
def airdrop_handler(message):
    chat_id = message.chat.id
    if has_joined_required_channels(chat_id):
        show_main_menu(chat_id)
    else:
        bot.send_message(chat_id, "You need to join all required channels first. Type /start to see the links.")

def show_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    profile_button = types.KeyboardButton("𝗣𝗿𝗼𝗳𝗶𝗹𝗲 👤")
    wallet_button = types.KeyboardButton("𝗦𝗲𝘁 𝗪𝗮𝗹𝗹𝗲𝘁 💰")
    withdraw_button = types.KeyboardButton("𝗪𝗶𝘁𝗵𝗱𝗿𝗮𝘄 💸")
    referrals_button = types.KeyboardButton("𝗥𝗲𝗳𝗲𝗿𝗿𝗮𝗹𝘀 👥")
    markup.add(profile_button, wallet_button)
    markup.add(withdraw_button, referrals_button)
    bot.send_message(chat_id, "𝗠𝗔𝗜𝗡 𝗠𝗘𝗡𝗨 📋:", reply_markup=markup)

# Handle text messages
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text.lower()

    if text == "𝗣𝗿𝗼𝗳𝗶𝗹𝗲 👤":
        show_profile(message)
    elif text == "𝗦𝗲𝘁 𝗪𝗮𝗹𝗹𝗲𝘁 💰":
        bot.send_message(chat_id, "Please enter your USDT wallet address:")
        cursor.execute("UPDATE users SET wallet_address=NULL WHERE user_id=?", (chat_id,))
        conn.commit()
    elif text == "𝗪𝗶𝘁𝗵𝗱𝗿𝗮𝘄 💸":
        bot.send_message(chat_id, "Withdrawal feature is coming soon. Please wait for the next update and for ZephyrCoin to be listed.")
    elif text == "𝗥𝗲𝗳𝗲𝗿𝗿𝗮𝗹𝘀 👥":
        show_referrals(chat_id)
    elif text == "back to main menu ↩️":
        show_main_menu(chat_id)
    else:
        cursor.execute("SELECT wallet_address FROM users WHERE user_id=?", (chat_id,))
        wallet_address = cursor.fetchone()[0]
        if wallet_address is None:
            if validate_usdt_wallet(text):
                cursor.execute("UPDATE users SET wallet_address=? WHERE user_id=?", (text, chat_id))
                conn.commit()
                bot.send_message(chat_id, f"Wallet address {text} has been set.")
            else:
                bot.send_message(chat_id, "Invalid USDT wallet address. Please enter a valid address.")
        else:
            bot.send_message(chat_id, "I didn't understand that. Please use the menu buttons.")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id

    if call.data == 'joined':
        if has_joined_required_channels(chat_id):
            bot.send_message(chat_id, "You have successfully joined the channels.")
            show_main_menu(chat_id)
        else:
            bot.send_message(chat_id, "We couldn't verify your join status. Please make sure you have joined all the channels and try again.")

# Update the function signature to accept a Message object
def show_profile(message: Message):
    chat_id = message.chat.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name if message.from_user.last_name else ''
    
    cursor.execute("SELECT * FROM users WHERE user_id=?", (chat_id,))
    user = cursor.fetchone()
    
    if user:
        full_name = f"{first_name} {last_name}" if last_name else first_name
        profile_info = (f"» 👤*User*: {full_name}\n"
                        f"» 💰*Balance*: {user[1]} ZephyrCoin\n"
                        f"» 🫂*Total Referrals*: {user[2]}\n"
                        f"» 🔗*Referral Link*: {user[3]}\n"
                        f"» 🛅*Wallet Address*: `{user[4] if user[4] else 'Not set'}`")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        back_button = types.KeyboardButton("Back to Main Menu ↩️")
        markup.add(back_button)
        bot.send_message(chat_id, profile_info, reply_markup=markup, parse_mode='Markdown')
    else:
        bot.send_message(chat_id, "You need to start the bot first by typing /start.")

def show_referrals(chat_id):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (chat_id,))
    user = cursor.fetchone()
    if user:
        referral_info = (f"REFERRALS 🫂:\n"
                         f"» 👥*Total Referrals*: {user[2]}\n"
                         f"» 🔗*Your Referral Link*: {user[3]}")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        back_button = types.KeyboardButton("Back to Main Menu ↩️")
        markup.add(back_button)
        bot.send_message(chat_id, referral_info, reply_markup=markup, parse_mode='Markdown')
    else:
        bot.send_message(chat_id, "You need to start the bot first by typing /start.")

def validate_usdt_wallet(wallet_address):
    # Check for ERC-20 address (starts with '0x' and is 42 characters long)
    if wallet_address.startswith('0x') and len(wallet_address) == 42:
        return True
    # Check for TRC-20 address (starts with 'T' and is 34 characters long)
    elif wallet_address.startswith('T') and len(wallet_address) == 34:
        return True
    return False

def run_bot():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    app.run(host='0.0.0.0', port=5000)