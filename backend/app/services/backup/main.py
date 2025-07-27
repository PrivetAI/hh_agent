# backend/app/services/backup/main.py
import asyncio
import logging
import signal
import sys
from typing import Optional

from .backup_service import BackupService
from .telegram_bot import BackupBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

class BackupApp:
    def __init__(self):
        self.backup_service: Optional[BackupService] = None
        self.bot: Optional[BackupBot] = None
        self.running = False
    
    async def start(self):
        """Start the backup application"""
        try:
            logger.info("Starting Backup Application...")
            
            # Initialize services
            self.backup_service = BackupService()
            self.bot = BackupBot(self.backup_service)
            
            # Start scheduler
            self.backup_service.start_scheduler()
            
            # Run initial backup on startup
            logger.info("Running initial backup on startup...")
            await self.backup_service.run_backup()
            
            self.running = True
            
            # Start bot in background
            bot_task = asyncio.create_task(self.bot.start())
            
            # Keep running
            while self.running:
                await asyncio.sleep(1)
            
            # Cleanup
            await self.stop()
            
        except Exception as e:
            logger.error(f"Application error: {e}")
            await self.stop()
            sys.exit(1)
    
    async def stop(self):
        """Stop the application gracefully"""
        logger.info("Stopping Backup Application...")
        self.running = False
        
        if self.backup_service and self.backup_service.scheduler.running:
            self.backup_service.scheduler.shutdown()
        
        if self.bot:
            await self.bot.stop()
        
        logger.info("Backup Application stopped")
    
    def handle_signal(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}")
        self.running = False

async def main():
    """Main entry point"""
    app = BackupApp()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, app.handle_signal)
    signal.signal(signal.SIGTERM, app.handle_signal)
    
    await app.start()

if __name__ == "__main__":
    asyncio.run(main())