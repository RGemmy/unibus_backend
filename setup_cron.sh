#!/bin/bash
# =============================================================
#  UniBus — Scheduled Jobs Setup
#  شغّل هذا الملف مرة واحدة لتفعيل الـ cron jobs
# =============================================================
#
#  الأوامر المتاحة:
#    python manage.py auto_noshow             → يكشف الغائبين ويضيفهم لقائمة الانتظار
#    python manage.py auto_noshow --dry-run   → معاينة بدون تغيير
#    python manage.py send_confirm_reminders  → يبعت تذكيرات مهلة التأكيد
#
#  إضافة للـ crontab (crontab -e):
# =============================================================

PROJECT_DIR="/path/to/unibus-backend1"
PYTHON="/path/to/venv/bin/python"
LOG_DIR="$PROJECT_DIR/logs"

mkdir -p "$LOG_DIR"

CRON_JOBS='
# UniBus — كل 5 دقائق: اكشف الغائبين بعد انطلاق الرحلة
*/5 * * * * cd '"$PROJECT_DIR"' && '"$PYTHON"' manage.py auto_noshow >> '"$LOG_DIR"'/noshow.log 2>&1

# UniBus — كل 5 دقائق: ابعت تذكيرات مهلة التأكيد
*/5 * * * * cd '"$PROJECT_DIR"' && '"$PYTHON"' manage.py send_confirm_reminders >> '"$LOG_DIR"'/reminders.log 2>&1
'

echo "الأوامر المقترح إضافتها للـ crontab:"
echo "$CRON_JOBS"
echo ""
echo "لإضافتها تلقائياً، شغّل:"
echo "  (crontab -l 2>/dev/null; echo \"$CRON_JOBS\") | crontab -"
