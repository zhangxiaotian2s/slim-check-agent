from typing import Literal
from langgraph.graph import StateGraph, END
from src.graph.state import CalorieState, ContentType
from src.agents.base_agent import BaseAgent
from src.agents.image_analyst_agent import ImageAnalystAgent
from src.agents.diet_analyst_agent import DietAnalystAgent
from src.agents.exercise_analyst_agent import ExerciseAnalystAgent
from src.agents.health_manager_agent import HealthManagerAgent
from src.storage import get_user_storage
from src.models import AnalysisResult
from src.utils.logger import logger
from datetime import datetime

def create_calorie_graph():
    """Create the LangGraph for calorie analysis."""
    graph = StateGraph(CalorieState)

    # Initialize agents
    image_analyst = ImageAnalystAgent()
    diet_analyst = DietAnalystAgent()
    exercise_analyst = ExerciseAnalystAgent()
    health_manager = HealthManagerAgent()

    # Add nodes
    graph.add_node("route_input", route_input)
    graph.add_node("classify_text", classify_text)
    graph.add_node("analyze_image", image_analyst.run)
    graph.add_node("load_user_profile", load_user_profile)
    graph.add_node("analyze_diet", diet_analyst.run)
    graph.add_node("analyze_exercise", exercise_analyst.run)
    graph.add_node("check_user_info", health_manager.check_info)
    graph.add_node("request_missing_info", request_missing_info)
    graph.add_node("save_user_profile", health_manager.save_profile)
    graph.add_node("generate_result", generate_result)

    # Entry point
    graph.set_entry_point("route_input")

    # Conditional routing based on input type
    graph.add_conditional_edges(
        "route_input",
        decide_image_or_text,
        {
            "analyze_image": "analyze_image",
            "classify_text": "classify_text",
        },
    )

    # After image analysis, load user profile if available
    graph.add_edge("analyze_image", "load_user_profile")

    # After loading user profile, go to diet analysis (images are always diet)
    graph.add_edge("load_user_profile", "analyze_diet")

    # After text classification, route to appropriate handler
    graph.add_conditional_edges(
        "classify_text",
        route_by_content_type,
        {
            "diet": "load_user_profile",
            "exercise": "load_user_profile",
            "user_registration": "check_user_info",
        },
    )

    # After loading user profile for text diet, go to diet analysis
    graph.add_conditional_edges(
        "load_user_profile",
        continue_after_load_user,
        {
            "analyze_diet": "analyze_diet",
            "analyze_exercise": "analyze_exercise",
        },
    )

    # After diet analysis, check if we also need to analyze exercise
    graph.add_conditional_edges(
        "analyze_diet",
        needs_also_exercise,
        {
            "needs_exercise": "analyze_exercise",
            "no_exercise": "generate_result",
        },
    )

    # After exercise analysis, always go directly to generate result
    # If there was both diet and exercise, we already did diet first
    graph.add_edge("analyze_exercise", "generate_result")

    # Check if user info is complete
    graph.add_conditional_edges(
        "check_user_info",
        is_user_info_complete,
        {
            "complete": "save_user_profile",
            "incomplete": "request_missing_info",
        },
    )

    # If incomplete, end and request user input
    graph.add_edge("request_missing_info", END)

    # After saving user profile, generate result
    graph.add_edge("save_user_profile", "generate_result")

    # End after result generation
    graph.add_edge("generate_result", END)

    return graph.compile()

# Router functions
def route_input(state: CalorieState) -> dict:
    """Initial routing based on input type."""
    logger.info(f"Routing input: type={state['input_type']}")
    # For image inputs, it's always diet analysis
    if state["input_type"] in ["image", "image_with_text"]:
        return {"content_type": "diet"}
    return {}

def decide_image_or_text(state: CalorieState) -> Literal["analyze_image", "classify_text"]:
    """Decide whether to go to image analysis or text classification."""
    if state["input_type"] in ["image", "image_with_text"]:
        return "analyze_image"
    else:
        return "classify_text"

