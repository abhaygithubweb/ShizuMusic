import asyncio
import random
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message
from ShizuMusic import app, userbot

TAGALL_USERS = {}

# Function to dynamically convert member names into Royal Serif Bold (𝐀𝐛𝐡𝐚𝐲)
def to_royal_bold(text: str) -> str:
    bold_serif_map = {
        'A': '𝐀', 'B': '𝐁', 'C': '𝐂', 'D': '𝐃', 'E': '𝐄', 'F': '𝐅', 'G': '𝐆', 'H': '𝐇', 'I': '𝐈',
        'J': '𝐉', 'K': '𝐊', 'L': '𝐋', 'M': '𝐌', 'N': '𝐍', 'O': '𝐎', 'P': '𝐏', 'Q': '𝐐', 'R': '𝐑',
        'S': '𝐒', 'T': '𝐓', 'U': '𝐔', 'V': '𝐕', 'W': '𝐖', 'X': '𝐗', 'Y': '𝐘', 'Z': '𝐙',
        'a': '𝐚', 'b': '𝐛', 'c': '𝐜', 'd': '𝐝', 'e': '𝐞', 'f': '𝐟', 'g': '𝐠', 'h': '𝐡', 'i': '𝐢',
        'j': '𝐣', 'k': '𝐤', 'l': '𝐥', 'm': '𝐦', 'n': '𝐧', 'o': '𝐨', 'p': '𝐩', 'q': '𝐪', 'r': '𝐫',
        's': '𝐬', 't': '𝐭', 'u': '𝐮', 'v': '𝐯', 'w': '𝐰', 'x': '𝐱', 'y': '𝐲', 'z': '𝐳'
    }
    return "".join(bold_serif_map.get(char, char) for char in text)


