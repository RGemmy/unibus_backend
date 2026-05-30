import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('reservations', '0003_add_scan_and_deadline_fields'),
        ('students',     '0002_initial'),
        ('trips',        '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='WaitlistEntry',
            fields=[
                ('id',               models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('amount_paid',      models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('resolution',       models.CharField(
                    choices=[
                        ('pending',  'بانتظار اختيار الطالب'),
                        ('refund',   'استرداد المبلغ'),
                        ('credit',   'رصيد لرحلة تانية'),
                        ('resolved', 'تم الحل'),
                    ],
                    default='pending', max_length=20
                )),
                ('resolution_notes',   models.TextField(blank=True)),
                ('created_at',         models.DateTimeField(auto_now_add=True)),
                ('resolved_at',        models.DateTimeField(blank=True, null=True)),
                ('credit_valid_until', models.DateField(blank=True, null=True)),
                ('alternatives_sent',  models.BooleanField(default=False)),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='waitlist_entries',
                    to='students.student'
                )),
                ('trip', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='waitlist_entries',
                    to='trips.trip'
                )),
                ('reservation', models.OneToOneField(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='waitlist_entry',
                    to='reservations.tripreservation'
                )),
                ('credit_used_trip', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='used_credits',
                    to='trips.trip'
                )),
            ],
            options={'db_table': 'waitlist_entries', 'ordering': ['-created_at']},
        ),
        migrations.AddConstraint(
            model_name='waitlistentry',
            constraint=models.UniqueConstraint(fields=['student', 'trip'], name='unique_student_trip_waitlist'),
        ),
        migrations.CreateModel(
            name='CreditBalance',
            fields=[
                ('id',          models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('balance',     models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('valid_until', models.DateField(blank=True, null=True)),
                ('created_at',  models.DateTimeField(auto_now_add=True)),
                ('updated_at',  models.DateTimeField(auto_now=True)),
                ('student', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='credit_balance',
                    to='students.student'
                )),
                ('source_entry', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='+',
                    to='waitlist.waitlistentry'
                )),
            ],
            options={'db_table': 'credit_balances'},
        ),
        migrations.CreateModel(
            name='StudentNotification',
            fields=[
                ('id',         models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('type',       models.CharField(
                    choices=[
                        ('confirm_reminder', 'تذكير بالتأكيد'),
                        ('no_show',          'غياب عن الرحلة'),
                        ('alternatives',     'رحلات بديلة'),
                        ('refund_initiated', 'استرداد بدأ'),
                        ('credit_added',     'رصيد أضيف'),
                        ('general',          'عام'),
                    ],
                    default='general', max_length=30
                )),
                ('title_ar',   models.CharField(max_length=200)),
                ('title_en',   models.CharField(blank=True, max_length=200)),
                ('body_ar',    models.TextField()),
                ('body_en',    models.TextField(blank=True)),
                ('is_read',    models.BooleanField(default=False)),
                ('data',       models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notifications',
                    to='students.student'
                )),
            ],
            options={'db_table': 'student_notifications', 'ordering': ['-created_at']},
        ),
    ]
