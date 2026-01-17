import logging
import asyncio
import json
import os
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from uuid import uuid4
import time
from flask import Flask, request

# Flask app for webhook
flask_app = Flask(__name__)

# Settings - Use environment variables for security
BOT_TOKEN = os.environ.get('BOT_TOKEN', "8478077524:AAHlsbLLzUD83AvhmvszVapyxa0HX8fbaDA")
OWNER_ID = int(os.environ.get('OWNER_ID', "8076328865"))
FILES_BASE_URL = "https://t.me/Mind_spark_file_downloads_bot?start="
DEFAULT_DELETE_TIME = 0
FILES_DATA_FILE = "files_database.json"
USER_STATS_FILE = "user_stats.json"

# Force join channels - NEW CHANNELS
FORCE_JOIN_CHANNELS = [
    {
        "id": -1002656523143,
        "link": "https://t.me/Dream2k26madhyamik",
        "name": "Join 🔗"
    },
    {
        "id": -1003296338449,
        "link": "https://t.me/Madhyamik_Achievers",
        "name": "Join 🔗"
    },
    {
        "id": -1002576057549,
        "link": "https://t.me/Itzquiztimepro",
        "name": "Join 🔗"
    }
]

# Random welcome images
WELCOME_IMAGES = [
    "https://ibb.co/HLQV7pBx",
    "https://ibb.co/Q32C3cnv",
    "https://ibb.co/ccBB6ZvR",
    "https://ibb.co/PGHkm8X4",
    "https://ibb.co/bVpv72P",
    "https://ibb.co/99Jx60Fm",
    "https://ibb.co/gMQSbgbc"
]

# Source code button link
SOURCE_CODE_BUTTON_LINK = "https://t.me/+6lG7YsLD-0I4MWNl"
UPLOAD_BUTTON_LINK = "https://t.me/+VXWr7_UuS4kzNmZl"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Global variables
file_database = {}
user_stats = {}
bot_start_time = time.time()
application = None

def is_owner(user_id):
    return user_id == OWNER_ID

def load_files_data():
    global file_database
    try:
        if os.path.exists(FILES_DATA_FILE):
            with open(FILES_DATA_FILE, 'r', encoding='utf-8') as f:
                file_database = json.load(f)
            logger.info(f"Loaded {len(file_database)} files from database")
    except Exception as e:
        logger.error(f"Error loading file data: {e}")
        file_database = {}

