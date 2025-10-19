// TypeScript interfaces matching the backend Pydantic models

export interface HealthSummary {
  date: string;
  total_calories: number;
  target_calories: number;
  remaining_calories: number;
  protein: number;
  carbs: number;
  fat: number;
  meals: string[];
  recommendations: string[];
  health_score: number; // 1-10
}

export interface CartItem {
  name: string;
  quantity: number;
  price: number;
  total_price: number;
  availability: string;
}

export interface GrocerySummary {
  cart_items: CartItem[];
  total_cost: number;
  item_count: number;
  budget_set: number | null;
  budget_remaining: number | null;
  budget_status: string;
  savings_opportunities: string[];
  recommendations: string[];
  substitutions: string[];
  availability_summary: string;
}

export interface Recipe {
  name: string;
  prep_time: number;
  cook_time: number;
  servings: number;
  ingredients: string[];
  instructions: string[];
  calories_per_serving: number;
  dietary_tags: string[];
  difficulty_level: string;
  meal_type: string;
}

export interface MealPlan {
  date: string;
  recipes: Recipe[];
  total_calories: number;
  total_prep_time: number;
  total_cook_time: number;
  shopping_list: string[];
  ingredient_substitutions: string[];
  dietary_notes: string[];
  nutritional_summary: Record<string, number>;
  meal_balance_score: number; // 1-10
  estimated_cost: number | null;
}

export type StructuredResponse = HealthSummary | GrocerySummary | MealPlan;

// Utility function to detect if a string is JSON
export const isJsonResponse = (response: string): boolean => {
  try {
    JSON.parse(response);
    return true;
  } catch {
    return false;
  }
};

// Utility function to determine the type of structured response
export const getResponseType = (data: any): 'health' | 'grocery' | 'meal' | 'unknown' => {
  if (data.health_score !== undefined && data.total_calories !== undefined) {
    return 'health';
  }
  if (data.cart_items !== undefined && data.total_cost !== undefined) {
    return 'grocery';
  }
  if (data.recipes !== undefined && data.meal_balance_score !== undefined) {
    return 'meal';
  }
  return 'unknown';
};