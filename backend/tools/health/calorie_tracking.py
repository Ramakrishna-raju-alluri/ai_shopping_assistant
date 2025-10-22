"""
Calorie tracking tools for backend_bedrock health management.

This module provides calorie logging, tracking, and analysis functionality
for health and nutrition monitoring.
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
    from backend_bedrock.dynamo.client import dynamodb, NUTRITION_TABLE
    from backend_bedrock.tools.shared.calculations import calculate_calories
except ImportError:
    try:
        from dynamo.client import dynamodb, NUTRITION_TABLE
        from tools.shared.calculations import calculate_calories
    except ImportError:
        print("⚠️ Error importing database modules in calorie tracking.py")
        #sys.exit(1)
        # Fallback for testing
        # import boto3
        # try:
        #     dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        # except:
        #     dynamodb = None
        # NUTRITION_TABLE = "nutrition_calendar"
        # def calculate_calories(items):
        #     return {"success": True, "data": {"total_calories": 400}}


def _table():
    """Get the nutrition table."""
    return dynamodb.Table(NUTRITION_TABLE)


@tool
def log_daily_calories(user_id: str, calories: int, date: str, meal_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Log daily calorie intake.
    
    Args:
        user_id (str): User identifier
        calories (int): Calories to log
        date (str): Date in YYYY-MM-DD format
        meal_type (Optional[str]): Type of meal (breakfast, lunch, dinner, snack)
        
    Returns:
        Dict[str, Any]: Standardized response with logging result
    """
    try:
        # Get existing day plan
        existing_plan = get_day_plan(user_id, date)
        
        if not existing_plan['success']:
            # Create new day plan
            day_plan = {
                "user_id": user_id,
                "date": date,
                "target": 0,
                "consumed": calories,
                "meals": []
            }
        else:
            day_plan = existing_plan['data']
            day_plan['consumed'] = day_plan.get('consumed', 0) + calories
        
        # Add meal entry if meal_type provided
        if meal_type:
            meal_entry = {
                "meal_type": meal_type,
                "calories": calories,
                "logged_at": datetime.utcnow().isoformat()
            }
            day_plan.setdefault('meals', []).append(meal_entry)
        
        # Save to database
        _table().put_item(Item=day_plan)
        
        return {
            'success': True,
            'data': {
                'logged_calories': calories,
                'total_consumed': day_plan['consumed'],
                'date': date,
                'meal_type': meal_type
            },
            'message': f'Logged {calories} calories for {date}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error logging calories: {str(e)}'
        }


@tool
def get_calorie_history(user_id: str, date_range: int = 7) -> Dict[str, Any]:
    """
    Get calorie tracking history for a date range.
    
    Args:
        user_id (str): User identifier
        date_range (int): Number of days to retrieve
        
    Returns:
        Dict[str, Any]: Standardized response with calorie history
    """
    try:
        history = []
        total_calories = 0
        
        # Get data for each day in range
        for i in range(date_range):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            day_result = get_day_plan(user_id, date)
            
            if day_result['success']:
                day_data = day_result['data']
                consumed = day_data.get('consumed', 0)
                target = day_data.get('target', 0)
                
                history.append({
                    'date': date,
                    'consumed': consumed,
                    'target': target,
                    'deficit_surplus': target - consumed if target > 0 else 0,
                    'meals': day_data.get('meals', [])
                })
                
                total_calories += consumed
        
        # Calculate averages
        avg_daily_calories = total_calories / date_range if date_range > 0 else 0
        
        history_data = {
            'history': sorted(history, key=lambda x: x['date']),
            'date_range_days': date_range,
            'total_calories': total_calories,
            'average_daily_calories': round(avg_daily_calories, 1),
            'days_with_data': len([h for h in history if h['consumed'] > 0])
        }
        
        return {
            'success': True,
            'data': history_data,
            'message': f'Retrieved {date_range} days of calorie history'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error getting calorie history: {str(e)}'
        }

