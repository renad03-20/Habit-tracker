from django.db import models
from django.contrib.auth.models import User

# a model for habits 
class Habit(models.Model):

    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    title = models.CharField(max_length=50)

    color = models.CharField(
        max_length=7,
        default='#3b82f6'
    )

    periodicity = models.CharField(
        max_length=10,
        choices=PERIOD_CHOICES
    )

    target_per_day = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title