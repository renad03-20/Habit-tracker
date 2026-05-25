from datetime import timedelta, date
from django.db.models import Count, Q
from django.utils import timezone
from .models import Habit, HabitCompletion


def get_today_range():
    now = timezone.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end   = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start, end


def completions_today(habit):
    start, end = get_today_range()
    return HabitCompletion.objects.filter(
        habit=habit,
        completed_at__range=(start, end)
    ).count()


def calculate_streak(habit):
    """Count consecutive days (or weeks) with at least one completion."""
    today = timezone.now().date()
    streak = 0

    if habit.periodicity == 'daily':
        cursor = today
        while True:
            day_start = timezone.make_aware(
                timezone.datetime.combine(cursor, timezone.datetime.min.time())
            )
            day_end = timezone.make_aware(
                timezone.datetime.combine(cursor, timezone.datetime.max.time())
            )
            done = HabitCompletion.objects.filter(
                habit=habit,
                completed_at__range=(day_start, day_end)
            ).exists()
            if done:
                streak += 1
                cursor -= timedelta(days=1)
            else:
                break
    else:  # weekly
        cursor = today - timedelta(days=today.weekday())  # this Monday
        while True:
            week_start = timezone.make_aware(
                timezone.datetime.combine(cursor, timezone.datetime.min.time())
            )
            week_end = week_start + timedelta(days=7)
            done = HabitCompletion.objects.filter(
                habit=habit,
                completed_at__range=(week_start, week_end)
            ).exists()
            if done:
                streak += 1
                cursor -= timedelta(weeks=1)
            else:
                break

    return streak


def longest_streak(habit):
    """Calculate all-time longest streak."""
    completions = (
        HabitCompletion.objects.filter(habit=habit)
        .order_by('completed_at')
        .values_list('completed_at', flat=True)
    )
    if not completions:
        return 0

    dates = sorted({c.date() for c in completions})
    longest = current = 1
    for i in range(1, len(dates)):
        delta = (dates[i] - dates[i - 1]).days
        if delta == 1:
            current += 1
            longest = max(longest, current)
        elif delta > 1:
            current = 1
    return longest


def xp_and_level(user):
    """Simple XP/level system: 10 XP per completion."""
    total_completions = HabitCompletion.objects.filter(habit__user=user).count()
    xp = total_completions * 10
    level = 1 + xp // 100          # level up every 100 XP
    xp_in_level = xp % 100         # progress within current level
    return xp, level, xp_in_level


def badges(user, habits_data):
    """Return earned badge keys."""
    badges = []
    total_completions = HabitCompletion.objects.filter(habit__user=user).count()

    max_streak = max((h['streak'] for h in habits_data), default=0)
    if max_streak >= 7:
        badges.append({'icon': '🔥', 'label': '7-Day Streak'})
    if max_streak >= 30:
        badges.append({'icon': '💎', 'label': '30-Day Streak'})

    # Perfect week: all daily habits completed every day this week
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    daily_habits = [h for h in habits_data if h['periodicity'] == 'daily']
    if daily_habits:
        perfect = all(
            HabitCompletion.objects.filter(
                habit__id=h['id'],
                completed_at__date__gte=week_start,
                completed_at__date__lte=today,
            ).values('completed_at__date').distinct().count()
            == (today - week_start).days + 1
            for h in daily_habits
        )
        if perfect and (today - week_start).days >= 6:
            badges.append({'icon': '⭐', 'label': 'Perfect Week'})

    if total_completions >= 1:
        badges.append({'icon': '🌱', 'label': 'First Step'})
    if total_completions >= 50:
        badges.append({'icon': '🏆', 'label': 'Consistency King'})

    return badges


def weekly_bar_data(user):
    """Returns dict {weekday_name: completion_count} for the last 7 days."""
    today = timezone.now().date()
    data = {}
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = HabitCompletion.objects.filter(
            habit__user=user,
            completed_at__date=day
        ).count()
        data[day.strftime('%a')] = count
    return data


def heatmap_data(user, weeks=18):
    """Returns list of {date, count} for the last `weeks` weeks."""
    today = timezone.now().date()
    start = today - timedelta(weeks=weeks)
    completions = (
        HabitCompletion.objects.filter(
            habit__user=user,
            completed_at__date__gte=start,
        )
        .values('completed_at__date')
        .annotate(count=Count('id'))
    )
    lookup = {c['completed_at__date']: c['count'] for c in completions}

    result = []
    cursor = start
    while cursor <= today:
        result.append({'date': cursor.isoformat(), 'count': lookup.get(cursor, 0)})
        cursor += timedelta(days=1)
    return result
