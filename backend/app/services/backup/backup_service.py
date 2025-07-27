# backend/app/services/backup/backup_service.py
import os
import subprocess
import gzip
import asyncio
import logging
from datetime import datetime
from typing import Optional
import aiofiles
from aiogram import Bot
from aiogram.types import InputFile, FSInputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

class BackupService:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.db_url = os.getenv("DATABASE_URL")
        
        if not all([self.bot_token, self.chat_id]):
            raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")
        
        self.bot = Bot(token=self.bot_token)
        self.scheduler = AsyncIOScheduler()
        
        # Parse database URL
        self._parse_db_url()
        
    def _parse_db_url(self):
        """Parse PostgreSQL connection URL"""
        # postgresql://user:password@host:port/database
        import re
        pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
        match = re.match(pattern, self.db_url)
        
        if not match:
            raise ValueError("Invalid DATABASE_URL format")
        
        self.db_user = match.group(1)
        self.db_password = match.group(2)
        self.db_host = match.group(3)
        self.db_port = match.group(4)
        self.db_name = match.group(5)
    
    async def create_backup(self) -> Optional[str]:
        """Create database backup and return compressed file path"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dump_file = f"/tmp/backup_{timestamp}.sql"
        compressed_file = f"/tmp/backup_{timestamp}.sql.gz"
        
        try:
            # Create dump
            logger.info(f"Creating database dump: {dump_file}")
            
            dump_command = [
                "pg_dump",
                f"--host={self.db_host}",
                f"--port={self.db_port}",
                f"--username={self.db_user}",
                f"--dbname={self.db_name}",
                "--no-password",
                "--clean",
                "--if-exists",
                "--verbose",
                f"--file={dump_file}"
            ]
            
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_password
            
            result = subprocess.run(
                dump_command,
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"pg_dump failed: {result.stderr}")
                return None
            
            # Compress dump
            logger.info(f"Compressing dump to: {compressed_file}")
            
            with open(dump_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb', compresslevel=9) as f_out:
                    f_out.write(f_in.read())
            
            # Remove uncompressed dump
            os.remove(dump_file)
            
            # Get file size
            file_size = os.path.getsize(compressed_file)
            logger.info(f"Backup created: {compressed_file} ({file_size / 1024 / 1024:.2f} MB)")
            
            return compressed_file
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            # Cleanup
            for f in [dump_file, compressed_file]:
                if os.path.exists(f):
                    os.remove(f)
            return None
    
    async def send_to_telegram(self, file_path: str) -> bool:
        """Send backup file to Telegram"""
        try:
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            
            # Telegram file size limit is 50MB
            if file_size > 50 * 1024 * 1024:
                await self.bot.send_message(
                    self.chat_id,
                    f"⚠️ Backup file too large: {file_size / 1024 / 1024:.2f} MB\n"
                    f"Maximum allowed: 50 MB"
                )
                return False
            
            # Send file
            logger.info(f"Sending backup to Telegram: {file_name}")
            
            caption = (
                f"🗄 Database Backup\n"
                f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"📦 Size: {file_size / 1024 / 1024:.2f} MB\n"
                f"🏷 Database: {self.db_name}"
            )
            
            document = FSInputFile(file_path, filename=file_name)
            await self.bot.send_document(
                self.chat_id,
                document,
                caption=caption
            )
            
            logger.info("Backup sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send backup to Telegram: {e}")
            return False
    
    async def run_backup(self) -> bool:
        """Run complete backup process"""
        logger.info("Starting backup process...")
        
        try:
            # Notify start
            await self.bot.send_message(
                self.chat_id,
                "🔄 Starting database backup..."
            )
            
            # Create backup
            backup_file = await self.create_backup()
            
            if not backup_file:
                await self.bot.send_message(
                    self.chat_id,
                    "❌ Backup creation failed!"
                )
                return False
            
            # Send to Telegram
            success = await self.send_to_telegram(backup_file)
            
            # Cleanup - always remove local file
            if os.path.exists(backup_file):
                os.remove(backup_file)
                logger.info(f"Removed local backup file: {backup_file}")
            
            if success:
                await self.bot.send_message(
                    self.chat_id,
                    "✅ Backup completed successfully!"
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Backup process failed: {e}")
            await self.bot.send_message(
                self.chat_id,
                f"❌ Backup error: {str(e)}"
            )
            return False
    
    def start_scheduler(self):
        """Start scheduled backups"""
        # Schedule hourly backups
        self.scheduler.add_job(
            self.run_backup,
            CronTrigger(minute=0),  # Every hour at :00
            id="hourly_backup",
            name="Hourly database backup",
            misfire_grace_time=300  # 5 minutes grace time
        )
        
        self.scheduler.start()
        logger.info("Backup scheduler started - running every hour")
    
    async def restore_from_file(self, file_path: str) -> bool:
        """Restore database from backup file"""
        try:
            # Decompress if needed
            if file_path.endswith('.gz'):
                logger.info("Decompressing backup file...")
                decompressed_file = file_path.replace('.gz', '')
                
                with gzip.open(file_path, 'rb') as f_in:
                    with open(decompressed_file, 'wb') as f_out:
                        f_out.write(f_in.read())
                
                restore_file = decompressed_file
            else:
                restore_file = file_path
            
            # Restore database
            logger.info(f"Restoring database from: {restore_file}")
            
            restore_command = [
                "psql",
                f"--host={self.db_host}",
                f"--port={self.db_port}",
                f"--username={self.db_user}",
                f"--dbname={self.db_name}",
                "--no-password",
                f"--file={restore_file}"
            ]
            
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_password
            
            result = subprocess.run(
                restore_command,
                env=env,
                capture_output=True,
                text=True
            )
            
            # Cleanup
            if file_path.endswith('.gz') and os.path.exists(decompressed_file):
                os.remove(decompressed_file)
            
            if result.returncode != 0:
                logger.error(f"Restore failed: {result.stderr}")
                return False
            
            logger.info("Database restored successfully")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False