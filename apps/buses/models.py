from django.db import models


class Bus(models.Model):
    plate_number = models.CharField(max_length=20, unique=True)
    capacity     = models.PositiveIntegerField()
    color        = models.CharField(max_length=50, blank=True)
    photo_path   = models.ImageField(upload_to='buses/', null=True, blank=True)

    class Meta:
        db_table  = 'buses'
        ordering  = ['plate_number']

    def __str__(self):
        return self.plate_number
