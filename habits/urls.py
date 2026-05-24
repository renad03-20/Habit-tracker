from django.urls import path
from . import views

app_name = 'habits'

urlpatterns = [
    # Dashboard (main page)
    path('',                         views.dashboard,        name='dashboard'),

    # Habit CRUD
    path('create/',                  views.habit_create,     name='habit_create'),
    path('<int:pk>/edit/',           views.habit_edit,       name='habit_edit'),
    path('<int:pk>/delete/',         views.habit_delete,     name='habit_delete'),

    # AJAX completion toggles
    path('<int:pk>/complete/',       views.habit_complete,   name='habit_complete'),
    path('<int:pk>/uncomplete/',     views.habit_uncomplete, name='habit_uncomplete'),
]