# File: database.py
from tinydb import TinyDB, Query

# Initialize a simple file-based database
db = TinyDB('focusflow_db.json')
users_table = db.table('users')
gamification_table = db.table('gamification')

def save_user_profile(user_id, profile_data):
    """Saves or updates a user's profile."""
    User = Query()
    users_table.upsert({'user_id': user_id, **profile_data}, User.user_id == user_id)
    print(f"Profile saved for user {user_id}")

def get_user_profile(user_id):
    """Retrieves a user's profile."""
    User = Query()
    result = users_table.get(User.user_id == user_id)
    return result

def init_gamification_stats(user_id):
    """Initializes gamification stats for a new user."""
    Stats = Query()
    if not gamification_table.contains(Stats.user_id == user_id):
        gamification_table.insert({'user_id': user_id, 'level': 1, 'points': 0, 'focus_sessions': 0})
    print(f"Gamification stats initialized for user {user_id}")

def get_gamification_stats(user_id):
    """Retrieves gamification stats."""
    Stats = Query()
    return gamification_table.get(Stats.user_id == user_id)

def update_gamification_stats(user_id, points_to_add=0, sessions_to_add=0):
    """Updates points and focus sessions, and handles leveling up."""
    Stats = Query()
    user_stats = gamification_table.get(Stats.user_id == user_id)
    if user_stats:
        new_points = user_stats['points'] + points_to_add
        new_sessions = user_stats['focus_sessions'] + sessions_to_add
        
        # Leveling logic: a new level every 500 points
        current_level = user_stats['level']
        new_level = (new_points // 500) + 1
        
        gamification_table.update({
            'points': new_points,
            'focus_sessions': new_sessions,
            'level': new_level
        }, Stats.user_id == user_id)
        
        if new_level > current_level:
            return f"Leveled Up! You are now Level {new_level}!"
    return None