from django.db import models

class Place(models.Model):
    place_name = models.CharField(max_length=200, unique=True)
    class Meta:
        db_table = 'places'
    def __str__(self): return self.place_name

class Route(models.Model):
    start_point = models.CharField(max_length=200)
    end_point   = models.CharField(max_length=200)
    class Meta:
        db_table = 'routes'
    def __str__(self): return f"{self.start_point} → {self.end_point}"

class Schedule(models.Model):
    route         = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='schedules')
    schedule_time = models.TimeField()
    class Meta:
        db_table = 'schedules'
    def __str__(self): return f"{self.route} @ {self.schedule_time}"
