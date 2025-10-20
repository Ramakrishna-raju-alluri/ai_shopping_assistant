"""
Goal management tools for backend_bedrock health management.

This module provides health goal setting, tracking, and progress monitoring
functionality for health and wellness management.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from strands import tool

# Add parent directory to path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import dependencies with flexible import system
try:
    from backend_bedrock.dynamo.client import dynamodb
    from backend_bedrock.tools.health.calorie_tracking import get_calorie_history
except ImportError:
    try:
        from dynamo.client import dynamodb
        from tools.health.calorie_tracking import get_calorie_history
    except ImportError:
        # Fallback for testing
        import boto3
        try:
            dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        except:
            dynamodb = None
        def get_calorie_history(user_id, date_range):
            return {"success": True, "data": {"average_daily_calories": 2000}}

# Health goals table
HEALTH_GOALS_TABLE = "health_goals"


def _goals_table():
    """Get the health goals table."""
    return dynamodb.Table(HEALTH_GOALS_TABLE)


@tool
def set_health_goals(user_id: str, goals: Dict[str, Any]) -> Dict[str, Any]:
    """
    Set user health goals.
    
    Args:
        user_id (str): User identifier
        goals (Dict[str, Any]): Health goals to set
        
    Returns:
        Dict[str, Any]: Standardized response with goal setting result
    """
    try:
        # Prepare goals data
        goals_data = {
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'goals': {}
        }
        
        # Process different types of goals
        supported_goals = {
            'daily_calories': {'type': 'numeric', 'unit': 'calories'},
            'weekly_exercise': {'type': 'numeric', 'unit': 'sessions'},
            'weight_target': {'type': 'numeric', 'unit': 'lbs'},
            'water_intake': {'type': 'numeric', 'unit': 'glasses'},
            'sleep_hours': {'type': 'numeric', 'unit': 'hours'},
            'steps_daily': {'type': 'numeric', 'unit': 'steps'}
        }
        
        for goal_name, goal_value in goals.items():
            if goal_name in supported_goals:
                goal_info = supported_goals[goal_name]
                goals_data['goals'][goal_name] = {
                    'target': goal_value,
                    'type': goal_info['type'],
                    'unit': goal_info['unit'],
                    'status': 'active',
                    'progress': 0,
                    'set_date': datetime.utcnow().isoformat()
                }
        
        # Save to database (mock implementation)
        # In real implementation, would save to DynamoDB
        goals_data['goal_id'] = f"goals_{user_id}_{datetime.now().strftime('%Y%m%d')}"
        
        return {
            'success': True,
            'data': goals_data,
            'message': f'Set {len(goals_data["goals"])} health goals for user'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error setting health goals: {str(e)}'
        }


@tool
def track_goal_progress(user_id: str, goal_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Track progress toward health goals.
    
    Args:
        user_id (str): User identifier
        goal_type (Optional[str]): Specific goal type to track (optional)
        
    Returns:
        Dict[str, Any]: Standardized response with progress tracking
    """
    try:
        # Mock goal retrieval (in real implementation, would query database)
        user_goals = {
            'daily_calories': {'target': 2000, 'type': 'numeric', 'unit': 'calories'},
            'weekly_exercise': {'target': 5, 'type': 'numeric', 'unit': 'sessions'},
            'weight_target': {'target': 150, 'type': 'numeric', 'unit': 'lbs'},
            'water_intake': {'target': 8, 'type': 'numeric', 'unit': 'glasses'},
            'sleep_hours': {'target': 8, 'type': 'numeric', 'unit': 'hours'}
        }
        
        progress_data = {}
        
        # Track specific goal or all goals
        goals_to_track = {goal_type: user_goals[goal_type]} if goal_type and goal_type in user_goals else user_goals
        
        for goal_name, goal_info in goals_to_track.items():
            target = goal_info['target']
            
            # Calculate current progress based on goal type
            if goal_name == 'daily_calories':
                # Get recent calorie history
                history_result = get_calorie_history(user_id, 7)
                if history_result['success']:
                    current_value = history_result['data']['average_daily_calories']
                else:
                    current_value = 0
            else:
                # Mock current values for other goals
                current_value = target * 0.7  # 70% progress
            
            # Calculate progress percentage
            progress_percentage = (current_value / target) * 100 if target > 0 else 0
            
            # Determine status
            if progress_percentage >= 100:
                status = 'achieved'
            elif progress_percentage >= 80:
                status = 'on_track'
            elif progress_percentage >= 50:
                status = 'behind'
            else:
                status = 'needs_attention'
            
            progress_data[goal_name] = {
                'target': target,
                'current': round(current_value, 1),
                'progress_percentage': round(progress_percentage, 1),
                'status': status,
                'unit': goal_info['unit'],
                'remaining': max(0, target - current_value)
            }
        
        # Calculate overall progress
        if progress_data:
            avg_progress = sum(goal['progress_percentage'] for goal in progress_data.values()) / len(progress_data)
            overall_status = 'excellent' if avg_progress >= 90 else 'good' if avg_progress >= 70 else 'needs_improvement'
        else:
            avg_progress = 0
            overall_status = 'no_goals'
        
        tracking_summary = {
            'goal_progress': progress_data,
            'overall_progress_percentage': round(avg_progress, 1),
            'overall_status': overall_status,
            'goals_tracked': len(progress_data),
            'goals_achieved': len([g for g in progress_data.values() if g['status'] == 'achieved']),
            'tracking_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        return {
            'success': True,
            'data': tracking_summary,
            'message': f'Tracked progress for {len(progress_data)} health goals'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error tracking goal progress: {str(e)}'
        }

