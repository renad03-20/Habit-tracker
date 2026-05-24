# Momentum — Habit Tracker

A full-stack habit tracking web app built with Django. Track daily and weekly habits, visualize streaks, earn XP and badges, and stay consistent with a GitHub-style activity heatmap.

---

## Features

- **Authentication** — sign up, email verification, login/logout, password reset, account lockout after failed attempts
- **Habit management** — create, edit, and delete habits with a custom icon, color, periodicity, and daily goal
- **Daily check-ins** — complete habits from the dashboard with instant AJAX updates (no page reload)
- **Streaks** — current and all-time longest streak tracked per habit
- **Gamification** — XP points, levels, and achievement badges (7-day streak, 30-day streak, perfect week, etc.)
- **Analytics panel** — weekly bar chart, circular completion ring, and a GitHub-style 18-week activity heatmap
- **Dark / light mode** — toggle in the navbar, applied instantly via CSS variables
- **Responsive layout** — two-column dashboard that stacks on smaller screens

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.13, Django 6 |
| Frontend | Bootstrap 5, Chart.js 4 |
| Fonts | Syne (display), DM Sans (body) |
| Database | SQLite (dev) |
| Auth | Custom user model (email-based) |

---

## Project Structure

```
habit_tracker/
├── accounts/                   # Authentication app
│   ├── models.py               # Custom User, tokens, login sessions
│   ├── views.py                # Signup, login, logout, password reset
│   ├── forms.py
│   ├── emails.py
│   └── urls.py
│
├── habits/                     # Core app
│   ├── models.py               # Habit, HabitCompletion
│   ├── views.py                # Dashboard, CRUD, AJAX endpoints
│   ├── urls.py
│   └── templates/
│       └── habits/
│           ├── base.html       # Shared navbar layout
│           └── dashboard.html  # Main dashboard
│
├── habit_tracker/              # Project config
│   ├── settings.py
│   └── urls.py
│
├── manage.py
└── requirements.txt
```

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/your-username/habit-tracker.git
cd habit-tracker
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

### 5. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Start the development server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` — you'll be redirected to login.

---

## Data Models

### `Habit`

| Field | Type | Notes |
|---|---|---|
| `user` | FK → `AUTH_USER_MODEL` | Owner of the habit |
| `title` | CharField(50) | Habit name |
| `icon` | CharField | Emoji from 12 preset choices |
| `color` | CharField(7) | Hex color, default `#3b82f6` |
| `periodicity` | CharField | `daily` or `weekly` |
| `target_per_day` | PositiveIntegerField | Completions needed per day |
| `created_at` | DateTimeField | Auto-set on creation |

### `HabitCompletion`

| Field | Type | Notes |
|---|---|---|
| `habit` | FK → `Habit` | Related habit |
| `completed_at` | DateTimeField | Auto-set timestamp |

---

## URL Routes

| URL | View | Description |
|---|---|---|
| `/` | `dashboard` | Main dashboard |
| `/create/` | `habit_create` | POST — create a habit |
| `/<pk>/edit/` | `habit_edit` | POST — update a habit |
| `/<pk>/delete/` | `habit_delete` | POST — delete a habit |
| `/<pk>/complete/` | `habit_complete` | POST (AJAX) — log a completion |
| `/<pk>/uncomplete/` | `habit_uncomplete` | POST (AJAX) — remove last completion |
| `/accounts/signup/` | `signup_view` | Registration |
| `/accounts/login/` | `login_view` | Login |
| `/accounts/logout/` | `logout_view` | Logout (POST) |
| `/accounts/password-reset/` | `password_reset_request_view` | Request reset email |

---

## Gamification System

| Mechanic | Rule |
|---|---|
| XP | 10 XP per completion |
| Level | Level up every 100 XP |
| 🌱 First Step | Complete any habit once |
| 🔥 7-Day Streak | Maintain a 7-day streak on any habit |
| 💎 30-Day Streak | Maintain a 30-day streak on any habit |
| ⭐ Perfect Week | Complete all daily habits every day for a full week |
| 🏆 Consistency King | Reach 50 total completions |

---

## License

MIT