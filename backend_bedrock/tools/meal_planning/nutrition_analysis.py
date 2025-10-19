"""
Nutrition analysis tools for backend_bedrock meal planning.

This module provides nutritional analysis, dietary filtering, and meal
nutrition calculation functionality for meal planning agents.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from strands import tool

# Add parent directory to path for imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import dependencies with flexible import system
try:
    from backend_bedrock.tools.shared.calculations import calculate_nutrition, calculate_calories
    from backend_bedrock.tools.shared.user_profile import get_user_preferences
    from backend_bedrock.tools.shared.product_catalog import find_products_by_names
except ImportError:
    try:
        from tools.shared.calculations import calculate_nutrition, calculate_calories
        from tools.shared.user_profile import get_user_preferences
        from tools.shared.product_catalog import find_products_by_names
    except ImportError:
        # Fallback for testing
        def calculate_nutrition(items):
            return {"success": True, "data": {"totals": {"calories": 400, "protein": 25, "carbs": 45, "fat": 12}}}
        def calculate_calories(items):
            return {"success": True, "data": {"total_calories": 400}}
        def get_user_preferences(user_id):
            return {"success": True, "data": {"allergies": [], "restrictions": []}}
        def find_products_by_names(names):
            return {"success": True, "data": []}


@tool
def analyze_meal_nutrition(meal_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze nutritional content of a meal.
    
    Args:
        meal_items (List[Dict[str, Any]]): List of meal items with names and quantities
        
    Returns:
        Dict[str, Any]: Standardized response with nutritional analysis
    """
    try:
        # Calculate comprehensive nutrition
        nutrition_result = calculate_nutrition(meal_items)
        
        if not nutrition_result['success']:
            return nutrition_result
        
        nutrition_data = nutrition_result['data']
        totals = nutrition_data['totals']
        
        # Analyze nutritional balance
        total_calories = totals.get('calories', 0)
        protein_cals = totals.get('protein', 0) * 4  # 4 calories per gram
        carb_cals = totals.get('carbs', 0) * 4      # 4 calories per gram
        fat_cals = totals.get('fat', 0) * 9         # 9 calories per gram
        
        # Calculate macronutrient percentages
        if total_calories > 0:
            protein_percent = (protein_cals / total_calories) * 100
            carb_percent = (carb_cals / total_calories) * 100
            fat_percent = (fat_cals / total_calories) * 100
        else:
            protein_percent = carb_percent = fat_percent = 0
        
        # Nutritional analysis
        analysis = {
            'totals': totals,
            'macronutrient_breakdown': {
                'protein_percent': round(protein_percent, 1),
                'carbs_percent': round(carb_percent, 1),
                'fat_percent': round(fat_percent, 1)
            },
            'nutritional_quality': {
                'balanced': 15 <= protein_percent <= 35 and 45 <= carb_percent <= 65 and 20 <= fat_percent <= 35,
                'high_protein': protein_percent > 25,
                'low_carb': carb_percent < 30,
                'low_fat': fat_percent < 20
            },
            'meal_items_analyzed': len(meal_items),
            'items_with_nutrition_data': nutrition_data.get('items_found', 0)
        }
        
        # Add recommendations
        recommendations = []
        if protein_percent < 15:
            recommendations.append("Consider adding more protein sources")
        if carb_percent > 65:
            recommendations.append("Consider reducing carbohydrate content")
        if fat_percent > 35:
            recommendations.append("Consider reducing fat content")
        if total_calories < 300:
            recommendations.append("This meal may be too low in calories")
        elif total_calories > 800:
            recommendations.append("This meal is quite high in calories")
        
        analysis['recommendations'] = recommendations
        
        return {
            'success': True,
            'data': analysis,
            'message': f'Analyzed nutrition for {len(meal_items)} meal items ({total_calories} calories)'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error analyzing meal nutrition: {str(e)}'
        }