def save_files_data():
    try:
        with open(FILES_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(file_database, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving file data: {e}")

def load_user_stats():
    global user_stats
    try:
        if os.path.exists(USER_STATS_FILE):
            with open(USER_STATS_FILE, 'r', encoding='utf-8') as f:
                user_stats = json.load(f)
            logger.info(f"Loaded {len(user_stats)} users from stats")
    except Exception as e:
        logger.error(f"Error loading user stats: {e}")
        user_stats = {}

def save_user_stats():
    try:
        with open(USER_STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving user stats: {e}")

def update_user_stats(user_id, username, first_name, last_name, file_id, action):
    try:
        if str(user_id) not in user_stats:
            user_stats[str(user_id)] = {
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'files_downloaded': {},
                'files_uploaded': [],
                'total_downloads': 0,
                'total_uploads': 0,
                'first_seen': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat(),
                'has_joined_channels': False,
                'last_verified': None,
                'is_owner': is_owner(user_id)
            }
        
        user_data = user_stats[str(user_id)]
        user_data['last_seen'] = datetime.now().isoformat()
        
        if action == 'download':
            if file_id not in user_data['files_downloaded']:
                user_data['files_downloaded'][file_id] = 0
            user_data['files_downloaded'][file_id] += 1
            user_data['total_downloads'] += 1
        elif action == 'upload':
            if file_id not in user_data['files_uploaded']:
                user_data['files_uploaded'].append(file_id)
                user_data['total_uploads'] += 1
        
        save_user_stats()
        
    except Exception as e:
        logger.error(f"Error updating user stats: {e}")

async def check_user_membership(user_id, context: CallbackContext):
    """Check if user has joined all required channels"""
    not_joined = []
    
    for channel in FORCE_JOIN_CHANNELS:
        try:
            member = await context.bot.get_chat_member(channel["id"], user_id)
            if member.status in ['left', 'kicked']:
                not_joined.append(channel)
        except:
            not_joined.append(channel)
    
    return not_joined

async def show_join_requirement(update: Update, context: CallbackContext, user_id, user):
    """Show join requirement WITHOUT welcome message"""
    # Create inline keyboard with THREE join buttons
    keyboard = []
    for channel in FORCE_JOIN_CHANNELS:
        keyboard.append([InlineKeyboardButton("Join 🔗", url=channel["link"])])
    
    keyboard.append([InlineKeyboardButton("✅ Verify Membership", callback_data="verify_membership")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🚫 *Access Denied!* 🚫\n\n"
        "✨ *Welcome to Mind Spark Store Bot!* ✨\n\n"
        "📢 *Before you can use this amazing bot, you must join our exclusive communities!*\n\n"
        "🔗 *Why join our channels?*\n"
        "• Get daily study materials and resources\n"
        "• Join a community of achievers\n"
        "• Access exclusive content and updates\n"
        "• Connect with like-minded students\n\n"
        "🎯 *How to proceed:*\n"
        "1. Click ALL THREE 'Join 🔗' buttons below\n"
        "2. Join each channel/group\n"
        "3. After joining ALL, click '✅ Verify Membership'\n\n"
        "⏳ *This only takes 30 seconds!*\n"
        "🔓 *Unlock unlimited file sharing once verified!*",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return False

async def show_welcome_after_verification(update: Update, context: CallbackContext, user_id, user):
    """Show welcome message AFTER verification"""
    # Select random welcome image
    random_image = random.choice(WELCOME_IMAGES)
    
    # Create reply keyboard
    keyboard = [
        ["📤 Upload File", "📥 Download File"],
        ["📁 My Uploads", "📊 My Stats"],
        ["🆔 My ID", "ℹ️ Help"]
    ]
    
    if is_owner(user_id):
        keyboard.append(["👑 Owner Panel"])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    # Check if user is returning
    user_data = user_stats.get(str(user_id), {})
    welcome_note = ""
    
    if user_data.get('total_downloads', 0) == 0 and user_data.get('total_uploads', 0) == 0:
        welcome_note = (
            "\n\n📝 *First Time User Note:*\n"
            "If this is your first time using this bot, you need to click "
            "on the link that brought you here. If you came directly to the "
            "bot, you can now start using all features by selecting options "
            "from the menu below."
        )
    else:
        welcome_note = "\n\n🎉 Welcome back! Your verification is complete. You can continue using all features."
    
    # Send welcome image
    await update.message.reply_photo(
        photo=random_image,
        caption=(
            "✨ *Welcome to Mind Spark Store Bot!* ✨\n\n"
            "✅ *Verification Successful!*\n\n"
            "🎉 *Congratulations! You're now part of our exclusive community!*\n\n"
            "🚀 *Now you can use all amazing features:*\n"
            "• Upload and share files instantly\n"
            "• Get permanent shareable links\n"
            "• Track your uploads and downloads\n"
            "• Access our educational resources\n\n"
            "📚 *Ready to start sharing?* Choose an option from the menu below:"
            + welcome_note
        ),
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = update.effective_user
    
    # IGNORE messages from groups - only respond in private
    if update.message.chat.type != 'private':
        return
    
    # Update user stats
    update_user_stats(
        user_id=user_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        file_id=None,
        action='start'
    )
    
    # If user has file ID in args (trying to download)
    if context.args:
        file_id = context.args[0]
        
        # First check membership
        not_joined = await check_user_membership(user_id, context)
        if not_joined:
            await show_join_requirement(update, context, user_id, user)
            return
        
        # User is verified, process file download WITH SOURCE CODE BUTTON
        await process_file_download(update, context, file_id, user_id, user)
        return
    
    # Regular start without file ID - check membership
    not_joined = await check_user_membership(user_id, context)
    if not_joined:
        await show_join_requirement(update, context, user_id, user)
        return
    
    # User has joined all channels - show welcome
    user_data = user_stats.get(str(user_id), {})
    user_data['has_joined_channels'] = True
    user_data['last_verified'] = datetime.now().isoformat()
    save_user_stats()
    
    # Show welcome with random image
    await show_welcome_after_verification(update, context, user_id, user)

async def process_file_download(update: Update, context: CallbackContext, file_id, user_id, user):
    """Process file download - SENDS FILE WITH SOURCE CODE BUTTON"""
    if file_id in file_database:
        file_info = file_database[file_id]
        file_type = file_info['type']
        caption = file_info.get('caption', '')
        
        # Increment download count
        if 'download_count' not in file_info:
            file_info['download_count'] = 0
        file_info['download_count'] += 1
        save_files_data()
        
        # Update user stats
        update_user_stats(
            user_id=user_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            file_id=file_id,
            action='download'
        )
        
        # ALWAYS SHOW SOURCE CODE BUTTON WITH EVERY FILE
        keyboard = [[InlineKeyboardButton("Join channel 📑", url=SOURCE_CODE_BUTTON_LINK)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send file with source code button
        try:
            if file_type == 'video':
                await update.message.reply_video(
                    file_info['file_id'], 
                    caption=f"{caption}" if caption else None,
                    reply_markup=reply_markup
                )
            elif file_type == 'document':
                await update.message.reply_document(
                    file_info['file_id'], 
                    caption=f"{caption}" if caption else None,
                    reply_markup=reply_markup
                )
            elif file_type == 'audio':
                await update.message.reply_audio(
                    file_info['file_id'], 
                    caption=f"{caption}" if caption else None,
                    reply_markup=reply_markup
                )
            elif file_type == 'photo':
                await update.message.reply_photo(
                    file_info['file_id'], 
                    caption=f"{caption}" if caption else None,
                    reply_markup=reply_markup
                )
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    else:
        await update.message.reply_text("❌ File not found!")

async def handle_video(update: Update, context: CallbackContext):
    # IGNORE messages from groups
    if update.message.chat.type != 'private':
        return
    await handle_file(update, context, 'video')

async def handle_document(update: Update, context: CallbackContext):
    # IGNORE messages from groups
    if update.message.chat.type != 'private':
        return
    await handle_file(update, context, 'document')

async def handle_audio(update: Update, context: CallbackContext):
    # IGNORE messages from groups
    if update.message.chat.type != 'private':
        return
    await handle_file(update, context, 'audio')

async def handle_photo(update: Update, context: CallbackContext):
    # IGNORE messages from groups
    if update.message.chat.type != 'private':
        return
    await handle_file(update, context, 'photo')

async def handle_file(update: Update, context: CallbackContext, file_type: str):
    user_id = update.effective_user.id
    
    # Check membership for non-owner
    if not is_owner(user_id):
        not_joined = await check_user_membership(user_id, context)
        if not_joined:
            await show_join_requirement(update, context, user_id, update.effective_user)
            return
    
    # Get file ID based on type
    file_id = None
    if file_type == 'video':
        file_id = update.message.video.file_id
    elif file_type == 'document':
        file_id = update.message.document.file_id
    elif file_type == 'audio':
        file_id = update.message.audio.file_id
    elif file_type == 'photo':
        file_id = update.message.photo[-1].file_id
    
    # Generate unique ID for the file
    file_unique_id = str(uuid4())[:8]
    caption = update.message.caption or ""
    
    # Store file info
    file_database[file_unique_id] = {
        'file_id': file_id,
        'type': file_type,
        'caption': caption,
        'uploader_id': user_id,
        'uploader_name': update.effective_user.username or update.effective_user.first_name,
        'created_at': datetime.now().isoformat(),
        'download_count': 0
    }
    
    save_files_data()
    
    # Update user stats
    update_user_stats(
        user_id=user_id,
        username=update.effective_user.username,
        first_name=update.effective_user.first_name,
        last_name=update.effective_user.last_name,
        file_id=file_unique_id,
        action='upload'
    )
    
    # Generate shareable link
    file_link = f"{FILES_BASE_URL}{file_unique_id}"
    
    # Send confirmation message with JOIN CHANNEL BUTTON
    keyboard = [
        [InlineKeyboardButton("Join channel 🔗", url=UPLOAD_BUTTON_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ *Upload Complete!*\n\n"
        f"🔗 *Shareable Link:*\n`{file_link}`\n\n"
        f"📝 *Caption:* {caption if caption else 'No caption'}\n\n"
        f"💡 *Click the link to download the file*\n\n"
        f"🎯 *Share with friends and help them learn!*",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data == "verify_membership":
        # Check membership
        not_joined = await check_user_membership(user_id, context)
        
        if not_joined:
            # Still not joined all channels
            keyboard = []
            for channel in FORCE_JOIN_CHANNELS:
                if channel in not_joined:
                    keyboard.append([InlineKeyboardButton("Join 🔗", url=channel["link"])])
            
            keyboard.append([InlineKeyboardButton("🔄 Verify Again", callback_data="verify_membership")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "❌ *Verification Failed!* ❌\n\n"
                "You haven't joined all channels yet!\n\n"
                "📋 *Channels still pending:*\n"
                f"{len(not_joined)} out of {len(FORCE_JOIN_CHANNELS)} channels\n\n"
                "👉 *Please click the buttons below to join remaining channels*\n"
                "👉 *Then click '🔄 Verify Again'*",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            # Successfully joined all channels
            user_data = user_stats.get(str(user_id), {})
            user_data['has_joined_channels'] = True
            user_data['last_verified'] = datetime.now().isoformat()
            save_user_stats()
            
            # Delete verification message
            await query.message.delete()
            
            # Show welcome with random image using query.message (not update)
            random_image = random.choice(WELCOME_IMAGES)
            
            # Create reply keyboard
            keyboard = [
                ["📤 Upload File", "📥 Download File"],
                ["📁 My Uploads", "📊 My Stats"],
                ["🆔 My ID", "ℹ️ Help"]
            ]
            
            if is_owner(user_id):
                keyboard.append(["👑 Owner Panel"])
            
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            # Check if user is returning
            welcome_note = ""
            if user_data.get('total_downloads', 0) == 0 and user_data.get('total_uploads', 0) == 0:
                welcome_note = (
                    "\n\n📝 *First Time User Note:*\n"
                    "If this is your first time using this bot, you need to click "
                    "on the link that brought you here. If you came directly to the "
                    "bot, you can now start using all features by selecting options "
                    "from the menu below."
                )
            else:
                welcome_note = "\n\n🎉 Welcome back! Your verification is complete. You can continue using all features."
            
            await context.bot.send_photo(
                chat_id=user_id,
                photo=random_image,
                caption=(
                    "✨ *Welcome to Mind Spark Store Bot!* ✨\n\n"
                    "✅ *Verification Successful!*\n\n"
                    "🎉 *Congratulations! You're now part of our exclusive community!*\n\n"
                    "🚀 *Now you can use all amazing features:*\n"
                    "• Upload and share files instantly\n"
                    "• Get permanent shareable links\n"
                    "• Track your uploads and downloads\n"
                    "• Access our educational resources\n\n"
                    "📚 *Ready to start sharing?* Choose an option from the menu below:"
                    + welcome_note
                ),
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    # Owner panel buttons
    elif data == "owner_panel":
        if not is_owner(user_id):
            await query.answer("Owner access required!", show_alert=True)
            return
        
        keyboard = [
            [InlineKeyboardButton("📊 Bot Statistics", callback_data="bot_stats")],
            [InlineKeyboardButton("👥 User Management", callback_data="user_management")],
            [InlineKeyboardButton("📁 File Management", callback_data="file_management")],
            [InlineKeyboardButton("📢 Broadcast Message", callback_data="broadcast_message")],
            [InlineKeyboardButton("📤 Export Data", callback_data="export_data")],
            [InlineKeyboardButton("🔄 Reset Bot", callback_data="reset_bot")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "👑 *Owner Panel* 👑\n\n"
            "✨ *Mind Spark Store Bot Admin*\n\n"
            "Select an option:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "bot_stats":
        if not is_owner(user_id):
            await query.answer("Owner access required!", show_alert=True)
            return
        
        total_users = len(user_stats)
        total_files = len(file_database)
        total_downloads = sum(user_data.get('total_downloads', 0) for user_data in user_stats.values())
        verified_users = sum(1 for user_data in user_stats.values() if user_data.get('has_joined_channels', False))
        
        # Calculate bot uptime
        uptime_seconds = int(time.time() - bot_start_time)
        uptime_str = f"{uptime_seconds // 86400}d {(uptime_seconds % 86400) // 3600}h"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="owner_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📊 *Bot Statistics*\n\n"
            f"✨ *Mind Spark Store Bot*\n\n"
            f"👥 Total Users: {total_users}\n"
            f"✅ Verified Users: {verified_users}\n"
            f"📁 Total Files: {total_files}\n"
            f"📥 Total Downloads: {total_downloads}\n"
            f"⏰ Uptime: {uptime_str}\n\n"
            f"⚡ *Bot is running smoothly*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "user_management":
        if not is_owner(user_id):
            await query.answer("Owner access required!", show_alert=True)
            return
        
        total_users = len(user_stats)
        verified_users = sum(1 for user_data in user_stats.values() if user_data.get('has_joined_channels', False))
        
        # Get last 5 users
        recent_users = list(user_stats.items())[-5:] if user_stats else []
        users_list = ""
        
        for user_id_str, user_data in recent_users:
            username = user_data.get('username', 'No username')
            users_list += f"• {user_id_str} (@{username})\n"
        
        keyboard = [
            [InlineKeyboardButton("📋 All User Links", callback_data="all_user_links")],
            [InlineKeyboardButton("📊 User Activity", callback_data="user_activity")],
            [InlineKeyboardButton("🔙 Back", callback_data="owner_panel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"👥 *User Management*\n\n"
            f"✨ *Mind Spark Community*\n\n"
            f"📈 *Statistics:*\n"
            f"Total Users: {total_users}\n"
            f"Verified Users: {verified_users}\n\n"
            f"👤 *Recent Users (Last 5):*\n{users_list if users_list else 'No users yet'}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "all_user_links":
        if not is_owner(user_id):
            await query.answer("Owner access required!", show_alert=True)
            return
        
        # Create message with all user file links
        message_lines = ["🔗 *All User File Links:*\n\n"]
        
        for file_id, file_info in file_database.items():
            file_link = f"{FILES_BASE_URL}{file_id}"
            uploader_name = file_info.get('uploader_name', 'Unknown')
            message_lines.append(f"• {uploader_name}: `{file_link}`")
        
        if len(message_lines) == 1:
            message_lines.append("No files uploaded yet.")
        
        # Split message if too long
        message = "\n".join(message_lines[:50])  # First 50 files
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="user_management")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message + f"\n\n📁 Total Files: {len(file_database)}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "file_management":
        if not is_owner(user_id):
            await query.answer("Owner access required!", show_alert=True)
            return
        
        total_files = len(file_database)
        
        # Get top 5 downloaded files
        top_files = sorted(file_database.items(), 
                          key=lambda x: x[1].get('download_count', 0), 
                          reverse=True)[:5]
        
        files_list = ""
        for file_id, file_info in top_files:
            downloads = file_info.get('download_count', 0)
            files_list += f"• {file_id}: {downloads} downloads\n"
        
        keyboard = [
            [InlineKeyboardButton("🗑 Delete All Files", callback_data="delete_all_files")],
            [InlineKeyboardButton("📋 View All Files", callback_data="view_all_files")],
            [InlineKeyboardButton("🔙 Back", callback_data="owner_panel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📁 *File Management*\n\n"
            f"✨ *Mind Spark Files*\n\n"
            f"📊 Total Files: {total_files}\n\n"
            f"🔥 *Top Downloaded Files:*\n{files_list if files_list else 'No downloads yet'}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "delete_all_files":
        if not is_owner(user_id):
            await query.answer("Owner access required!", show_alert=True)
            return
        
        keyboard = [
            [InlineKeyboardButton("✅ Confirm Delete", callback_data="confirm_delete_files")],
            [InlineKeyboardButton("❌ Cancel", callback_data="file_management")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚠️ *Warning!*\n\n"
            "This will delete ALL files from the database.\n"
            "This action cannot be undone!\n\n"
            "Are you sure you want to delete all files?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "confirm_delete_files":
        if not is_owner(user_id):
            await query.answer("Owner access required!", show_alert=True)
            return
        
        file_count = len(file_database)
        file_database.clear()
        save_files_data()
        
        await query.edit_message_text(
            f"✅ *All files deleted!*\n\n"
            f"🗑 Deleted {file_count} files.\n"
            f"The database has been cleared.",
            parse_mode='Markdown'
        )
    
    elif data == "broadcast_message":
        if not is_owner(user_id):
            await query.answer("Owner access required!", show_alert=True)
            return
        
        await query.edit_message_text(
            "📢 *Broadcast Message*\n\n"
            "✨ *Send any content to broadcast:*\n\n"
            "✅ *Supported formats:*\n"
            "• Text messages\n"
            "• Photos/Images\n"
            "• Videos\n"
            "• Audio files\n"
            "• Documents (PDF, Word, Excel)\n"
            "• ZIP/RAR archives\n"
            "• Stickers\n"
            "• Voice messages\n"
            "• Animations (GIFs)\n"
            "• Video notes\n\n"
            "📤 *Simply send me the content you want to broadcast*\n"
            "📨 *It will be sent exactly as you send it*",
            parse_mode='Markdown'
        )
        context.user_data['waiting_for_broadcast'] = True
    
    elif data == "export_data":
        if not is_owner(user_id):
            await query.answer("Owner access required!", show_alert=True)
            return
        
        # Export data to JSON file
        export_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_filename = f"mind_spark_export_{export_time}.json"
        
        export_data = {
            'export_time': datetime.now().isoformat(),
            'total_users': len(user_stats),
            'total_files': len(file_database),
            'users': user_stats,
            'files': file_database
        }
        
        try:
            with open(export_filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            with open(export_filename, 'rb') as f:
                await query.message.reply_document(
                    document=f,
                    filename=export_filename,
                    caption=f"📊 Mind Spark Bot Data Export\n\n"
                           f"👥 Users: {len(user_stats)}\n"
                           f"📁 Files: {len(file_database)}\n"
                           f"⏰ Export Time: {export_time}"
                )
            
            os.remove(export_filename)
            
        except Exception as e:
            await query.edit_message_text(f"❌ Export failed: {str(e)}")
    
    elif data == "reset_bot":
        if not is_owner(user_id):
            await query.answer("Owner access required!", show_alert=True)
            return
        
        keyboard = [
            [InlineKeyboardButton("✅ Reset All Data", callback_data="confirm_reset")],
            [InlineKeyboardButton("❌ Cancel", callback_data="owner_panel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "⚠️ *DANGER!*\n\n"
            "This will reset ALL bot data:\n"
            "• All user statistics\n"
            "• All uploaded files\n"
            "• All database records\n\n"
            "This action is PERMANENT and cannot be undone!\n\n"
            "Are you absolutely sure?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "confirm_reset":
        if not is_owner(user_id):
            await query.answer("Owner access required!", show_alert=True)
            return
        
        # Reset all data
        file_database.clear()
        user_stats.clear()
        save_files_data()
        save_user_stats()
        
        await query.edit_message_text(
            "🔄 *Bot Reset Complete!*\n\n"
            "All data has been cleared.\n"
            "The bot is now fresh and empty.",
            parse_mode='Markdown'
        )
    
    elif data == "back_to_menu":
        # Get the user ID from the callback query
        user_id = query.from_user.id
        
        # Create fresh keyboard
        keyboard = [
            ["📤 Upload File", "📥 Download File"],
            ["📁 My Uploads", "📊 My Stats"],
            ["🆔 My ID", "ℹ️ Help"]
        ]
        
        if is_owner(user_id):
            keyboard.append(["👑 Owner Panel"])
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        # Send new message with fresh keyboard
        await context.bot.send_message(
            chat_id=user_id,
            text="✨ *Mind Spark Store Bot* ✨\n\n"
                 "Choose an option from the menu below:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        # Delete the callback query message
        await query.message.delete()
    
    elif data == "user_activity":
        if not is_owner(user_id):
            await query.answer("Owner access required!", show_alert=True)
            return
        
        # Show user activity stats
        active_users = []
        for user_id_str, user_data in user_stats.items():
            last_seen = user_data.get('last_seen')
            if last_seen:
                last_seen_dt = datetime.fromisoformat(last_seen)
                days_ago = (datetime.now() - last_seen_dt).days
                if days_ago <= 7:  # Active in last 7 days
                    username = user_data.get('username', 'No username')
                    uploads = len(user_data.get('files_uploaded', []))
                    downloads = user_data.get('total_downloads', 0)
                    active_users.append((user_id_str, username, uploads, downloads, days_ago))
        
        active_users.sort(key=lambda x: x[4])  # Sort by most recent
        
        message_lines = ["📊 *User Activity (Last 7 Days):*\n\n"]
        for i, (uid, username, uploads, downloads, days_ago) in enumerate(active_users[:10]):
            message_lines.append(f"{i+1}. @{username}")
            message_lines.append(f"   📤 {uploads} uploads | 📥 {downloads} downloads")
            message_lines.append(f"   ⏰ Active {days_ago} day{'s' if days_ago != 1 else ''} ago\n")
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="user_management")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "\n".join(message_lines),
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "view_all_files":
        if not is_owner(user_id):
            await query.answer("Owner access required!", show_alert=True)
            return
        
        # Show all files with pagination
        files_list = []
        for file_id, file_info in file_database.items():
            uploader = file_info.get('uploader_name', 'Unknown')
            downloads = file_info.get('download_count', 0)
            file_type = file_info.get('type', 'unknown')
            created = file_info.get('created_at', 'Unknown')
            
            files_list.append(f"• {file_id} ({file_type})")
            files_list.append(f"  👤 {uploader} | 📥 {downloads} downloads")
            files_list.append(f"  ⏰ {created[:10]}\n")
        
        if not files_list:
            files_list.append("No files uploaded yet.")
        
        # Take first 30 lines to avoid message too long
        message = "\n".join(files_list[:30])
        if len(files_list) > 30:
            message += f"\n\n... and {len(file_database) - 30} more files"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="file_management")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📁 *All Files ({len(file_database)} total):*\n\n{message}",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def handle_text_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text
    
    # IGNORE messages from groups - only respond in private
    if update.message.chat.type != 'private':
        return
    
    # Handle broadcast message from owner
    if 'waiting_for_broadcast' in context.user_data and is_owner(user_id):
        await handle_broadcast(update, context)
        return
    
    # First, check membership for non-owner
    if not is_owner(user_id):
        not_joined = await check_user_membership(user_id, context)
        if not_joined:
            await show_join_requirement(update, context, user_id, update.effective_user)
            return
    
    # Handle reply keyboard buttons
    if text == "📤 Upload File":
        await update.message.reply_text(
            "📤 *Ready to Upload!*\n\n"
            "✨ *Share educational resources with our community!*\n\n"
            "Send me any file:\n"
            "• Videos 📹\n"
            "• Photos 🖼\n"
            "• Documents 📄\n"
            "• Audio files 🎵\n\n"
            "I'll create a permanent shareable link for you!",
            parse_mode='Markdown'
        )
    
    elif text == "📥 Download File":
        await update.message.reply_text(
            "📥 *Download Files*\n\n"
            "To access shared educational resources:\n"
            "1. Click on any shared file link\n"
            "2. The file will be sent to you immediately\n"
            "3. All files are stored permanently\n\n"
            "💡 *Perfect for sharing study materials!*",
            parse_mode='Markdown'
        )
    
    elif text == "📁 My Uploads":
        user_data = user_stats.get(str(user_id), {})
        uploaded_files = user_data.get('files_uploaded', [])
        
        if uploaded_files:
            files_list = []
            for i, file_id in enumerate(uploaded_files[:5]):
                if file_id in file_database:
                    file_link = f"{FILES_BASE_URL}{file_id}"
                    files_list.append(f"{i+1}. `{file_link}`")
            
            message = "📁 *Your Uploaded Files*\n\n" + "\n".join(files_list)
            if len(uploaded_files) > 5:
                message += f"\n\n... and {len(uploaded_files)-5} more"
            
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text(
                "📭 *No files uploaded yet!*\n\n"
                "Start sharing educational resources with our community!\n"
                "Use '📤 Upload File' to get started.",
                parse_mode='Markdown'
            )
    
    elif text == "📊 My Stats":
        user_data = user_stats.get(str(user_id), {})
        total_uploads = len(user_data.get('files_uploaded', []))
        total_downloads = user_data.get('total_downloads', 0)
        
        await update.message.reply_text(
            f"📊 *Your Statistics*\n\n"
            f"✨ *Mind Spark Contributor*\n\n"
            f"📤 Files Uploaded: {total_uploads}\n"
            f"📥 Files Downloaded: {total_downloads}\n"
            f"✅ Status: Verified Member\n\n"
            f"🌟 *Keep sharing knowledge!*",
            parse_mode='Markdown'
        )
    
    elif text == "🆔 My ID":
        await update.message.reply_text(
            f"🆔 *Your User ID:*\n`{user_id}`\n\n"
            "✨ *This unique ID identifies you in our community!*",
            parse_mode='Markdown'
        )
    
    elif text == "ℹ️ Help":
        await help_command(update, context)
    
    elif text == "👑 Owner Panel" and is_owner(user_id):
        keyboard = [
            [InlineKeyboardButton("📊 Bot Statistics", callback_data="bot_stats")],
            [InlineKeyboardButton("👥 User Management", callback_data="user_management")],
            [InlineKeyboardButton("📁 File Management", callback_data="file_management")],
            [InlineKeyboardButton("📢 Broadcast Message", callback_data="broadcast_message")],
            [InlineKeyboardButton("📤 Export Data", callback_data="export_data")],
            [InlineKeyboardButton("🔄 Reset Bot", callback_data="reset_bot")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "👑 *Owner Panel* 👑\n\n"
            "✨ *Mind Spark Store Bot Admin*\n\n"
            "Select an option:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    else:
        # If it's not a button text, check if it's a command
        if text.startswith('/'):
            await update.message.reply_text(
                "❓ *Unknown Command*\n\n"
                "Use the buttons below or type /help for assistance.",
                parse_mode='Markdown'
            )

async def help_command(update: Update, context: CallbackContext):
    """Help command handler - BOTH /help command AND button will work"""
    # IGNORE messages from groups
    if update.message.chat.type != 'private':
        return
    
    user_id = update.effective_user.id
    
    # Check membership for non-owner
    if not is_owner(user_id):
        not_joined = await check_user_membership(user_id, context)
        if not_joined:
            await show_join_requirement(update, context, user_id, update.effective_user)
            return
    
    # Create keyboard for help menu
    keyboard = [
        ["📤 Upload File", "📥 Download File"],
        ["📁 My Uploads", "📊 My Stats"],
        ["🆔 My ID", "ℹ️ Help"]
    ]
    
    if is_owner(user_id):
        keyboard.append(["👑 Owner Panel"])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🆘 *Mind Spark Store Bot - Help*\n\n"
        "✨ *Welcome to our educational community!*\n\n"
        "📚 *How to use this bot:*\n"
        "1. Join all required educational channels\n"
        "2. Verify your membership\n"
        "3. Upload study materials to get shareable links\n"
        "4. Share links with classmates and friends\n"
        "5. Click links to download educational resources\n\n"
        "📋 *Commands:*\n"
        "/start - Start the bot and join channels\n"
        "/help - Show this help message\n"
        "/owner - Owner panel (owner only)\n\n"
        "📱 *Reply Keyboard Buttons:*\n"
        "• 📤 Upload File - Upload new files\n"
        "• 📥 Download File - Access shared files\n"
        "• 📁 My Uploads - View your uploaded files\n"
        "• 📊 My Stats - View your statistics\n"
        "• 🆔 My ID - Get your user ID\n"
        "• ℹ️ Help - Show help message\n"
        "• 👑 Owner Panel - Admin controls (owner only)\n\n"
        "🔧 *Features:*\n"
        "• Permanent educational resource storage\n"
        "• Shareable links for study materials\n"
        "• User statistics and tracking\n"
        "• Channel verification system\n"
        "• Support for all file types\n\n"
        "🎯 *Perfect for:*\n"
        "• Sharing notes and study materials\n"
        "• Distributing educational videos\n"
        "• Collaborating on projects\n"
        "• Building a learning community\n\n"
        "❓ *Support:* @Team_2k26_Support_Bot",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_broadcast(update: Update, context: CallbackContext):
    """Handle broadcast message from owner - SUPPORTS ALL FORMATS"""
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        return
    
    message = update.message
    verified_users = [uid for uid, data in user_stats.items() if data.get('has_joined_channels', False)]
    success_count = 0
    fail_count = 0
    
    progress_msg = await update.message.reply_text(f"📢 Broadcasting to {len(verified_users)} users...")
    
    for user_id_str in verified_users:
        try:
            # Send message exactly as owner sent it
            if message.text:
                await context.bot.send_message(
                    chat_id=int(user_id_str),
                    text=message.text,
                    parse_mode='Markdown' if message.text_markdown_v2 else None
                )
            elif message.photo:
                await context.bot.send_photo(
                    chat_id=int(user_id_str),
                    photo=message.photo[-1].file_id,
                    caption=message.caption,
                    parse_mode='Markdown' if message.caption_markdown_v2 else None
                )
            elif message.video:
                await context.bot.send_video(
                    chat_id=int(user_id_str),
                    video=message.video.file_id,
                    caption=message.caption,
                    parse_mode='Markdown' if message.caption_markdown_v2 else None
                )
            elif message.audio:
                await context.bot.send_audio(
                    chat_id=int(user_id_str),
                    audio=message.audio.file_id,
                    caption=message.caption,
                    parse_mode='Markdown' if message.caption_markdown_v2 else None
                )
            elif message.document:
                await context.bot.send_document(
                    chat_id=int(user_id_str),
                    document=message.document.file_id,
                    caption=message.caption,
                    parse_mode='Markdown' if message.caption_markdown_v2 else None
                )
            elif message.sticker:
                await context.bot.send_sticker(
                    chat_id=int(user_id_str),
                    sticker=message.sticker.file_id
                )
            elif message.voice:
                await context.bot.send_voice(
                    chat_id=int(user_id_str),
                    voice=message.voice.file_id,
                    caption=message.caption,
                    parse_mode='Markdown' if message.caption_markdown_v2 else None
                )
            elif message.animation:  # GIFs
                await context.bot.send_animation(
                    chat_id=int(user_id_str),
                    animation=message.animation.file_id,
                    caption=message.caption,
                    parse_mode='Markdown' if message.caption_markdown_v2 else None
                )
            elif message.video_note:
                await context.bot.send_video_note(
                    chat_id=int(user_id_str),
                    video_note=message.video_note.file_id
                )
            
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            logging.error(f"Failed to send broadcast to {user_id_str}: {e}")
            fail_count += 1
    
    await progress_msg.edit_text(
        f"✅ *Broadcast Complete!*\n\n"
        f"✨ *Mind Spark Community Update*\n\n"
        f"✅ Successfully sent: {success_count} users\n"
        f"❌ Failed to send: {fail_count} users\n"
        f"📊 Total reached: {len(verified_users)} users\n"
        f"📈 Success rate: {(success_count/len(verified_users)*100):.1f}%",
        parse_mode='Markdown'
    )
    
    context.user_data.pop('waiting_for_broadcast', None)

async def owner_command(update: Update, context: CallbackContext):
    """Owner command handler - BOTH /owner command AND button will work"""
    user_id = update.effective_user.id
    
    # IGNORE messages from groups
    if update.message.chat.type != 'private':
        return
    
    if not is_owner(user_id):
        await update.message.reply_text("❌ Owner access required.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Bot Statistics", callback_data="bot_stats")],
        [InlineKeyboardButton("👥 User Management", callback_data="user_management")],
        [InlineKeyboardButton("📁 File Management", callback_data="file_management")],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="broadcast_message")],
        [InlineKeyboardButton("📤 Export Data", callback_data="export_data")],
        [InlineKeyboardButton("🔄 Reset Bot", callback_data="reset_bot")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👑 *Owner Panel* 👑\n\n"
        "✨ *Mind Spark Store Bot Admin*\n\n"
        "Select an option:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_sticker(update: Update, context: CallbackContext):
    """Handle sticker messages - for non-owner users, check membership"""
    # IGNORE messages from groups
    if update.message.chat.type != 'private':
        return
    
    user_id = update.effective_user.id
    
    # If owner is in broadcast mode
    if 'waiting_for_broadcast' in context.user_data and is_owner(user_id):
        await handle_broadcast(update, context)
        return
    
    # Check membership for non-owner
    if not is_owner(user_id):
        not_joined = await check_user_membership(user_id, context)
        if not_joined:
            await show_join_requirement(update, context, user_id, update.effective_user)
            return
    
    await update.message.reply_text(
        "😊 *Stickers are fun!*\n\n"
        "But I can only store and share educational files.\n"
        "Please send me videos, photos, documents, or audio files instead.",
        parse_mode='Markdown'
    )

async def handle_voice(update: Update, context: CallbackContext):
    """Handle voice messages - for non-owner users, check membership"""
    # IGNORE messages from groups
    if update.message.chat.type != 'private':
        return
    
    user_id = update.effective_user.id
    
    # If owner is in broadcast mode
    if 'waiting_for_broadcast' in context.user_data and is_owner(user_id):
        await handle_broadcast(update, context)
        return
    
    # Check membership for non-owner
    if not is_owner(user_id):
        not_joined = await check_user_membership(user_id, context)
        if not_joined:
            await show_join_requirement(update, context, user_id, update.effective_user)
            return
    
    await update.message.reply_text(
        "🎤 *Voice message received!*\n\n"
        "I currently don't store voice messages.\n"
        "Please send me videos, photos, documents, or audio files instead.",
        parse_mode='Markdown'
    )

async def handle_animation(update: Update, context: CallbackContext):
    """Handle animation (GIF) messages"""
    # IGNORE messages from groups
    if update.message.chat.type != 'private':
        return
    
    user_id = update.effective_user.id
    
    # If owner is in broadcast mode
    if 'waiting_for_broadcast' in context.user_data and is_owner(user_id):
        await handle_broadcast(update, context)
        return
    
    # Check membership for non-owner
    if not is_owner(user_id):
        not_joined = await check_user_membership(user_id, context)
        if not_joined:
            await show_join_requirement(update, context, user_id, update.effective_user)
            return
    
    await update.message.reply_text(
        "🎬 *Animation received!*\n\n"
        "I currently don't store animations/GIFs.\n"
        "Please send me videos, photos, documents, or audio files instead.",
        parse_mode='Markdown'
    )

async def error_handler(update: Update, context: CallbackContext):
    logger.error(f"Error: {context.error}")

# Flask routes for Render webhook
@flask_app.route('/')
def home():
    return "🤖 Mind Spark Store Bot is Running! 🚀"

@flask_app.route('/health')
def health():
    return "OK"

@flask_app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == "POST":
        if application:
            update = Update.de_json(request.get_json(force=True), application.bot)
            asyncio.run(application.process_update(update))
    return "ok"

async def setup_webhook():
    """Set up webhook for Render"""
    global application
    
    # Load data first
    load_files_data()
    load_user_stats()
    
    # Create application
    application = Application.builder()\
        .token(BOT_TOKEN)\
        .concurrent_updates(True)\
        .pool_timeout(20)\
        .build()
    
    application.add_error_handler(error_handler)
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("owner", owner_command))
    application.add_handler(CommandHandler("help", help_command))
    
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.AUDIO, handle_audio))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.ANIMATION, handle_animation))
    
    # Text handler should be added LAST
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Get Render URL
    render_url = os.environ.get('RENDER_EXTERNAL_URL')
    if render_url:
        # Set webhook for Render
        webhook_url = f"{render_url}/webhook"
        await application.bot.set_webhook(webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")
    else:
        # Local development - use polling
        logger.info("Starting with polling...")
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
    
    return application

def start_bot():
    """Start bot for Render"""
    import threading
    
    # Start Flask in a separate thread
    def run_flask():
        port = int(os.environ.get('PORT', 10000))
        flask_app.run(host='0.0.0.0', port=port, debug=False)
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Setup and run bot
    asyncio.run(setup_webhook())
    
    logger.info("✨ Mind Spark Store Bot activated...")
    logger.info("✅ Bot will ONLY respond in private chat")
    logger.info("✅ Bot will IGNORE all group messages")
    logger.info("✅ Webhook mode for Render")

if __name__ == '__main__':
    # For local testing
    load_files_data()
    load_user_stats()
    
    # Local polling mode
    application_local = Application.builder()\
        .token(BOT_TOKEN)\
        .concurrent_updates(True)\
        .pool_timeout(20)\
        .build()
    
    application_local.add_error_handler(error_handler)
    
    application_local.add_handler(CommandHandler("start", start))
    application_local.add_handler(CommandHandler("owner", owner_command))
    application_local.add_handler(CommandHandler("help", help_command))
    
    application_local.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application_local.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application_local.add_handler(MessageHandler(filters.AUDIO, handle_audio))
    application_local.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application_local.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
    application_local.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application_local.add_handler(MessageHandler(filters.ANIMATION, handle_animation))
    
    application_local.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    application_local.add_handler(CallbackQueryHandler(button_handler))
    
    print("✨ Mind Spark Store Bot activated...")
    print("✅ Local polling mode")
    print("✅ Bot will ONLY respond in private chat")
    
    application_local.run_polling()