import telebot
from openai import OpenAI
import sqlite3
import threading
import logging
from dotenv import load_dotenv
import os
from utils.messages import bot_instruction

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize OpenAI client
client = OpenAI()
logging.info("OpenAI client initialized.")

# Initialize the bot with your token
bot_token = os.getenv('TG_BOT_TOKEN')
if not bot_token:
    logging.error("Telegram bot token is missing. Please check your environment variables.")
    exit(1)

bot = telebot.TeleBot(bot_token, parse_mode=None)
logging.info("Telegram bot initialized.")

# Set the number of messages to keep in history
HISTORY_SIZE = 10

# In-memory storage for message history per chat
chat_histories = {}

# Initialize database connection
NO_DB_REWRITE = os.getenv('NO_DB_REWRITE', 'false').lower() == 'true'
if not NO_DB_REWRITE:
    try:
        conn = sqlite3.connect('messages.db', check_same_thread=False)
        cursor = conn.cursor()
        logging.info("Database connection established.")
    except sqlite3.Error as e:
        logging.error(f"Failed to connect to the database: {e}")
        exit(1)
else:
    conn = None
    cursor = None
    logging.info("Database rewrite is disabled.")

# Create a lock for thread-safe database operations
db_lock = threading.Lock()

# Create table for storing messages
if not NO_DB_REWRITE:
    with db_lock:
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    user_id INTEGER,
                    username TEXT,
                    message_text TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            logging.info("Database table 'messages' ensured.")
        except sqlite3.Error as e:
            logging.error(f"Failed to create table: {e}")
            exit(1)


def store_message(chat_id, user_id, username, message_text):
    if NO_DB_REWRITE:
        logging.info("Database rewrite is disabled. Skipping message storage.")
        return
    with db_lock:
        try:
            cursor.execute('''
                INSERT INTO messages (chat_id, user_id, username, message_text)
                VALUES (?, ?, ?, ?)
            ''', (chat_id, user_id, username, message_text))
            conn.commit()
            logging.info(f"Stored message from {username} in chat {chat_id}.")
        except sqlite3.Error as e:
            logging.error(f"Failed to store message: {e}")


def load_chat_history(chat_id):
    if NO_DB_REWRITE:
        logging.info("Database rewrite is disabled. Skipping chat history load.")
        return []
    with db_lock:
        try:
            cursor.execute('''
                SELECT username, message_text FROM messages WHERE chat_id = ? ORDER BY timestamp ASC
            ''', (chat_id,))
            rows = cursor.fetchall()
            logging.info(f"Loaded chat history for chat {chat_id}. Total messages: {len(rows)}")
            return [{'role': 'user', 'content': f'{username}: {message_text}'} for username, message_text in rows]
        except sqlite3.Error as e:
            logging.error(f"Failed to load chat history: {e}")
            return []


def is_bot_mentioned(message):
    if message.entities:
        for entity in message.entities:
            if entity.type == 'mention':
                mention = message.text[entity.offset:entity.offset + entity.length]
                bot_username = f'@{bot.get_me().username}'
                if mention == bot_username:
                    logging.info(f"Bot mentioned by {message.from_user.username} in chat {message.chat.id}.")
                    return True
    return False


def is_reply_to_bot(message):
    if message.reply_to_message and message.reply_to_message.from_user.username == bot.get_me().username:
        logging.info(f"Message from {message.from_user.username} is a reply to the bot in chat {message.chat.id}.")
        return True
    return False


def is_reply(message):
    if message.reply_to_message:
        logging.info(f"Message from {message.from_user.username} is a reply in chat {message.chat.id}.")
        return True
    return False


def is_forwarded_message(message):
    if message.forward_from or message.forward_sender_name:
        logging.info(f"Message from {message.from_user.username} is a forwarded message in chat {message.chat.id}.")
        return True
    return False


def is_reply_or_forward_mention(message):
    if (is_reply(message) or is_forwarded_message(message)) and is_bot_mentioned(message):
        logging.info(
            f"Message from {message.from_user.username} is a reply or forward that mentions the bot in chat {message.chat.id}.")
        return True
    return False


# @bot.message_handler(func=lambda message: True, content_types=['text', 'audio', 'document', 'photo', 'sticker', 'video', 'video_note', 'voice', 'location', 'contact', 'venue', 'animation', 'dice', 'poll', 'invoice', 'successful_payment', 'website_connected', 'passport_data', 'proximity_alert_triggered', 'voice_chat_scheduled', 'voice_chat_started', 'voice_chat_ended', 'voice_chat_participants_invited', 'message_auto_delete_timer_changed', 'chat_invite_link', 'video_chat_scheduled', 'video_chat_started', 'video_chat_ended', 'video_chat_participants_invited', 'web_app_data', 'forum_topic_created', 'forum_topic_closed', 'forum_topic_reopened', 'forum_topic_edited', 'general_forum_topic_hidden', 'general_forum_topic_unhidden', 'write_access_allowed', 'user_shared', 'chat_shared', 'story'])
# def handle_everything(message):
#     content_type = message.content_type
#     print(f"Message of type '{content_type}' received.")


