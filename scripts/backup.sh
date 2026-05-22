#!/bin/bash

# Script de backup automático para Papelería Yessy
# Uso en cron: 0 2 * * * /Users/johncruz/Desktop/Papeleria/scripts/backup.sh

PROJECT_DIR="/Users/johncruz/Desktop/Papeleria"
LOG_FILE="$PROJECT_DIR/backups/backup.log"

# Crear directorio si no existe
mkdir -p "$PROJECT_DIR/backups"

# Cambiar al directorio del proyecto
cd "$PROJECT_DIR"

# Ejecutar script de backup
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando backup..." >> "$LOG_FILE"

python3 backup_database.py >> "$LOG_FILE" 2>&1

# Registrar resultado
if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Backup completado" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Error en backup" >> "$LOG_FILE"
fi

if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Backup completado exitosamente" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Error durante el backup" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"