def classify_text(state: CalorieState) -> dict:
    """Classify pure text input into diet/exercise/registration."""
    from src.utils.llm_client import get_llm_client
    from src.prompts import ROUTER_SYSTEM_PROMPT, ROUTER_CLASSIFY_PROMPT

    llm = get_llm_client()
    prompt = ROUTER_CLASSIFY_PROMPT.format(text=state["text_input"])

    messages = [
        {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    response = llm.chat(messages, temperature=0.1)

    # Parse JSON response
    import json
    try:
        # Clean response - sometimes LLM adds markdown code blocks
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        result = json.loads(cleaned)

        has_diet = bool(result.get("has_diet", False))
        has_exercise = bool(result.get("has_exercise", False))
        is_user_registration = bool(result.get("is_user_registration", False))

        # Determine content_type for backward compatibility in routing
        # If it's user registration, that's the only one
        if is_user_registration:
            content_type = "user_registration"
        elif has_diet and not has_exercise:
            content_type = "diet"
        elif has_exercise and not has_diet:
            content_type = "exercise"
        elif has_diet and has_exercise:
            content_type = "diet"  # Will handle both sequentially

        logger.info(f"Text classified: has_diet={has_diet}, has_exercise={has_exercise}, is_user_registration={is_user_registration}")
        return {
            "content_type": content_type,
            "_has_diet": has_diet,
            "_has_exercise": has_exercise,
            "_is_user_registration": is_user_registration,
        }
    except Exception as e:
        logger.error(f"Failed to parse classification: {e}, response={response}")
        # Default to diet
        return {
            "content_type": "diet",
            "_has_diet": True,
            "_has_exercise": False,
            "_is_user_registration": False,
        }

def route_by_content_type(state: CalorieState) -> Literal["diet", "exercise", "user_registration"]:
    """Route based on classified content type."""
    if state.get("_is_user_registration"):
        return "user_registration"
    return state["content_type"]

def load_user_profile(state: CalorieState) -> dict:
    """Load user profile if person_id is provided."""
    person_id = state.get("person_id")
    if not person_id:
        logger.info("No person_id provided, skipping user profile loading")
        return {"user_profile": None}

    storage = get_user_storage()
    profile = storage.load(person_id)
    logger.info(f"Loaded user profile: {person_id}, found={profile is not None}")
    return {"user_profile": profile}

def continue_after_load_user(state: CalorieState) -> Literal["analyze_diet", "analyze_exercise"]:
    """Continue to appropriate analysis after loading user."""
    if state["content_type"] == "diet":
        return "analyze_diet"
    else:
        return "analyze_exercise"

def needs_also_exercise(state: CalorieState) -> Literal["needs_exercise", "no_exercise"]:
    """Check if we also need to analyze exercise after diet analysis."""
    has_exercise = state.get("_has_exercise", False)
    logger.info(f"needs_also_exercise: has_exercise={has_exercise}")
    if has_exercise:
        return "needs_exercise"
    return "no_exercise"

def needs_also_diet(state: CalorieState) -> Literal["needs_diet", "no_diet"]:
    """Check if we also need to analyze diet after exercise analysis."""
    has_diet = state.get("_has_diet", False)
    logger.info(f"needs_also_diet: has_diet={has_diet}")
    if has_diet:
        return "needs_diet"
    return "no_diet"

def is_user_info_complete(state: CalorieState) -> Literal["complete", "incomplete"]:
    """Check if user registration info is complete."""
    if state.get("requires_user_input"):
        return "incomplete"
    return "complete"

def request_missing_info(state: CalorieState) -> dict:
    """Request user to provide missing information."""
    missing = state.get("missing_fields", [])
    logger.info(f"Requesting missing user info: {missing}")
    return {
        "requires_user_input": True,
        "error_message": f"需要你提供以下信息：{', '.join(missing)}",
    }

def generate_result(state: CalorieState) -> dict:
    """Generate the final analysis result."""
    from src.models import AnalysisResult

    # Determine request type - if both diet and exercise are present, we use diet_analysis
    # but include both results
    has_diet = state.get("analyzed_foods") is not None and len(state.get("analyzed_foods", [])) > 0
    has_exercise = state.get("analyzed_exercise") is not None and len(state.get("analyzed_exercise", [])) > 0

    if has_diet and has_exercise:
        request_type = "diet_analysis"  # Will contain both
    else:
        request_type_map = {
            "diet": "diet_analysis",
            "exercise": "exercise_analysis",
            "user_registration": "user_registration",
        }
        content_type = state.get("content_type", "diet") if state["input_type"] == "text_only" else "diet"
        request_type = request_type_map.get(content_type, "diet_analysis")

    # Build result
    result = AnalysisResult(
        request_type=request_type,
        timestamp=datetime.now(),
        person_id=state.get("person_id"),
        user_profile=state.get("user_profile"),
        recommendations=[],
    )

    # Add diet info if we have it
    if has_diet and state.get("analyzed_foods"):
        total_calories = sum(f.calories for f in state["analyzed_foods"])
        total_protein = sum(f.protein_g for f in state["analyzed_foods"])
        total_carbs = sum(f.carbs_g for f in state["analyzed_foods"])
        total_fat = sum(f.fat_g for f in state["analyzed_foods"])

        result.total_calories_intake = round(total_calories, 1)
        result.total_protein = round(total_protein, 1)
        result.total_carbs = round(total_carbs, 1)
        result.total_fat = round(total_fat, 1)
        result.food_items = state["analyzed_foods"]

    # Add exercise info if we have it
    if has_exercise and state.get("analyzed_exercise"):
        total_burned = sum(e.calories_burned for e in state["analyzed_exercise"])
        result.total_calories_burned = round(total_burned, 1)
        result.exercise_items = state["analyzed_exercise"]

    # Generate summary
    summary_parts = []
    if result.total_calories_intake is not None:
        if state.get("user_profile"):
            daily_need = state["user_profile"].daily_calorie_needs
            percentage = (result.total_calories_intake / daily_need * 100) if daily_need > 0 else 0
            summary_parts.append(
                f"总共摄入 {result.total_calories_intake:.0f} 大卡，"
                f"占每日推荐摄入量 ({daily_need:.0f} 大卡) 的 {percentage:.0f}%。"
            )
        else:
            summary_parts.append(f"总共摄入 {result.total_calories_intake:.0f} 大卡。")

    if result.total_calories_burned is not None:
        summary_parts.append(f"运动总共消耗 {result.total_calories_burned:.0f} 大卡。")

    result.summary = " ".join(summary_parts)

    if request_type == "user_registration" and state.get("user_profile"):
        profile = state["user_profile"]
        result.summary = (
            f"用户信息已保存，人物ID: {profile.person_id}。"
            f"你的BMI为 {profile.bmi:.1f}，每日推荐摄入 {profile.daily_calorie_needs:.0f} 大卡。"
            f"{profile.health_assessment}。"
        )

    logger.info(f"Result generated: request_type={request_type}")
    return {"analysis_result": result}
