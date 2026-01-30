from flask import Flask, request, jsonify
import telebot
from telebot import types
import json
import os
import random
import string
import datetime
from threading import Thread

# --- CONFIGURATION ---
# 1. Get your Bot Token from BotFather
# 2. Add it to Render Environment Variables as 'BOT_TOKEN'
#    OR replace it directly here (Not recommended for public repos)
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '0'))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN env var is required")

# Initialize Apps
app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)

# --- SECURITY MIDDLEWARE ---
def _is_admin(user_id: int) -> bool:
    return ADMIN_ID == 0 or user_id == ADMIN_ID

@bot.message_handler(func=lambda message: not _is_admin(message.from_user.id))
def unauthorized_user(message):
    bot.reply_to(message, "⛔ **Access Denied**\n\nYou are not authorized to use this bot.", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: not _is_admin(call.from_user.id))
def unauthorized_callback(call):
    bot.answer_callback_query(call.id, "⛔ Access Denied")

# Storage (Note: On Render Free, this resets on restart! Use a DB for permanent storage)
KEYS_FILE = 'keys.json'
keys_db = {}

def load_keys():
    global keys_db
    try:
        if os.path.exists(KEYS_FILE):
            with open(KEYS_FILE, 'r') as f:
                keys_db = json.load(f)
    except:
        keys_db = {}

def save_keys():
    try:
        with open(KEYS_FILE, 'w') as f:
            json.dump(keys_db, f)
    except:
        pass

load_keys()

# --- UTILS ---
def generate_random_key(length=10):
    chars = string.ascii_uppercase + string.digits
    return 'STONEIOS-' + ''.join(random.choice(chars) for _ in range(length))

def get_expiry_date(days):
    if days >= 3000:
        return "Lifetime"
    exp = datetime.datetime.now() + datetime.timedelta(days=days)
    return exp.strftime("%Y-%m-%d")