@tool
def apply_dietary_filters(items: List[Dict[str, Any]], restrictions: List[str]) -> Dict[str, Any]:
    """
    Filter items based on dietary restrictions.
    
    Args:
        items (List[Dict[str, Any]]): List of food items
        restrictions (List[str]): List of dietary restrictions
        
    Returns:
        Dict[str, Any]: Standardized response with filtered items
    """
    try:
        if not restrictions:
            return {
                'success': True,
                'data': {
                    'filtered_items': items,
                    'removed_items': [],
                    'restrictions_applied': []
                },
                'message': 'No dietary restrictions applied'
            }
        
        filtered_items = []
        removed_items = []
        
        for item in items:
            item_name = item.get('name', '').lower() if isinstance(item, dict) else str(item).lower()
            item_tags = item.get('tags', []) if isinstance(item, dict) else []
            item_description = item.get('description', '').lower() if isinstance(item, dict) else ''
            
            # Check against restrictions
            is_allowed = True
            violated_restrictions = []
            
            for restriction in restrictions:
                restriction_lower = restriction.lower()
                
                # Common dietary restriction checks
                if restriction_lower in ['vegetarian', 'vegan']:
                    meat_keywords = ['chicken', 'beef', 'pork', 'fish', 'meat', 'turkey', 'lamb']
                    if any(keyword in item_name for keyword in meat_keywords):
                        is_allowed = False
                        violated_restrictions.append(restriction)
                
                elif restriction_lower == 'vegan':
                    dairy_keywords = ['milk', 'cheese', 'butter', 'cream', 'yogurt', 'egg']
                    if any(keyword in item_name for keyword in dairy_keywords):
                        is_allowed = False
                        violated_restrictions.append(restriction)
                
                elif restriction_lower in ['gluten-free', 'gluten free']:
                    gluten_keywords = ['wheat', 'bread', 'pasta', 'flour', 'barley', 'rye']
                    if any(keyword in item_name for keyword in gluten_keywords):
                        is_allowed = False
                        violated_restrictions.append(restriction)
                
                elif restriction_lower in ['dairy-free', 'dairy free', 'lactose-free']:
                    dairy_keywords = ['milk', 'cheese', 'butter', 'cream', 'yogurt']
                    if any(keyword in item_name for keyword in dairy_keywords):
                        is_allowed = False
                        violated_restrictions.append(restriction)
                
                elif restriction_lower in ['nut-free', 'nut free']:
                    nut_keywords = ['almond', 'peanut', 'walnut', 'cashew', 'pecan', 'hazelnut']
                    if any(keyword in item_name for keyword in nut_keywords):
                        is_allowed = False
                        violated_restrictions.append(restriction)
                
                # Generic restriction check
                elif restriction_lower in item_name or restriction_lower in item_description:
                    is_allowed = False
                    violated_restrictions.append(restriction)
                
                # Check tags if available
                if isinstance(item, dict) and item_tags:
                    if any(restriction_lower in str(tag).lower() for tag in item_tags):
                        is_allowed = False
                        violated_restrictions.append(restriction)
            
            if is_allowed:
                filtered_items.append(item)
            else:
                removed_item = item.copy() if isinstance(item, dict) else {'name': item}
                removed_item['violated_restrictions'] = violated_restrictions
                removed_items.append(removed_item)
        
        filter_summary = {
            'filtered_items': filtered_items,
            'removed_items': removed_items,
            'restrictions_applied': restrictions,
            'original_count': len(items),
            'filtered_count': len(filtered_items),
            'removed_count': len(removed_items)
        }
        
        return {
            'success': True,
            'data': filter_summary,
            'message': f'Applied {len(restrictions)} dietary restrictions. {len(filtered_items)} items remain from {len(items)} original items.'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error applying dietary filters: {str(e)}'
        }

