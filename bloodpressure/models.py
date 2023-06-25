from django.db import models

class BloodPressure(models.Model):
    systolic = models.IntegerField()
    diastolic = models.IntegerField()
    measured_at = models.DateTimeField()

    def __str__(self):
        return f"Systolic: {self.systolic}, Diastolic: {self.diastolic}, Measured At: {self.measured_at}"
