# backend/app/services/backup/telegram_bot.py
import os
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import aiofiles

from .backup_service import BackupService

logger = logging.getLogger(__name__)

class BackupBot:
    def __init__(self, backup_service: BackupService):
        self.backup_service = backup_service
        self.bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
        self.dp = Dispatcher()
        self.allowed_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        # Register handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register bot command handlers"""
        
        @self.dp.message(Command("start"))
        async def cmd_start(message: Message):
            if str(message.chat.id) != self.allowed_chat_id:
                return
            
            await message.answer(
                "🤖 HH Agent Backup Bot\n\n"
                "Available commands:\n"
                "/backup - Create backup now\n"
                "/status - Check backup status\n"
                "/help - Show this message"
            )
        
        @self.dp.message(Command("help"))
        async def cmd_help(message: Message):
            if str(message.chat.id) != self.allowed_chat_id:
                return
            
            await message.answer(
                "📋 Commands:\n\n"
                "/backup - Create database backup immediately\n"
                "/status - Show backup schedule and last backup time\n"
                "/restore - Instructions for restoring from backup\n\n"
                "⏰ Automatic backups run every hour"
            )
        
        @self.dp.message(Command("backup"))
        async def cmd_backup(message: Message):
            if str(message.chat.id) != self.allowed_chat_id:
                await message.answer("⛔ Unauthorized")
                return
            
            await message.answer("🔄 Starting manual backup...")
            
            # Run backup
            success = await self.backup_service.run_backup()
            
            if not success:
                await message.answer("❌ Manual backup failed. Check logs for details.")
        
        @self.dp.message(Command("status"))
        async def cmd_status(message: Message):
            if str(message.chat.id) != self.allowed_chat_id:
                return
            
            jobs = self.backup_service.scheduler.get_jobs()
            
            status_text = "📊 Backup Status\n\n"
            
            if jobs:
                for job in jobs:
                    status_text += f"📅 Schedule: Every hour at :00\n"
                    status_text += f"⏰ Next run: {job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    
                    if hasattr(job, 'last_run_time') and job.last_run_time:
                        status_text += f"✅ Last run: {job.last_run_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            else:
                status_text += "⚠️ No scheduled backups found"
            
            status_text += f"\n🗄 Database: {self.backup_service.db_name}"
            
            await message.answer(status_text)
        
        @self.dp.message(Command("restore"))
        async def cmd_restore(message: Message):
            if str(message.chat.id) != self.allowed_chat_id:
                return
            
            await message.answer(
                "🔧 Database Restore Instructions\n\n"
                "1. Download the backup file from chat\n"
                "2. Copy to server: `scp backup.sql.gz server:/tmp/`\n"
                "3. Run restore command:\n"
                "```\ndocker-compose -f docker-compose.prod.yml run --rm backup-hh restore /tmp/backup.sql.gz\n```\n\n"
                "⚠️ Warning: This will replace all existing data!"
            )
        
        @self.dp.message()
        async def handle_document(message: Message):
            """Handle backup file uploads for restore"""
            if str(message.chat.id) != self.allowed_chat_id:
                return
            
            if not message.document:
                return
            
            # Check if it's a backup file
            if not (message.document.file_name.endswith('.sql.gz') or 
                    message.document.file_name.endswith('.sql')):
                return
            
            await message.answer(
                "📦 Backup file received\n\n"
                "To restore this backup:\n"
                "1. Download the file\n"
                "2. Copy to your server\n"
                "3. Run the restore command shown in /restore"
            )
    
    async def start(self):
        """Start the bot"""
        logger.info("Starting Telegram bot...")
        
        # Send startup message
        await self.bot.send_message(
            self.allowed_chat_id,
            "🚀 Backup bot started!\n"
            "Automatic backups scheduled every hour.\n"
            "Use /help to see available commands."
        )
        
        # Start polling
        await self.dp.start_polling(self.bot)
    
    async def stop(self):
        """Stop the bot"""
        logger.info("Stopping Telegram bot...")
        await self.bot.session.close()