@tool
def calculate_daily_nutrition(meals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate daily nutritional totals from multiple meals.
    
    Args:
        meals (List[Dict[str, Any]]): List of meals with their items
        
    Returns:
        Dict[str, Any]: Standardized response with daily nutrition totals
    """
    try:
        daily_totals = {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0,
            'fiber': 0
        }
        
        meal_analyses = []
        
        # Analyze each meal
        for i, meal in enumerate(meals):
            meal_name = meal.get('name', f'Meal {i+1}')
            meal_items = meal.get('items', [])
            
            if not meal_items:
                continue
            
            # Analyze this meal's nutrition
            meal_analysis_result = analyze_meal_nutrition(meal_items)
            
            if meal_analysis_result['success']:
                meal_nutrition = meal_analysis_result['data']['totals']
                
                # Add to daily totals
                for nutrient in daily_totals:
                    daily_totals[nutrient] += meal_nutrition.get(nutrient, 0)
                
                meal_analyses.append({
                    'meal_name': meal_name,
                    'nutrition': meal_nutrition,
                    'items_count': len(meal_items)
                })
        
        # Calculate daily percentages and analysis
        total_calories = daily_totals['calories']
        
        if total_calories > 0:
            protein_percent = (daily_totals['protein'] * 4 / total_calories) * 100
            carb_percent = (daily_totals['carbs'] * 4 / total_calories) * 100
            fat_percent = (daily_totals['fat'] * 9 / total_calories) * 100
        else:
            protein_percent = carb_percent = fat_percent = 0
        
        # Daily nutrition analysis
        daily_analysis = {
            'daily_totals': daily_totals,
            'macronutrient_percentages': {
                'protein': round(protein_percent, 1),
                'carbs': round(carb_percent, 1),
                'fat': round(fat_percent, 1)
            },
            'meal_breakdown': meal_analyses,
            'meals_analyzed': len(meal_analyses),
            'nutritional_goals': {
                'meets_calorie_range': 1500 <= total_calories <= 2500,
                'balanced_macros': 15 <= protein_percent <= 35 and 45 <= carb_percent <= 65 and 20 <= fat_percent <= 35,
                'adequate_protein': daily_totals['protein'] >= 50,
                'adequate_fiber': daily_totals.get('fiber', 0) >= 25
            }
        }
        
        # Add daily recommendations
        recommendations = []
        if total_calories < 1200:
            recommendations.append("Daily calorie intake may be too low")
        elif total_calories > 3000:
            recommendations.append("Daily calorie intake is quite high")
        
        if protein_percent < 15:
            recommendations.append("Consider increasing protein intake throughout the day")
        if daily_totals.get('fiber', 0) < 25:
            recommendations.append("Consider adding more fiber-rich foods")
        
        daily_analysis['daily_recommendations'] = recommendations
        
        return {
            'success': True,
            'data': daily_analysis,
            'message': f'Calculated daily nutrition from {len(meals)} meals ({total_calories} total calories)'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error calculating daily nutrition: {str(e)}'
        }

@tool
def get_nutrition_recommendations(user_id: str, current_nutrition: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get personalized nutrition recommendations based on user profile and current intake.
    
    Args:
        user_id (str): User identifier
        current_nutrition (Dict[str, Any]): Current nutritional intake
        
    Returns:
        Dict[str, Any]: Standardized response with nutrition recommendations
    """
    try:
        # Get user preferences
        preferences_result = get_user_preferences(user_id)
        user_preferences = preferences_result['data'] if preferences_result['success'] else {}
        
        # Extract current nutrition values
        current_calories = current_nutrition.get('calories', 0)
        current_protein = current_nutrition.get('protein', 0)
        current_carbs = current_nutrition.get('carbs', 0)
        current_fat = current_nutrition.get('fat', 0)
        
        # Basic nutritional targets (would be personalized based on user profile)
        targets = {
            'calories': 2000,  # Would be calculated based on age, gender, activity level
            'protein': 150,    # grams
            'carbs': 250,      # grams
            'fat': 67          # grams
        }
        
        recommendations = []
        nutrient_status = {}
        
        # Analyze each nutrient
        for nutrient, target in targets.items():
            current_value = current_nutrition.get(nutrient, 0)
            percentage_of_target = (current_value / target) * 100 if target > 0 else 0
            
            nutrient_status[nutrient] = {
                'current': current_value,
                'target': target,
                'percentage_of_target': round(percentage_of_target, 1),
                'deficit': max(0, target - current_value),
                'excess': max(0, current_value - target)
            }
            
            # Generate recommendations
            if percentage_of_target < 80:
                recommendations.append(f"Increase {nutrient} intake - currently at {percentage_of_target:.1f}% of target")
            elif percentage_of_target > 120:
                recommendations.append(f"Consider reducing {nutrient} intake - currently at {percentage_of_target:.1f}% of target")
        
        # Add dietary restriction considerations
        restrictions = user_preferences.get('restrictions', [])
        if restrictions:
            recommendations.append(f"Ensure food choices align with dietary restrictions: {', '.join(restrictions)}")
        
        # Add allergy considerations
        allergies = user_preferences.get('allergies', [])
        if allergies:
            recommendations.append(f"Avoid allergens: {', '.join(allergies)}")
        
        recommendation_data = {
            'nutrient_status': nutrient_status,
            'recommendations': recommendations,
            'user_restrictions': restrictions,
            'user_allergies': allergies,
            'overall_status': 'on_track' if all(80 <= status['percentage_of_target'] <= 120 for status in nutrient_status.values()) else 'needs_adjustment'
        }
        
        return {
            'success': True,
            'data': recommendation_data,
            'message': f'Generated {len(recommendations)} nutrition recommendations'
        }
        
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'message': f'Error getting nutrition recommendations: {str(e)}'
        }


# Legacy compatibility functions
@tool
def analyze_meal_nutrition_legacy(meal_items: List[str]) -> str:
    """Legacy function returning JSON string for backward compatibility."""
    # Convert string list to dict format
    items_dict = [{'name': item} for item in meal_items]
    result = analyze_meal_nutrition(items_dict)
    return json.dumps(result['data'] if result['success'] else {"error": result['message']})

@tool
def apply_dietary_filters_legacy(items: List[str], restrictions: List[str]) -> str:
    """Legacy function returning JSON string for backward compatibility."""
    # Convert string list to dict format
    items_dict = [{'name': item} for item in items]
    result = apply_dietary_filters(items_dict, restrictions)
    return json.dumps(result['data'] if result['success'] else {"error": result['message']})