#!/bin/bash

TIMESTAMP=`date +"%Y%m%d_%H%M%S"`
PWD=`pwd`
BACKUP_FULL="backup/KB4IT_CORE_DATASET_BACKUP-$TIMESTAMP.xml"
php maintenance/dumpBackup.php -q --current --pagelist=kb4it/etc/KB4IT_CORE_PAGELIST.txt > backup/KB4IT_CORE_DATASET_USER_SPACE.xml 
php maintenance/dumpBackup.php -q --current --filter=namespace:2,4,6,8,10,12,14,102,106 --include-files=backup/KB4IT_CORE_DATASET_USER_SPACE.xml > $BACKUP_FULL 
echo "KB4IT full backup done!"
echo "Saved to $PWD/$BACKUP_FULL"

