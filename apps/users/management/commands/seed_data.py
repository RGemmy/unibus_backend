from django.core.management.base import BaseCommand
from datetime import date, time, timedelta


class Command(BaseCommand):
    help = 'Seed database with demo data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding...')

        from apps.users.models import Role, User, Driver
        roles = {}
        for r in ['admin', 'student', 'driver', 'university_mod', 'bus_mod']:
            role, _ = Role.objects.get_or_create(name=r)
            roles[r] = role
        # Keep backward compat
        roles['moderator'] = roles['university_mod']

        if not User.objects.filter(email='admin@unibus.sa').exists():
            User.objects.create_superuser(
                email='admin@unibus.sa', password='admin123',
                user_name='Ahmed Admin', role=roles['admin'],
            )

        from apps.students.models import University, Student
        unis = [University.objects.get_or_create(name=n)[0] for n in [
            'King Saud University', 'Prince Sultan University',
            'Imam University', 'King Abdulaziz University',
        ]]

        from apps.routes.models import Place, Route, Schedule
        places = [Place.objects.get_or_create(place_name=n)[0] for n in [
            'King Saud University', 'Prince Sultan University',
            'Imam University', 'King Abdulaziz University',
        ]]

        route, _ = Route.objects.get_or_create(
            start_point='Riyadh - Al Nuzha', end_point='King Saud University')
        schedule, _ = Schedule.objects.get_or_create(route=route, schedule_time=time(7, 30))

        from apps.buses.models import Bus
        buses = [Bus.objects.get_or_create(
            plate_number=p, defaults={'capacity': c, 'color': col})[0]
            for p, c, col in [
                ('ABC 123', 45, 'White'), ('DEF 456', 50, 'Yellow'),
                ('GHI 789', 40, 'White'), ('JKL 012', 45, 'Blue'),
            ]]

        for name, email, lic, exp in [
            ('Khalid Driver', 'driver1@unibus.sa', 'DL-001', date(2027, 6, 15)),
            ('Fahad Driver',  'driver2@unibus.sa', 'DL-002', date(2026, 8, 20)),
        ]:
            if not User.objects.filter(email=email).exists():
                u = User.objects.create_user(
                    email=email, password='driver123',
                    user_name=name, role=roles['driver'],
                )
                Driver.objects.create(
                    user=u, license_number=lic, license_expiry_date=exp,
                    next_drug_test_date=date.today() + timedelta(days=90),
                )

        students = []
        for name, email, uni_i in [
            ('Sara Ahmed',    'sara@student.sa',  0),
            ('Mohammed K',    'moh@student.sa',   1),
            ('Noura Salman',  'noura@student.sa', 2),
        ]:
            if not User.objects.filter(email=email).exists():
                u = User.objects.create_user(
                    email=email, password='student123',
                    user_name=name, role=roles['student'],
                )
                s = Student.objects.create(
                    user=u, faculty='Engineering', program='CS', university=unis[uni_i])
                students.append(s)

        from apps.trips.models import Trip
        for i, (place, bus) in enumerate(zip(places[:3], buses[:3])):
            Trip.objects.get_or_create(
                place=place, bus=bus, schedule=schedule,
                trip_date=date.today() + timedelta(days=i),
                defaults={'status': 'active'},
            )

        from apps.payments.models import PaymentType
        for pt in ['Credit Card', 'Bank Transfer', 'Cash', 'App Payment']:
            PaymentType.objects.get_or_create(payment_type_name=pt)

        self.stdout.write(self.style.SUCCESS('Done! admin@unibus.sa / admin123'))