@bot.message_handler(func=lambda message: True, content_types=['text', 'audio', 'document', 'photo', 'sticker', 'video', 'video_note', 'voice', 'location', 'contact', 'venue', 'animation', 'dice', 'poll', 'invoice', 'successful_payment', 'website_connected', 'passport_data', 'proximity_alert_triggered', 'voice_chat_scheduled', 'voice_chat_started', 'voice_chat_ended', 'voice_chat_participants_invited', 'message_auto_delete_timer_changed', 'chat_invite_link', 'video_chat_scheduled', 'video_chat_started', 'video_chat_ended', 'video_chat_participants_invited', 'web_app_data', 'forum_topic_created', 'forum_topic_closed', 'forum_topic_reopened', 'forum_topic_edited', 'general_forum_topic_hidden', 'general_forum_topic_unhidden', 'write_access_allowed', 'user_shared', 'chat_shared', 'story'])
def handle_message(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name

    if message.text:
        message_text = message.text
    else:
        message_text = ""

    logging.info(f"Received message from {username} in chat {chat_id}")

    if message.reply_to_message:
        message_text = f"""[Reply to {message.reply_to_message.from_user.username}]
Text from replied message:
===
{message.reply_to_message.any_text}
===

{username}: {message_text}"""

    elif message.forward_from:
        message_text = f"""[Forwarded from {message.forward_from.username or message.forward_sender_name}]
Text from forwarded message:
===
{message.any_text}
===
{username}: {message.text}"""

    # Store the message in the database
    store_message(chat_id, user_id, username, message_text)

    # Load message history from the database if not already in memory
    if chat_id not in chat_histories:
        chat_histories[chat_id] = load_chat_history(chat_id)
        logging.info(f"Loaded message history for chat {chat_id} from the database.")

    chat_history = chat_histories[chat_id]

    # Append the new message to the history
    chat_history.append({'role': 'user', 'content': f'{username}: {message_text}'})
    logging.info(f"Appended message to history for chat {chat_id}. Current history size: {len(chat_history)}")

    # Keep only the last N messages
    if len(chat_history) > HISTORY_SIZE:
        chat_history = chat_history[-20:]
        logging.info(f"Trimmed message history for chat {chat_id} to the last {HISTORY_SIZE} messages.")

    # Check if the bot is mentioned, if the message is a reply to the bot, if it is a forwarded message, or if it is a reply/forward that mentions the bot
    if is_bot_mentioned(message) or is_reply_to_bot(message) or is_forwarded_message(
            message) or is_reply_or_forward_mention(message):

        logging.info(f"Bot triggered in chat {chat_id}, preparing response.")
        # Remove bot mention from message text if mentioned
        bot_username = f'@{bot.get_me().username}'
        user_message = message_text.replace(bot_username, '').strip()

        if user_message:
            # Prepare the messages for the LLM
            messages_for_llm = chat_history.copy()
            # messages_for_llm.append({'role': 'user', 'content': f'{username}: {user_message}'})
            # Get the LLM response
            response = get_llm_response(messages_for_llm)
            # Send the response to the chat
            bot.reply_to(message, response)
            logging.info(f"Sent response to chat {chat_id}: {response}")
            # Add the bot's response to the history
            chat_history.append({'role': 'assistant', 'content': f'{response}'})
            # Keep only the last N messages
            # if len(chat_history) > HISTORY_SIZE:
            #     chat_history = chat_history[-20:]
            #     logging.info(
            #         f"Trimmed message history for chat {chat_id} to the last {HISTORY_SIZE} messages after bot response.")
        else:
            bot.reply_to(message, "Please provide a message after mentioning me.")
            logging.warning(f"User mentioned bot in chat {chat_id} but provided no message.")


def get_llm_response(messages):
    try:
        logging.info("Sending message history to OpenAI for response.")
        # Prepare the messages for OpenAI API
        simplified_messages = [{"role": "system", "content": bot_instruction}]
        for msg in messages:
            content = msg['content']
            simplified_messages.append({'role': msg['role'], 'content': content})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=simplified_messages
        )
        logging.info("Received response from OpenAI.")
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error communicating with OpenAI: {e}")
        return "Sorry, I'm having trouble processing your request right now."


def main():
    logging.info("Bot started. Listening for messages...")
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        if conn:
            conn.close()
        logging.info("Database connection closed.")


if __name__ == '__main__':
    main()
