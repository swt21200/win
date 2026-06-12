import telebot
import json
import os
import time
from datetime import datetime
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from flask import Flask
from threading import Thread

# ==================== CONFIGURATION ====================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

DB_DIR = os.environ.get("DB_DIR", "/data")
if not os.path.exists(DB_DIR):
    try:
        os.makedirs(DB_DIR)
    except:
        DB_DIR = "."
DB_FILE = os.path.join(DB_DIR, "user_secure_db.json")
# =======================================================

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running 24/7!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try: 
                data = json.load(f)
                if "approved_users" not in data: data["approved_users"] = {}
                if "user_states" not in data: data["user_states"] = {}
                if "keys_db" not in data: data["keys_db"] = {}
                return data
            except: 
                return get_default_db()
    return get_default_db()

def get_default_db():
    return {"approved_users": {}, "user_states": {}, "keys_db": {}}

def save_db(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"[-] DB Save Error: {e}")

def get_user_menu():
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_connect = KeyboardButton("📶 Wi-Fi စတင်ချိတ်ဆက်မည်")
    btn_help = KeyboardButton("❓ အသုံးပြုနည်း လမ်းညွှန်")
    markup.add(btn_connect, btn_help)
    return markup

def get_admin_menu():
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_approve = KeyboardButton("✅ User အား ခွင့်ပြုချက်ပေးမည် (Approve)")
    btn_block = KeyboardButton("❌ User အား အသုံးပြုခွင့်ပိတ်မည် (Block)")
    btn_add_key = KeyboardButton("🔑 Key နှင့် Link အသစ်ထည့်မည်")
    btn_view_keys = KeyboardButton("📋 သတ်မှတ်ထားသော Key များစာရင်း")
    btn_del_key = KeyboardButton("🗑️ Key နှင့် Link ပြန်ဖျက်မည်")
    btn_list = KeyboardButton("👤 ခွင့်ပြုထားသော User များစာရင်း")
    btn_exit = KeyboardButton("🚪 Admin Panel မှ ထွက်မည်")
    markup.add(btn_approve, btn_block, btn_add_key, btn_view_keys, btn_del_key, btn_list, btn_exit)
    return markup

