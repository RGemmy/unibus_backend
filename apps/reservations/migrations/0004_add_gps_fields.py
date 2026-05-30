from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Migration لإضافة حقول GPS لجدول trip_reservations.
    
    الحقول الجديدة:
      - gps_latitude    : خط العرض (Decimal)
      - gps_longitude   : خط الطول (Decimal)
      - gps_updated_at  : وقت آخر تحديث للموقع
      - gps_sharing     : هل الطالب فعّل مشاركة الموقع؟
    """

    dependencies = [
        ('reservations', '0003_add_scan_and_deadline_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='tripreservation',
            name='gps_latitude',
            field=models.DecimalField(
                max_digits=9, decimal_places=6,
                null=True, blank=True,
                verbose_name='خط العرض',
            ),
        ),
        migrations.AddField(
            model_name='tripreservation',
            name='gps_longitude',
            field=models.DecimalField(
                max_digits=9, decimal_places=6,
                null=True, blank=True,
                verbose_name='خط الطول',
            ),
        ),
        migrations.AddField(
            model_name='tripreservation',
            name='gps_updated_at',
            field=models.DateTimeField(
                null=True, blank=True,
                verbose_name='وقت آخر تحديث GPS',
            ),
        ),
        migrations.AddField(
            model_name='tripreservation',
            name='gps_sharing',
            field=models.BooleanField(
                default=False,
                verbose_name='مشاركة الموقع فعّالة؟',
            ),
        ),
    ]
