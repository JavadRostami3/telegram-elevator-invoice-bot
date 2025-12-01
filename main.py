"""
Main Bot Application
Entry point for the Telegram bot
"""
import logging
import os
import sys

from telegram.ext import Application

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from bot.handlers import setup_handlers
from bot.admin import setup_admin_handlers
from db import DatabaseManager

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Start the bot"""
    # Validate configuration
    if config.BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        logger.error("❌ Please set BOT_TOKEN in config.py or environment variable")
        logger.error("   You can create a bot token by talking to @BotFather on Telegram")
        return
    
    # Initialize database
    logger.info("Initializing database...")
    db = DatabaseManager(config.DATABASE_PATH)
    
    # Create output directory if not exists
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    
    # Create bot application
    logger.info("Creating bot application...")
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Setup handlers
    logger.info("Setting up handlers...")
    setup_handlers(application)
    setup_admin_handlers(application, db)
    
    # Start bot
    logger.info("Starting bot...")
    logger.info("Bot is running! Press Ctrl+C to stop.")
    
    application.run_polling(allowed_updates=True)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
