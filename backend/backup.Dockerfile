# backend/backup.Dockerfile
FROM python:3.11-slim

# Install PostgreSQL client tools
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir \
    aiogram==3.2.0 \
    apscheduler==3.10.4 \
    aiofiles==23.2.1 \
    psycopg2-binary==2.9.9

# Copy backup service files
COPY app/services/backup/ /app/backup/

# Create entrypoint script
RUN echo '#!/bin/bash\n\
if [ "$1" = "restore" ]; then\n\
    # Restore mode\n\
    if [ -z "$2" ]; then\n\
        echo "Usage: docker-compose run backup-hh restore /path/to/backup.sql.gz"\n\
        exit 1\n\
    fi\n\
    python -c "import asyncio; from backup.backup_service import BackupService; \
    service = BackupService(); \
    asyncio.run(service.restore_from_file(\"$2\"))"\n\
else\n\
    # Normal backup service mode\n\
    python -m backup.main\n\
fi' > /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]