# --- BOT INTERFACE ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_1day = types.KeyboardButton('🔑 Gen 1 Day (1 Device)')
    btn_1week = types.KeyboardButton('🔑 Gen 7 Days (1 Device)')
    btn_1month = types.KeyboardButton('🔑 Gen 30 Days (1 Device)')
    btn_global = types.KeyboardButton('🌍 Gen Global Key (Unlimited Devices)')
    btn_list = types.KeyboardButton('📋 List Keys')
    btn_custom = types.KeyboardButton('🛠 Custom Gen')

    # Management
    btn_ban = types.KeyboardButton('🚫 Ban Key')
    btn_reset = types.KeyboardButton('🔄 Reset HWID')
    btn_pause = types.KeyboardButton('⏸ Pause Key')
    btn_info = types.KeyboardButton('🔍 Check Key Stats')
    btn_buy = types.KeyboardButton('🛒 Buy Key')

    markup.add(btn_1day, btn_1week, btn_1month, btn_global, btn_list, btn_custom)
    markup.add(btn_ban, btn_reset, btn_pause, btn_info, btn_buy)
    
    bot.reply_to(message, "👋 Welcome to StoneiOS Cheats Manager!\nSelect an option below:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text.startswith('🔑 Gen'))
def quick_gen(message):
    days = 1
    if "7 Days" in message.text: days = 7
    if "30 Days" in message.text: days = 30
    
    create_key(message, days, 1)

@bot.message_handler(func=lambda message: message.text == '🌍 Gen Global Key (Unlimited Devices)')
def global_gen_menu(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_g_1day = types.KeyboardButton('🌍 Global 1 Day')
    btn_g_7days = types.KeyboardButton('🌍 Global 7 Days')
    btn_g_30days = types.KeyboardButton('🌍 Global 30 Days')
    btn_back = types.KeyboardButton('🔙 Back')
    markup.add(btn_g_1day, btn_g_7days, btn_g_30days, btn_back)
    
    bot.reply_to(message, "🌍 **Global Key Duration:**\nSelect how long this key should last:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text.startswith('🌍 Global'))
def global_gen_action(message):
    days = 1
    if "7 Days" in message.text: days = 7
    if "30 Days" in message.text: days = 30
    
    create_key(message, days, 999999)

@bot.message_handler(func=lambda message: message.text == '🔙 Back')
def back_to_main(message):
    send_welcome(message)

@bot.message_handler(func=lambda message: message.text == '📋 List Keys')
def list_keys_ui(message):
    if not keys_db:
        bot.reply_to(message, "📂 No active keys.")
        return
    
    msg = "📂 **Active Keys:**\n\n"
    for k, v in keys_db.items():
        status = "✅ Active" if v.get('status', 'active') == 'active' else "❌ Banned"
        users = len(v.get('used_hwids', []))
        max_users = v.get('max_devices', 1)
        max_str = "∞" if max_users > 900000 else str(max_users)
        
        msg += f"🔑 `{k}`\n⏳ {v['expiry']} | 👥 {users}/{max_str} | {status}\n/reset_{k} | /ban_{k} | /del_{k}\n\n"
    
    # Split message if too long
    if len(msg) > 4000:
        bot.reply_to(message, msg[:4000] + "...", parse_mode="Markdown")
    else:
        bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(regexp=r"^/reset_")
def reset_key(message):
    key = message.text.replace("/reset_", "")
    if key in keys_db:
        keys_db[key]['used_hwids'] = []
        save_keys()
        bot.reply_to(message, f"🔄 Key `{key}` devices have been RESET.\nIt can now be used on a new device.", parse_mode="Markdown")
    else:
        bot.reply_to(message, "Key not found.")

@bot.message_handler(func=lambda message: message.text == '🛠 Custom Gen')
def custom_gen_info(message):
    bot.reply_to(message, "To generate custom keys, use command:\n\n`/gen [days] [max_devices]`\n\nExample:\n`/gen 3 2` (3 Days, 2 Devices)\n`/gen 30 100` (30 Days, 100 Devices)", parse_mode="Markdown")

# --- MANAGEMENT HANDLERS ---
@bot.message_handler(func=lambda message: message.text == '🚫 Ban Key')
def ask_ban_key(message):
    msg = bot.reply_to(message, "🚫 **Ban Key Mode**\n\nPlease send the Key you want to BAN:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_ban_key)

def process_ban_key(message):
    if message.text == '🔙 Back' or message.text.startswith('/'):
        return # Avoid processing commands as keys
        
    key = message.text.strip()
    if key in keys_db:
        keys_db[key]['status'] = 'banned'
        save_keys()
        bot.reply_to(message, f"✅ Key `{key}` is now **BANNED**.", parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ Key not found in database.")

@bot.message_handler(func=lambda message: message.text == '🔄 Reset HWID')
def ask_reset_key(message):
    msg = bot.reply_to(message, "🔄 **Reset Device Mode**\n\nPlease send the Key to RESET devices for:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_reset_key)

def process_reset_key(message):
    if message.text == '🔙 Back' or message.text.startswith('/'):
        return 
        
    key = message.text.strip()
    if key in keys_db:
            keys_db[key]['used_hwids'] = []
            save_keys()
            bot.reply_to(message, f"✅ Devices for `{key}` have been **RESET**.", parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ Key not found.")

@bot.message_handler(func=lambda message: message.text == '⏸ Pause Key')
def ask_pause_key(message):
    msg = bot.reply_to(message, "⏸ **Pause Key Mode**\n\nPlease send the Key you want to PAUSE:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_pause_key)
    
def process_pause_key(message):
    if message.text == '🔙 Back' or message.text.startswith('/'):
        return
        
    key = message.text.strip()
    if key in keys_db:
        keys_db[key]['status'] = 'paused'
        save_keys()
        bot.reply_to(message, f"✅ Key `{key}` is now **PAUSED**.", parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ Key not found.")

@bot.message_handler(func=lambda message: message.text == '🔍 Check Key Stats')
def ask_key_info(message):
    msg = bot.reply_to(message, "🔍 **Check Key Stats**\n\nSend the Key to see how many users are using it:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_key_info)

def process_key_info(message):
    if message.text == '🔙 Back' or message.text.startswith('/'):
        return
        
    key = message.text.strip()
    if key in keys_db:
        v = keys_db[key]
        users_count = len(v.get('used_hwids', []))
        max_dev = v.get('max_devices', 1)
        
        msg = f"📊 **Key Statistics**\n\n"
        msg += f"🔑 `{key}`\n"
        msg += f"👥 **Online Users:** {users_count}\n"
        msg += f"📱 **Max Devices:** {'Unlimited' if max_dev > 900000 else max_dev}\n"
        msg += f"📅 **Expiry:** {v['expiry']}\n"
        msg += f"🔋 **Status:** {v.get('status', 'active').upper()}"
        
        bot.reply_to(message, msg, parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ Key not found.")

@bot.message_handler(func=lambda message: message.text == '🛒 Buy Key')
def buy_key_link(message):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("🛒 Buy Now", url="https://t.me/FAKHERDDIN5")
    markup.add(btn)
    bot.reply_to(message, "Click below to contact support and buy keys:", reply_markup=markup)

@bot.message_handler(commands=['gen'])
def command_gen(message):
    try:
        parts = message.text.split()
        days = int(parts[1]) if len(parts) > 1 else 1
        max_dev = int(parts[2]) if len(parts) > 2 else 1
        create_key(message, days, max_dev)
    except:
        bot.reply_to(message, "Usage: `/gen [days] [max_devices]`")

def create_key(message, days, max_devices):
    key = generate_random_key()
    expiry = get_expiry_date(days)
    
    keys_db[key] = {
        "expiry": expiry,
        "max_devices": max_devices,
        "used_hwids": [],
        "status": "active",
        "created_at": str(datetime.datetime.now())
    }
    save_keys()
    
    type_str = "Single User"
    if max_devices > 1: type_str = f"Multi-User ({max_devices})"
    if max_devices > 900000: type_str = "GLOBAL (Unlimited)"
    
    bot.reply_to(message, f"✅ **Key Generated!**\n\n🔑 Key: `{key}`\n⏳ Expires: {expiry}\n👥 Type: {type_str}\n\nCopy and send to user.", parse_mode="Markdown")

@bot.message_handler(regexp=r"^/ban_")
def ban_key(message):
    key = message.text.replace("/ban_", "")
    if key in keys_db:
        keys_db[key]['status'] = 'banned'
        save_keys()
        bot.reply_to(message, f"🚫 Key `{key}` has been BANNED.", parse_mode="Markdown")
    else:
        bot.reply_to(message, "Key not found.")

@bot.message_handler(regexp=r"^/del_")
def del_key(message):
    key = message.text.replace("/del_", "")
    if key in keys_db:
        del keys_db[key]
        save_keys()
        bot.reply_to(message, f"🗑 Key `{key}` DELETED.", parse_mode="Markdown")
    else:
        bot.reply_to(message, "Key not found.")

@bot.message_handler(func=lambda message: message.text and message.text.strip() in keys_db)
def auto_ban_pasted_key(message):
    key = message.text.strip()
    if keys_db[key].get('status') == 'banned':
        # If already banned, offer to unban
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("♻️ Unban Key", callback_data=f"unban_{key}")
        markup.add(btn)
        bot.reply_to(message, f"ℹ️ Key `{key}` is already **BANNED**.", reply_markup=markup, parse_mode="Markdown")
        return

    keys_db[key]['status'] = 'banned'
    save_keys()
    
    # Offer Unban option just in case
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("♻️ Mistake? Unban", callback_data=f"unban_{key}")
    markup.add(btn)
    
    bot.reply_to(message, f"🚫 **Key Automatically BANNED!**\n`{key}`\n\nUsers can no longer log in.", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('unban_'))
def callback_unban(call):
    key = call.data.replace("unban_", "")
    if key in keys_db:
        keys_db[key]['status'] = 'active'
        save_keys()
        bot.edit_message_text(f"✅ **Key Unbanned!**\n`{key}` is now Active.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        bot.answer_callback_query(call.id, "Key Unbanned")
    else:
        bot.answer_callback_query(call.id, "Key not found")


# --- API Logic ---
@app.route('/check', methods=['POST'])
def check_key():
    key = request.form.get('key')
    udid = request.form.get('udid')
    
    if not key or not udid:
        return jsonify({"status": "failed", "message": "Missing Data"})
    
    if key in keys_db:
        data = keys_db[key]
        
        # 1. Check Status
        status = data.get('status', 'active')
        if status == 'banned':
            return jsonify({"status": "failed", "message": "Key is BANNED"})
        if status == 'paused':
            return jsonify({"status": "failed", "message": "Key is PAUSED"})
            
        # 2. Check Expiry (Simple String Compare for now, can be improved)
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        if data['expiry'] != "Lifetime" and today > data['expiry']:
             return jsonify({"status": "failed", "message": "Key EXPIRED"})

        # 3. Check Device Lock
        used_list = data.get('used_hwids', [])
        max_dev = data.get('max_devices', 1)
        
        if udid in used_list:
            # Already authorized on this device
            return jsonify({"status": "success", "expiry": data['expiry'], "message": "Welcome Back"})
            
        # Not in list, check if room available
        if len(used_list) < max_dev:
            # Add device
            used_list.append(udid)
            keys_db[key]['used_hwids'] = used_list
            save_keys()
            return jsonify({"status": "success", "expiry": data['expiry'], "message": "Device Registered"})
        else:
            return jsonify({"status": "failed", "message": f"Max Devices Reached ({max_dev})"})
            
    return jsonify({"status": "failed", "message": "Invalid Key"})

@app.route('/')
def home():
    return "StoneiOS Cheats Server is Running!"

# --- RUNNER ---
def run_flask():
    # Helper to clean port execution
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # Start Flask in separate thread so Bot works too
    t = Thread(target=run_flask)
    t.start()
    
    # Start Polling
    bot.infinity_polling()