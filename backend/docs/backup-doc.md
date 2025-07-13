# Database Backup Service

Автоматический сервис резервного копирования БД с отправкой в Telegram.

## Возможности

- ✅ Автоматический backup каждый час
- ✅ Сжатие дампов (gzip)
- ✅ Отправка в Telegram
- ✅ Ручной запуск через бота
- ✅ Восстановление из backup
- ✅ Без локального хранения

## Настройка

### 1. Создание Telegram бота

1. Откройте [@BotFather](https://t.me/botfather)
2. Отправьте `/newbot`
3. Придумайте имя и username для бота
4. Сохраните токен

### 2. Получение Chat ID

1. Отправьте любое сообщение вашему боту
2. Откройте: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Найдите `"chat":{"id":123456789}` - это ваш Chat ID

### 3. Настройка .env

```bash
# Добавьте в .env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

## Команды бота

- `/start` - Приветствие
- `/help` - Список команд
- `/backup` - Создать backup сейчас
- `/status` - Статус и расписание
- `/restore` - Инструкции по восстановлению

## Запуск

```bash
# Production
docker-compose -f docker-compose.prod.yml up -d

# Проверка логов
docker-compose -f docker-compose.prod.yml logs -f backup-hh
```

## Восстановление из backup

### Способ 1: Через Docker Compose

```bash
# Скачайте файл backup из Telegram
# Скопируйте на сервер
scp backup_20240115_120000.sql.gz server:/tmp/

# Восстановите БД
docker-compose -f docker-compose.prod.yml run --rm backup-hh restore /tmp/backup_20240115_120000.sql.gz
```

### Способ 2: Напрямую

```bash
# Распакуйте архив
gunzip backup_20240115_120000.sql.gz

# Восстановите
docker exec -i hhagent_postgres psql -U hhuser -d hhapp < backup_20240115_120000.sql
```

## Мониторинг

### Проверка работы scheduler

```bash
docker-compose -f docker-compose.prod.yml logs backup-hh | grep