# Spicy, Flirty & Dark Humor Lines in Small Caps Luxury Font (ᴀʙʜᴀʏ style)
SPICY_AND_DARK_TAGS = [
    # 🫦 ꜱᴘɪᴄʏ & ꜰʟɪʀᴛʏ
    "🫦 ꜱᴛᴏᴘ ʟᴏᴏᴋɪɴɢ ꜱᴏ ᴇᴅɪʙʟᴇ ᴡʜᴇɴ ɪ’ᴍ ᴛʀʏɪɴɢ ᴛᴏ ʙᴇʜᴀᴠᴇ.",
    "🔥 ʏᴏᴜ ʟᴏᴏᴋ ʟɪᴋᴇ ᴍʏ ꜰᴀᴠᴏʀɪᴛᴇ ᴋɪɴᴅ ᴏꜰ ᴍɪꜱᴛᴀᴋᴇ.",
    "💋 ᴍʏ ʙᴇᴅ ɪꜱ ᴡᴀʏ ᴛᴏᴏ ꜱᴘᴀᴄɪᴏᴜꜱ ᴡɪᴛʜᴏᴜᴛ ʏᴏᴜ ɪɴ ɪᴛ.",
    "🥂 ɪ’ᴍ ɴᴏᴛ ꜱᴀʏɪɴɢ ʏᴏᴜ'ʀᴇ ᴀ ꜱɴᴀᴄᴋ, ʏᴏᴜ’ʀᴇ ᴛʜᴇ ᴡʜᴏʟᴇ ʙᴜꜰꜰᴇᴛ.",
    "😈 ᴛʀᴏᴜʙʟᴇ ɴᴇᴠᴇʀ ʟᴏᴏᴋᴇᴅ ꜱᴏ ᴅᴀᴍɴ ɪʀʀᴇꜱɪꜱᴛɪʙʟᴇ.",
    "🍒 ᴄᴀɴ ᴡᴇ ꜱᴋɪᴘ ᴛʜᴇ ꜱᴍᴀʟʟ ᴛᴀʟᴋ ᴀɴᴅ ᴛᴇꜱᴛ ᴛʜᴇ ᴄʜᴇᴍɪꜱᴛʀʏ?",
    "🥀 ꜱᴛᴏᴘ ʟɪᴠɪɴɢ ɪɴ ᴍʏ ʜᴇᴀᴅ ʀᴇɴᴛ-ꜰʀᴇᴇ ᴀɴᴅ ᴘᴀʏ ʏᴏᴜʀ ᴅᴜᴇꜱ.",
    "🔒 ᴋᴇᴇᴘ ꜱᴛᴀʀɪɴɢ ʟɪᴋᴇ ᴛʜᴀᴛ ᴀɴᴅ ꜱᴇᴇ ᴡʜᴀᴛ ʜᴀᴘᴘᴇɴꜱ ɴᴇxᴛ.",
    "✨ ʏᴏᴜ ʟᴏᴏᴋ ʟɪᴋᴇ ʏᴏᴜ ɢɪᴠᴇ ᴛʜᴇ ʙᴇꜱᴛ ʙᴀᴅ ɪᴅᴇᴀꜱ.",
    "🖤 ꜱᴇɴᴅ ʟᴏᴄᴀᴛɪᴏɴ, ɪ ʜᴀᴠᴇ ᴀ ꜰᴇᴡ ᴡɪᴄᴋᴇᴅ ᴘʟᴀɴꜱ ᴛᴏ ᴛʀʏ.",
    "🫦 ᴀʀᴇ ʏᴏᴜ ᴀʟᴡᴀʏꜱ ᴛʜɪꜱ ᴀᴅᴅɪᴄᴛɪᴠᴇ ᴏʀ ɪꜱ ɪᴛ ᴊᴜꜱᴛ ꜰᴏʀ ᴍᴇ?",
    "🥂 ɪ’ᴅ ʟᴏᴠᴇ ᴛᴏ ᴛᴇʟʟ ʏᴏᴜ ᴡʜᴀᴛ ɪ’ᴍ ᴛʜɪɴᴋɪɴɢ, ʙᴜᴛ ɪ'ʟʟ ᴡʜɪꜱᴘᴇʀ ɪᴛ.",
    "🔥 ᴅᴏɴ’ᴛ ᴛᴇᴍᴘᴛ ᴍᴇ ᴡɪᴛʜ ᴀ ʀᴇᴄᴋʟᴇꜱꜱ ɴɪɢʜᴛ ᴜɴʟᴇꜱꜱ ʏᴏᴜ ᴍᴇᴀɴ ɪᴛ.",
    "💋 ʏᴏᴜ’ᴠᴇ ɢᴏᴛ ᴛʜᴀᴛ ᴅᴀɴɢᴇʀᴏᴜꜱʟʏ ᴡɪʟᴅ ʟᴏᴏᴋ ɪ ᴄʀᴀᴠᴇ.",
    "🍒 ɪꜱ ɪᴛ ɢᴇᴛᴛɪɴɢ ʜᴏᴛ ɪɴ ʜᴇʀᴇ, ᴏʀ ᴅɪᴅ ʏᴏᴜ ᴊᴜꜱᴛ ꜱᴛᴇᴘ ɪɴ?",

    # 💀 ᴅᴀʀᴋ ʜᴜᴍᴏʀ & ꜱᴀᴠᴀɢᴇ
    "💀 ɪ'ᴅ ᴀɢʀᴇᴇ ᴡɪᴛʜ ʏᴏᴜ, ʙᴜᴛ ᴛʜᴇɴ ᴡᴇ’ᴅ ʙᴏᴛʜ ʙᴇ ᴡʀᴏɴɢ.",
    "⚰️ ᴍʏ ᴛʜᴇʀᴀᴘɪꜱᴛ ᴛᴏʟᴅ ᴍᴇ ᴛᴏ ᴇᴍʙʀᴀᴄᴇ ᴍʏ ᴅᴇᴍᴏɴꜱ... ꜱᴏ ᴡʜᴇʀᴇ ʏᴏᴜ ᴀᴛ?",
    "🖤 ʏᴏᴜ'ʀᴇ ᴛʜᴇ ʀᴇᴀꜱᴏɴ ᴛʜᴇ ɢᴇɴᴇ ᴘᴏᴏʟ ɴᴇᴇᴅꜱ ᴍᴏʀᴇ ᴄʜʟᴏʀɪɴᴇ.",
    "🥀 ɪ'ᴍ ɴᴏᴛ ᴜꜱᴇʟᴇꜱꜱ... ɪ ᴄᴀɴ ᴀʟᴡᴀʏꜱ ꜱᴇʀᴠᴇ ᴀꜱ ᴀ ʙᴀᴅ ᴇxᴀᴍᴘʟᴇ.",
    "💀 ɢɪᴠᴇ ᴍᴇ ʏᴏᴜʀ ʜᴇᴀʀᴛ... ꜱᴇʀɪᴏᴜꜱʟʏ, ᴏʀɢᴀɴ ᴘʀɪᴄᴇꜱ ᴀʀᴇ ʙᴏᴏᴍɪɴɢ.",
    "🥂 ʏᴏᴜ ʙʀɪɴɢ ᴊᴏʏ ᴡʜᴇɴᴇᴠᴇʀ ʏᴏᴜ ʟᴇᴀᴠᴇ ᴛʜᴇ ʀᴏᴏᴍ.",
    "⚰️ ᴅᴏɴ'ᴛ ᴛᴀᴋᴇ ʟɪꜰᴇ ꜱᴇʀɪᴏᴜꜱʟʏ, ɴᴏɴᴇ ᴏꜰ ᴜꜱ ɢᴇᴛ ᴏᴜᴛ ᴀʟɪᴠᴇ.",
    "🖤 ᴍɪʀʀᴏʀꜱ ᴅᴏɴ'ᴛ ʟɪᴇ, ᴀɴᴅ ʟᴜᴄᴋʏ ꜰᴏʀ ʏᴏᴜ, ᴛʜᴇʏ ᴅᴏɴ'ᴛ ʟᴀᴜɢʜ.",
    "💀 ʏᴏᴜ'ʀᴇ ʟɪᴋᴇ ᴀ ꜱᴏꜰᴛᴡᴀʀᴇ ᴜᴘᴅᴀᴛᴇ—ᴇᴠᴇʀʏᴏɴᴇ ʜɪᴛꜱ 'ʀᴇᴍɪɴᴅ ᴍᴇ ʟᴀᴛᴇʀ'.",
    "⚰️ ɪꜰ ᴋᴀʀᴍᴀ ᴅᴏᴇꜱɴ'ᴛ ʜɪᴛ ʏᴏᴜ, ᴅᴏɴ'ᴛ ᴡᴏʀʀʏ, ᴍʏ ᴘʟᴀʏʟɪꜱᴛ ᴡɪʟʟ.",
    "🥀 ᴇᴠᴇɴ ɢᴏᴏɢʟᴇ ᴄᴀɴ'ᴛ ꜱᴇᴀʀᴄʜ ꜰᴏʀ ʏᴏᴜʀ ᴄᴏᴍᴍᴏɴ ꜱᴇɴꜱᴇ.",
    "🖤 ʟɪɢʜᴛ ᴛʀᴀᴠᴇʟꜱ ꜰᴀꜱᴛᴇʀ ᴛʜᴀɴ ꜱᴏᴜɴᴅ, ᴡʜɪᴄʜ ɪꜱ ᴡʜʏ ʏᴏᴜ ʟᴏᴏᴋᴇᴅ ʙʀɪɢʜᴛ ᴜɴᴛɪʟ ʏᴏᴜ ꜱᴘᴏᴋᴇ."
]

