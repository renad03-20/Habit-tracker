from django.db import models
from django.conf import settings

class Habit(models.Model):

    PERIOD_CHOICES = [
        ('daily',  'Daily'),
        ('weekly', 'Weekly'),
    ]

    ICON_CHOICES = [
        ('💧', 'Water'),
        ('🏃', 'Run'),
        ('📚', 'Read'),
        ('🧘', 'Meditate'),
        ('💪', 'Workout'),
        ('🥗', 'Eat Healthy'),
        ('😴', 'Sleep'),
        ('✍️', 'Write'),
        ('🎯', 'Focus'),
        ('🎨', 'Create'),
        ('🌿', 'Nature'),
        ('💊', 'Medicine'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    title = models.CharField(max_length=50)

    icon = models.CharField(
        max_length=10,
        choices=ICON_CHOICES,
        default='🎯',
    )

    color = models.CharField(
        max_length=7,
        default='#3b82f6',
    )

    periodicity = models.CharField(
        max_length=10,
        choices=PERIOD_CHOICES,
        default='daily',
    )

    target_per_day = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.icon} {self.title}"


class HabitCompletion(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='completions')
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-completed_at']

    def __str__(self):
        return f"{self.habit.title} — {self.completed_at:%Y-%m-%d %H:%M}"