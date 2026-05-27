from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q
from django.views.decorators.http import require_POST
from datetime import timedelta, date
import json

from .models import Habit, HabitCompletion

from .helpers import (
    calculate_streak,
    longest_streak,
    xp_and_level,
    badges,
    weekly_bar_data,
    heatmap_data,
    completions_today,
    get_today_range,
)

# ─── Views ──────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    user = request.user
    habits = Habit.objects.filter(user=user).order_by('created_at')

    # Build per-habit context
    habits_data = []
    for habit in habits:
        done_today = completions_today(habit)
        streak     = calculate_streak(habit)
        progress   = min(int(done_today / habit.target_per_day * 100), 100)
        habits_data.append({
            'id':           habit.id,
            'title':        habit.title,
            'icon':         habit.icon,
            'color':        habit.color,
            'periodicity':  habit.periodicity,
            'target':       habit.target_per_day,
            'done_today':   done_today,
            'progress':     progress,
            'streak':       streak,
            'completed':    done_today >= habit.target_per_day,
        })

    # Hero stats
    total = len(habits_data)
    completed_count = sum(1 for h in habits_data if h['completed'])
    completion_pct  = int(completed_count / total * 100) if total else 0
    overall_streak  = max((h['streak'] for h in habits_data), default=0)

    # Gamification
    xp, level, xp_in_level = xp_and_level(user)
    badges = badges(user, habits_data)

    # Analytics
    weekly_data = weekly_bar_data(user)
    heatmap     = heatmap_data(user)
    longest     = max(
        (longest_streak(h) for h in habits),
        default=0
    )
    longest_habit = None
    for h in habits:
        if longest_streak(h) == longest:
            longest_habit = h.title
            break

    # Hour-of-day greeting
    hour = timezone.localtime().hour
    if hour < 12:
        greeting = 'Good Morning'
    elif hour < 17:
        greeting = 'Good Afternoon'
    else:
        greeting = 'Good Evening'

    context = {
        'habits_data':      habits_data,
        'total_habits':     total,
        'completed_count':  completed_count,
        'completion_pct':   completion_pct,
        'overall_streak':   overall_streak,
        'greeting':         greeting,
        'xp':               xp,
        'level':            level,
        'xp_in_level':      xp_in_level,
        'badges':           badges,
        'weekly_data':      json.dumps(weekly_data),
        'heatmap':          json.dumps(heatmap),
        'longest_streak':   longest,
        'longest_habit':    longest_habit,
        'icon_choices':     Habit.ICON_CHOICES,
    }
    return render(request, 'habits/dashboard.html', context)
