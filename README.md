# Telegram Bot with OpenAI Integration - README

## Overview

This project is a Telegram bot that integrates with OpenAI's GPT model to provide intelligent responses to user messages. The bot stores chat history in a SQLite database for context-aware conversations and supports various features such as mentions, replies, and forwarded messages.

---

## Features

- **AI-Powered Conversations**: Integrates with OpenAI's GPT models for dynamic and context-aware responses.
- **Message History Management**: Maintains recent chat history to provide context in conversations.
- **Database Integration**: Uses SQLite for storing chat history (optional, controlled by environment variables).
- **Trigger Mechanisms**: Responds to direct mentions, replies to bot messages, and forwarded messages that mention the bot.
- **Robust Logging**: Logs all activities and errors for monitoring and debugging.

---

## Prerequisites

1. Python 3.8 or higher
2. Telegram Bot Token (create a bot via [BotFather](https://core.telegram.org/bots#botfather))
3. OpenAI API Key
4. SQLite (optional for database functionality)

---

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repository_url>
   cd <repository_name>
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables**:
   Create a `.env` file in the root directory with the following keys:
   ```env
   TG_BOT_TOKEN=<your_telegram_bot_token>
   OPENAI_API_KEY=<your_openai_api_key>
   NO_DB_REWRITE=false # Set to 'true' to disable database usage
   ```

4. **Database Initialization**:
   The bot automatically creates the necessary SQLite database and table if `NO_DB_REWRITE` is `false`.

---

## Usage

1. **Run the Bot**:
   ```bash
   python bot.py
   ```

2. **Interacting with the Bot**:
   - Mention the bot in a group using `@<bot_username>` to trigger a response.
   - Reply to a message from the bot to continue the conversation.
   - Forward a message mentioning the bot for context-aware replies.

---

## Key Components

### Bot Configuration
- **`load_dotenv()`**: Loads environment variables from the `.env` file.
- **Logging**: Configured for detailed logs of bot activities.

### Database Integration
- **SQLite**: Used to store and retrieve chat history.
- **`NO_DB_REWRITE`**: Environment variable to toggle database usage.

### Chat History
- **In-Memory Cache**: Stores recent messages for context.
- **History Trimming**: Keeps only the last 10 messages to conserve memory.

### OpenAI Integration
- **`get_llm_response()`**: Sends chat history to OpenAI's API and retrieves a response.

### Trigger Mechanisms
- **Mentions**: Responds when the bot is mentioned in a message.
- **Replies**: Detects when a message is a reply to the bot.
- **Forwards**: Handles forwarded messages that mention the bot.

---

## Error Handling

- Logs errors for debugging.
- Sends fallback messages if OpenAI API calls fail.

---

## Extending the Bot

1. **Add New Handlers**:
   Use `@bot.message_handler` decorators to add custom behaviors.

2. **Customize Responses**:
   Modify `get_llm_response()` or the system prompt in `bot_instruction`.

3. **Integrate New Features**:
   Add modules to handle new content types (e.g., images, stickers).

---

## Troubleshooting

1. **Bot Token Missing**:
   Ensure `TG_BOT_TOKEN` is set in the `.env` file.

2. **Database Errors**:
   Verify write permissions in the project directory or set `NO_DB_REWRITE` to `true`.

3. **OpenAI Issues**:
   Ensure the OpenAI API key is valid and the account has sufficient usage credits.

---

## License

This project is open-source and available under the [MIT License](LICENSE).

---

## Contact

For support or feedback, please reach out via [GitHub Issues](<repository_issues_url>).