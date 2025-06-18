#!/bin/bash
  
# Restore database and uploads from backup location
# Source: /root/vibedodo_db_backup/
# Target: /home/varun/apps/vibedodo/

BACKUP_DIR="/root/vibedodo_db_backup"
APP_DIR="/root/vibedodo"

echo "Starting restoration process..."

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Error: Backup directory $BACKUP_DIR does not exist"
    exit 1
fi

# Check if required backup files exist
if [ ! -f "$BACKUP_DIR/site.db" ]; then
    echo "Error: Database backup $BACKUP_DIR/site.db not found"
    exit 1
fi

if [ ! -d "$BACKUP_DIR/uploads" ]; then
    echo "Error: Uploads backup directory $BACKUP_DIR/uploads not found"
    exit 1
fi

# Stop the application (if running as a service)
# Uncomment the appropriate line below based on your setup:
# systemctl stop vibedodo
# docker-compose down
# pkill -f "python.*run.py"


echo "Copying database from backup..."
cp "$BACKUP_DIR/site.db" "$APP_DIR/instance/site.db"

echo "Copying uploads from backup..."
cp -r "$BACKUP_DIR/uploads/"* "$APP_DIR/app/static/uploads/"

echo "adding jwt_refresh column to db"
cd /root/vibedodo && source venv/bin/activate && python3 migrate_jwt.py


# Set correct permissions
#chown -R varun:varun "$APP_DIR/instance/site.db"
#chown -R varun:varun "$APP_DIR/app/static/uploads"

#echo "Setting file permissions..."
#chmod 644 "$APP_DIR/instance/site.db"
#chmod -R 755 "$APP_DIR/app/static/uploads"

# Start the application (if running as a service)
# Uncomment the appropriate line below based on your setup:
# systemctl start vibedodo
# docker-compose up -d
# cd "$APP_DIR" && python run.py &

echo "Restoration completed successfully!"
echo "Database restored: $APP_DIR/instance/site.db"
echo "Uploads restored: $APP_DIR/app/static/uploads"