@app.on_message(filters.command(["tagall", "mention", "utag", "stag"]) & filters.group)
async def tag_all_members(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None

    # Check admin privileges
    if user_id:
        member = await client.get_chat_member(chat_id, user_id)
        if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
            return await message.reply_text("❌ **ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ!**")

    if chat_id in TAGALL_USERS:
        return await message.reply_text("⚠️ **ᴀ ᴛᴀɢ ꜱᴇꜱꜱɪᴏɴ ɪꜱ ᴀʟʀᴇᴀᴅʏ ʀᴜɴɴɪɴɢ. ᴜꜱᴇ `/cancel` ᴛᴏ ꜱᴛᴏᴘ.**")

    custom_text = message.text.split(None, 1)[1] if len(message.text.split()) > 1 else ""
    TAGALL_USERS[chat_id] = True

    # Assistant verification
    ub_client = getattr(userbot, "one", userbot)
    if not ub_client:
        return await message.reply_text("❌ **ᴀꜱꜱɪꜱᴛᴀɴᴛ ᴀᴄᴄᴏᴜɴᴛ ɪꜱ ᴏꜰꜰʟɪɴᴇ.**")

    await message.reply_text("⚡ **ᴀꜱꜱɪꜱᴛᴀɴᴛ ꜱᴛᴀʀᴛᴇᴅ ʟᴜxᴜʀʏ ᴛᴀɢɢɪɴɢ...**")

    async for member in client.get_chat_members(chat_id):
        if chat_id not in TAGALL_USERS:
            break

        user = member.user
        if user.is_bot or user.is_deleted:
            continue

        # Convert user's first name to Royal Bold (𝐀𝐛𝐡𝐚𝐲)
        royal_name = to_royal_bold(user.first_name)
        mention_link = f"[{royal_name}](tg://user?id={user.id})"
        tag_line = random.choice(SPICY_AND_DARK_TAGS)

        if custom_text:
            msg_text = f"👑 **{custom_text}**\n\n{mention_link} — {tag_line}"
        else:
            msg_text = f"{mention_link} — {tag_line}"

        try:
            await ub_client.send_message(chat_id, msg_text)
            await asyncio.sleep(2)
        except Exception:
            await asyncio.sleep(2)

    TAGALL_USERS.pop(chat_id, None)
    await message.reply_text("✅ **ᴛᴀɢɢɪɴɢ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!**")


@app.on_message(filters.command(["cancel", "stopmention", "canceltag"]) & filters.group)
async def cancel_tagging(client, message: Message):
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else None

    if user_id:
        member = await client.get_chat_member(chat_id, user_id)
        if member.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
            return await message.reply_text("❌ **ᴏɴʟʏ ɢʀᴏᴜᴘ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴄᴀɴᴄᴇʟ ᴛᴀɢɢɪɴɢ!**")

    if chat_id in TAGALL_USERS:
        TAGALL_USERS.pop(chat_id, None)
        await message.reply_text("🛑 **ᴛᴀɢɢɪɴɢ ꜱᴇꜱꜱɪᴏɴ ꜱᴛᴏᴘᴘᴇᴅ.**")
    else:
        await message.reply_text("❓ **ɴᴏ ᴀᴄᴛɪᴠᴇ ᴛᴀɢɢɪɴɢ ꜱᴇꜱꜱɪᴏɴ ꜰᴏᴜɴᴅ.**")