@tool
def calculate_calorie_deficit(user_id: str, date: str, daily_target: Optional[int] = None) -> Dict[str, Any]:
    """
    Calculate calorie deficit/surplus for a specific day.
    
    Args:
        user_id (str): User identifier
        date (str): Date in YYYY-MM-DD format
        daily_target (Optional[int]): Override target; uses stored if None
        
    Returns:
        Dict[str, Any]: Standardized response with deficit calculation
    """
    try:
        # Get day plan
        day_result = get_day_plan(user_id, date)
        
        if not day_result['success']:
            return {
                'success': False,
                'data': None,
                'message': f'No calorie data found for {date}'
            }
        
        day_data = day_result['data']
        consumed = day_data.get('consumed', 0)
        target = daily_target if daily_target is not None else day_data.get('target', 0)
        
        if target == 0:
            return {
                'success': False,
                'data': None,
                'message': 'No calorie target set for this day'
            }
        
        deficit_surplus = target - consumed
        percentage_of_target = (consumed / target) * 100 if target > 0 else 0
        
        deficit_data = {
            'date': date,
            'consumed': consumed,
            'target': target,
            'deficit_surplus': deficit_surplus,
            'percentage_of_target': round(percentage_of_target, 1),
            'status': 'deficit' if deficit_surplus > 0 else 'surplus' if deficit_surplus < 0 else 'on_target'
        }
        
        if deficit_surplus > 0:
            message = f'Calorie deficit of {deficit_surplus} calories on {date}'
        elif deficit_surplus < 0:
            message = f'Calorie surplus of {abs(deficit_surplus)} calories on {date}'
        else:
            message = f'On target for calories on {date}'
        
        return {
            'success': True,
            'data': deficit_data,
            'message': message
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error calculating calorie deficit: {str(e)}'
        }

@tool
def get_day_plan(user_id: str, date: str) -> Dict[str, Any]:
    """
    Get nutrition plan for a specific day.
    
    Args:
        user_id (str): User identifier
        date (str): Date in YYYY-MM-DD format
        
    Returns:
        Dict[str, Any]: Standardized response with day plan
    """
    try:
        resp = _table().get_item(Key={"user_id": user_id, "date": date})
        
        if "Item" in resp:
            return {
                'success': True,
                'data': resp["Item"],
                'message': f'Retrieved day plan for {date}'
            }
        else:
            # Return empty day plan
            empty_plan = {
                "user_id": user_id,
                "date": date,
                "target": 0,
                "consumed": 0,
                "meals": []
            }
            return {
                'success': True,
                'data': empty_plan,
                'message': f'No existing plan for {date}, returned empty plan'
            }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error getting day plan: {str(e)}'
        }

@tool
def set_daily_calorie_target(user_id: str, date: str, target: int) -> Dict[str, Any]:
    """
    Set daily calorie target for a date.
    
    Args:
        user_id (str): User identifier
        date (str): Date in YYYY-MM-DD format
        target (int): Daily calorie goal
        
    Returns:
        Dict[str, Any]: Standardized response with updated target
    """
    try:
        # Get existing plan
        plan_result = get_day_plan(user_id, date)
        
        if plan_result['success']:
            plan = plan_result['data']
        else:
            plan = {
                "user_id": user_id,
                "date": date,
                "consumed": 0,
                "meals": []
            }
        
        plan['target'] = int(target)
        
        # Save updated plan
        _table().put_item(Item=plan)
        
        return {
            'success': True,
            'data': {
                'date': date,
                'target': target,
                'consumed': plan.get('consumed', 0),
                'remaining': target - plan.get('consumed', 0)
            },
            'message': f'Set daily calorie target to {target} for {date}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error setting calorie target: {str(e)}'
        }


# Legacy compatibility functions
@tool
def calories_remaining_legacy(user_id: str, date: str, daily_target: int = None) -> int:
    """Legacy function for backward compatibility."""
    result = calculate_calorie_deficit(user_id, date, daily_target)
    
    if result['success']:
        deficit = result['data']['deficit_surplus']
        return max(0, deficit)  # Return remaining calories (0 if over target)
    else:
        return 0