def clear_user_chat_and_block(target_id):
    """ စာဟောင်းတွေအကုန်လုံး အပေါ်မြှုပ်သွားအောင် နေရာလွတ်တွေအများကြီးပို့ပြီး Tab ပါ ဖျက်ချပစ်တဲ့ စနစ် """
    blank_lines = "\n" * 80  # စာမျက်နှာအကျယ်ကြီးဖြစ်အောင် space ချပစ်ခြင်း
    block_text = (
        f"{blank_lines}"
        "🔒 **စနစ်ကို အသုံးပြုရန် ခွင့်ပြုချက် မရှိတော့ပါ**\n\n"
        "⚠️ **အကြောင်းကြားစာ:**\n"
        "Admin မှ သင့်အား အသုံးပြုခွင့် ပိတ်သိမ်းလိုက်ပြီ ဖြစ်သောကြောင့် Bot အတွင်းရှိ စာများနှင့် စနစ်များအားလုံးကို ဆက်လက်အသုံးပြုနိုင်တော့မည် မဟုတ်ပါ။"
    )
    try:
        bot.send_message(target_id, block_text, reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")
    except Exception as e:
        print(f"[-] Block Notification Error: {e}")

@bot.message_handler(commands=['start', 'help', 'admin'])
def send_welcome(message):
    chat_id = str(message.chat.id)
    db_data = load_db()
    db_data["user_states"][chat_id] = None
    save_db(db_data)

    if message.text == "/admin":
        db_data["user_states"][chat_id] = "AWAITING_ADMIN_PASSWORD"
        save_db(db_data)
        bot.send_message(chat_id, "🔐 Admin Panel သို့ ဝင်ရောက်ရန် Password ရိုက်ထည့်ပေးပါ...", reply_markup=ReplyKeyboardRemove())
        return
    
    if chat_id in db_data.get("approved_users", {}):
        welcome_text = f"👋 မင်္ဂလာပါ {db_data['approved_users'][chat_id]['name']}၊ Wi-Fi ချိတ်ဆက်ပေးမည့်စနစ်မှ ကြိုဆိုပါတယ်။"
        bot.send_message(chat_id, welcome_text, reply_markup=get_user_menu())
    else:
        pending_text = (
            "🔒 **စနစ်ကို အသုံးပြုရန် ခွင့်ပြုချက် လိုအပ်ပါသည်**\n\n"
            f"👤 သင့်အမည်: `{message.from_user.first_name}`\n"
            f"🆔 သင့်ရဲ့ ID: `{chat_id}`\n\n"
            "⚠️ အထက်ပါ **ID** နှင့် **သင့်အမည်** ကို Admin ထံသို့ ပို့ပေးကာ အသုံးပြုခွင့် တောင်းခံပါ။"
        )
        bot.send_message(chat_id, pending_text, reply_markup=ReplyKeyboardRemove(), parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    chat_id = str(message.chat.id)
    user_text = message.text.strip()
    db_data = load_db()
    state = db_data["user_states"].get(chat_id)

    if state == "AWAITING_ADMIN_PASSWORD":
        if user_text == ADMIN_PASSWORD:
            db_data["user_states"][chat_id] = "ADMIN_MAIN"
            save_db(db_data)
            bot.send_message(chat_id, "🔓 Admin Access Granted!", reply_markup=get_admin_menu())
        else:
            db_data["user_states"][chat_id] = None
            save_db(db_data)
            bot.send_message(chat_id, "❌ စကားဝှက် မှားယွင်းပါသည်။", reply_markup=ReplyKeyboardRemove())
        return

    # Admin Panel Actions
    if state == "ADMIN_MAIN" or (state and state.startswith("AWAITING_")):
        if user_text == "✅ User အား ခွင့်ပြုချက်ပေးမည် (Approve)":
            db_data["user_states"][chat_id] = "AWAITING_APPROVE_ID"
            save_db(db_data)
            bot.send_message(chat_id, "🔑 User ရဲ့ Telegram ID ကို ရိုက်ထည့်ပါ...", reply_markup=ReplyKeyboardRemove())
            return
        elif user_text == "❌ User အား အသုံးပြုခွင့်ပိတ်မည် (Block)":
            db_data["user_states"][chat_id] = "AWAITING_BLOCK"
            save_db(db_data)
            bot.send_message(chat_id, "🚷 ပိတ်မည့် User ရဲ့ ID ကို ရိုက်ထည့်ပါ...", reply_markup=ReplyKeyboardRemove())
            return
        elif user_text == "🔑 Key နှင့် Link အသစ်ထည့်မည်":
            db_data["user_states"][chat_id] = "AWAITING_KEY_NAME"
            save_db(db_data)
            bot.send_message(chat_id, "🔑 ထည့်လိုသော Key ကို ရိုက်ထည့်ပါ...", reply_markup=ReplyKeyboardRemove())
            return
        elif user_text == "🗑️ Key နှင့် Link ပြန်ဖျက်မည်":
            db_data["user_states"][chat_id] = "AWAITING_KEY_DELETE"
            save_db(db_data)
            bot.send_message(chat_id, "🗑️ ဖျက်ချင်တဲ့ Key ကို ရိုက်ထည့်ပေးပါ...", reply_markup=ReplyKeyboardRemove())
            return
        elif user_text == "📋 သတ်မှတ်ထားသော Key များစာရင်း":
            keys = db_data.get("keys_db", {})
            txt = "📋 **Key များစာရင်း**:\n\n" + ("\n".join([f"🔑 `{k}`: {v}" for k,v in keys.items()]) if keys else "မရှိသေးပါ။")
            bot.send_message(chat_id, txt, parse_mode="Markdown", disable_web_page_preview=True)
            return
        elif user_text == "👤 ခွင့်ပြုထားသော User များစာရင်း":
            users = db_data.get("approved_users", {})
            if users:
                user_list = []
                for uid, info in users.items():
                    used_key = info.get("used_key", "မသုံးရသေးပါ")
                    join_date = info.get("date", "မသိရှိရပါ")
                    user_list.append(f"• ID: `{uid}`\n  👤 အမည်: {info['name']}\n  📅 စသုံးသည့်ရက်: `{join_date}`\n  🔑 သုံးထားသော Key: `{used_key}`\n")
                txt = "👤 **ခွင့်ပြုထားသော User များစာရင်း**:\n\n" + "\n".join(user_list)
            else:
                txt = "👤 **ခွင့်ပြုထားသော User များစာရင်း**:\n\nမရှိသေးပါ။"
            bot.send_message(chat_id, txt, parse_mode="Markdown")
            return
        elif user_text == "🚪 Admin Panel မှ ထွက်မည်":
            db_data["user_states"][chat_id] = None
            save_db(db_data)
            bot.send_message(chat_id, "🚪 Admin Panel မှ ထွက်ပြီးပါပြီ။", reply_markup=get_user_menu() if chat_id in db_data["approved_users"] else ReplyKeyboardRemove())
            return

        # Handle Admin Awaiting States
        if state == "AWAITING_KEY_DELETE":
            if user_text in db_data.get("keys_db", {}):
                del db_data["keys_db"][user_text]
                db_data["user_states"][chat_id] = "ADMIN_MAIN"
                save_db(db_data)
                bot.send_message(chat_id, f"✅ Key: `{user_text}` ကို အောင်မြင်စွာ ဖျက်လိုက်ပါပြီ။", reply_markup=get_admin_menu())
            else:
                bot.send_message(chat_id, "❌ အဆိုပါ Key ကို ရှာမတွေ့ပါ။", reply_markup=get_admin_menu())
            return
        if state == "AWAITING_APPROVE_ID":
            db_data["user_states"][chat_id] = f"AWAITING_APPROVE_NAME:{user_text}"
            save_db(db_data)
            bot.send_message(chat_id, f"👤 User ID: `{user_text}` အတွက် နာမည် ရိုက်ထည့်ပါ...")
            return
        if state and state.startswith("AWAITING_APPROVE_NAME:"):
            target_id = state.split(":")[1]
            # ရက်စွဲ၊ လ၊ ခုနှစ် အတိအကျကို format လုပ်ပြီး သိမ်းဆည်းခြင်း
            current_date = datetime.now().strftime("%d-%m-%Y")
            db_data["approved_users"][target_id] = {
                "name": user_text, 
                "date": current_date, 
                "used_key": "မသုံးရသေးပါ"
            }
            db_data["user_states"][chat_id] = "ADMIN_MAIN"
            save_db(db_data)
            bot.send_message(chat_id, f"✅ User {target_id} ကို ခွင့်ပြုလိုက်ပါပြီ။", reply_markup=get_admin_menu())
            try: bot.send_message(target_id, "🎉 သင့်ကို အသုံးပြုခွင့် ပေးလိုက်ပါပြီ။", reply_markup=get_user_menu())
            except: pass
            return
        if state == "AWAITING_KEY_NAME":
            db_data["user_states"][chat_id] = f"AWAITING_KEY_LINK:{user_text}"
            save_db(db_data)
            bot.send_message(chat_id, f"🔗 Key: `{user_text}` အတွက် Link ကို ထည့်ပါ...")
            return
        if state and state.startswith("AWAITING_KEY_LINK:"):
            key = state.split(":")[1]
            db_data["keys_db"][key] = user_text
            db_data["user_states"][chat_id] = "ADMIN_MAIN"
            save_db(db_data)
            bot.send_message(chat_id, "✅ သိမ်းဆည်းပြီးပါပြီ။", reply_markup=get_admin_menu())
            return
        if state == "AWAITING_BLOCK":
            if user_text in db_data["approved_users"]:
                del db_data["approved_users"][user_text]
                db_data["user_states"][user_text] = None # User state ကိုပါ ဖျက်ပေးခြင်း
                save_db(db_data)
                bot.send_message(chat_id, f"✅ User {user_text} ကို ပိတ်လိုက်ပါပြီ။", reply_markup=get_admin_menu())
                # စာတွေဖျက်၊ Tab ပိတ်မည့် Function ကို လှမ်းခေါ်ခြင်း
                clear_user_chat_and_block(user_text)
            else:
                bot.send_message(chat_id, "❌ အဆိုပါ User ID ကို ရှာမတွေ့ပါ။", reply_markup=get_admin_menu())
            return

    # User Actions
    if chat_id in db_data.get("approved_users", {}):
        if user_text == "📶 Wi-Fi စတင်ချိတ်ဆက်မည်":
            db_data["user_states"][chat_id] = "USER_INPUT_PASSWORD"
            save_db(db_data)
            bot.send_message(chat_id, "🔑 Admin ပေးထားသော Key ကို ရိုက်ထည့်ပါ...", reply_markup=ReplyKeyboardRemove())
        elif user_text == "❓ အသုံးပြုနည်း လမ်းညွှန်":
            bot.send_message(chat_id, "📌 Wi-Fi ချိတ်ဆက်ပြီး 'စတင်ချိတ်ဆက်မည်' ကိုနှိပ်ပါ။ Key ရိုက်ထည့်ပြီး Link ကို နှိပ်ပါ။")
        elif state == "USER_INPUT_PASSWORD":
            if user_text in db_data["keys_db"]:
                link = db_data["keys_db"][user_text]
                
                # သူသုံးလိုက်တဲ့ Key ကို ၎င်း User ရဲ့ အချက်အလက်ထဲမှာ သိမ်းလိုက်ခြင်း
                db_data["approved_users"][chat_id]["used_key"] = user_text
                db_data["user_states"][chat_id] = None
                save_db(db_data)
                
                bot.send_message(chat_id, f"✅ မှန်ကန်ပါသည်။\n\n[👉 ဤနေရာကိုနှိပ်ပါ 👈]({link})", parse_mode="Markdown", reply_markup=get_user_menu())
            else:
                bot.send_message(chat_id, "❌ Key မမှန်ပါ။ သေချာပြန်ရိုက်ပေးပါ သို့မဟုတ် /start ကိုနှိပ်ပါ။", reply_markup=get_user_menu())
                db_data["user_states"][chat_id] = None
                save_db(db_data)

def start_bot():
    print("[!] Cleaning up connections...")
    try:
        bot.delete_webhook()
        time.sleep(2)
    except: pass

    while True:
        try:
            print("[+] Bot is running...")
            bot.polling(none_stop=True, interval=1, timeout=60)
        except Exception as e:
            print(f"[-] Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    Thread(target=run_web_server, daemon=True).start()
    start_bot()