@tool
def update_goal_status(user_id: str, goal_id: str, status: str, notes: Optional[str] = None) -> Dict[str, Any]:
    """
    Update goal status and add notes.
    
    Args:
        user_id (str): User identifier
        goal_id (str): Goal identifier
        status (str): New status (active, paused, completed, cancelled)
        notes (Optional[str]): Optional notes about the status change
        
    Returns:
        Dict[str, Any]: Standardized response with status update result
    """
    try:
        valid_statuses = ['active', 'paused', 'completed', 'cancelled']
        
        if status not in valid_statuses:
            return {
                'success': False,
                'data': None,
                'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }
        
        # Mock goal update (in real implementation, would update database)
        update_data = {
            'user_id': user_id,
            'goal_id': goal_id,
            'old_status': 'active',  # Would retrieve from database
            'new_status': status,
            'updated_at': datetime.utcnow().isoformat(),
            'notes': notes or '',
            'updated_by': user_id
        }
        
        return {
            'success': True,
            'data': update_data,
            'message': f'Updated goal {goal_id} status to {status}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error updating goal status: {str(e)}'
        }

@tool
def get_goal_recommendations(user_id: str) -> Dict[str, Any]:
    """
    Get personalized goal recommendations based on user progress.
    
    Args:
        user_id (str): User identifier
        
    Returns:
        Dict[str, Any]: Standardized response with goal recommendations
    """
    try:
        # Get current progress
        progress_result = track_goal_progress(user_id)
        
        if not progress_result['success']:
            return progress_result
        
        progress_data = progress_result['data']
        goal_progress = progress_data['goal_progress']
        
        recommendations = []
        
        # Analyze each goal and provide recommendations
        for goal_name, goal_data in goal_progress.items():
            status = goal_data['status']
            progress_pct = goal_data['progress_percentage']
            
            if status == 'needs_attention':
                recommendations.append({
                    'goal': goal_name,
                    'priority': 'high',
                    'recommendation': f'Focus on {goal_name} - currently at {progress_pct:.1f}% of target',
                    'suggested_actions': [
                        f'Set smaller daily targets for {goal_name}',
                        'Track progress more frequently',
                        'Consider adjusting target if too ambitious'
                    ]
                })
            elif status == 'behind':
                recommendations.append({
                    'goal': goal_name,
                    'priority': 'medium',
                    'recommendation': f'Increase effort on {goal_name} to get back on track',
                    'suggested_actions': [
                        f'Review what\'s preventing progress on {goal_name}',
                        'Consider breaking goal into smaller steps'
                    ]
                })
            elif status == 'achieved':
                recommendations.append({
                    'goal': goal_name,
                    'priority': 'low',
                    'recommendation': f'Great job achieving {goal_name}! Consider setting a new challenge',
                    'suggested_actions': [
                        f'Maintain current {goal_name} level',
                        'Set a more ambitious target',
                        'Help others with similar goals'
                    ]
                })
        
        # Add general recommendations
        overall_status = progress_data['overall_status']
        if overall_status == 'needs_improvement':
            recommendations.append({
                'goal': 'overall',
                'priority': 'high',
                'recommendation': 'Consider focusing on 1-2 goals at a time for better success',
                'suggested_actions': [
                    'Prioritize your most important health goals',
                    'Set up daily reminders',
                    'Track progress weekly'
                ]
            })
        
        recommendation_data = {
            'recommendations': recommendations,
            'total_recommendations': len(recommendations),
            'high_priority_count': len([r for r in recommendations if r['priority'] == 'high']),
            'overall_health_score': progress_data['overall_progress_percentage'],
            'generated_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        return {
            'success': True,
            'data': recommendation_data,
            'message': f'Generated {len(recommendations)} goal recommendations'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error getting goal recommendations: {str(e)}'
        }

@tool
def get_user_goals(user_id: str) -> Dict[str, Any]:
    """
    Get all health goals for a user.
    
    Args:
        user_id (str): User identifier
        
    Returns:
        Dict[str, Any]: Standardized response with user goals
    """
    try:
        # Mock goal retrieval (in real implementation, would query database)
        user_goals = {
            'user_id': user_id,
            'goals': {
                'daily_calories': {
                    'target': 2000,
                    'type': 'numeric',
                    'unit': 'calories',
                    'status': 'active',
                    'set_date': '2024-01-01'
                },
                'weekly_exercise': {
                    'target': 5,
                    'type': 'numeric',
                    'unit': 'sessions',
                    'status': 'active',
                    'set_date': '2024-01-01'
                },
                'weight_target': {
                    'target': 150,
                    'type': 'numeric',
                    'unit': 'lbs',
                    'status': 'active',
                    'set_date': '2024-01-01'
                }
            },
            'total_goals': 3,
            'active_goals': 3,
            'last_updated': datetime.now().strftime('%Y-%m-%d')
        }
        
        return {
            'success': True,
            'data': user_goals,
            'message': f'Retrieved {user_goals["total_goals"]} health goals'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error getting user goals: {str(e)}'
        }