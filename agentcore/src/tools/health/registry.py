"""
Health tools registry for backend_bedrock.

This module provides the registry for health tracking tools including
calorie tracking and goal management functionality.
"""

from .calorie_tracking import (
    log_daily_calories, get_calorie_history, calculate_calorie_deficit,
    get_day_plan, set_daily_calorie_target
)
from .goal_management import (
    set_health_goals, track_goal_progress, update_goal_status,
    get_goal_recommendations, get_user_goals
)

# Export callable tools for Strands Agent
HEALTH_TOOL_FUNCTIONS = [
    # Calorie Tracking Tools
    log_daily_calories,
    get_calorie_history,
    calculate_calorie_deficit,
    set_daily_calorie_target,
    get_day_plan,
    
    # Goal Management Tools
    set_health_goals,
    track_goal_progress,
    update_goal_status,
    get_goal_recommendations,
    get_user_goals
]