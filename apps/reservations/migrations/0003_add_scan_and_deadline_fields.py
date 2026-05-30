from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservations', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tripreservation',
            name='scanned',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='tripreservation',
            name='scanned_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='tripreservation',
            name='confirm_deadline',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='tripreservation',
            name='reminder_sent',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='tripreservation',
            name='seat_number',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='tripreservation',
            name='trip_type',
            field=models.CharField(
                blank=True, default='go', max_length=10,
                choices=[('go', 'ذهاب'), ('return', 'عودة')]
            ),
        ),
        migrations.AddField(
            model_name='tripreservation',
            name='payment_method',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='tripreservation',
            name='payment_receipt',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='tripreservation',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending',         'معلقة'),
                    ('pending_confirm', 'بانتظار التأكيد'),
                    ('confirmed',       'مؤكدة'),
                    ('cancelled',       'ملغية'),
                    ('no_show',         'لم يحضر'),
                ],
                default='pending',
                max_length=20,
            ),
        ),
    ]
