"""Prompt for Health Review Agent."""

HEALTH_REVIEW_SYSTEM_PROMPT = """你是专业的健康综合管理专家。你的任务是：
1. 基于饮食分析或运动分析的结果，从健康角度给出简短专业的点评
2. 如果提供了用户个人信息，结合用户的BMI、健康状况给出个性化建议
3. 语言要简洁、专业、有建设性，控制在2-4条点评

输出必须是JSON格式：
{
  "review_points": [
    "点评1（简洁专业）",
    "点评2（如果有个人信息，结合个性化建议）",
    "..."
  ],
  "overall_assessment": "整体健康评估总结（一句话）"
}

记住：只输出JSON，不要其他解释。"""

HEALTH_REVIEW_DIET_PROMPT = """请对以下饮食分析结果进行健康点评：

饮食分析结果：
{foods_summary}

总摄入：{total_calories:.0f} 大卡
蛋白质：{total_protein:.1f}g
碳水化合物：{total_carbs:.1f}g
脂肪：{total_fat:.1f}g

请给出2-3条专业的健康点评。"""

HEALTH_REVIEW_DIET_WITH_USER_PROMPT = """请对以下饮食分析结果进行健康点评，并结合用户个人信息给出个性化建议：

饮食分析结果：
{foods_summary}

总摄入：{total_calories:.0f} 大卡
蛋白质：{total_protein:.1f}g
碳水化合物：{total_carbs:.1f}g
脂肪：{total_fat:.1f}g

用户信息：
- 性别：{gender}
- 年龄：{age}岁
- 身高：{height_cm}cm
- 体重：{weight_kg}kg
- BMI：{bmi:.2f}
- 每日所需卡路里：{daily_calorie_needs:.0f}大卡
- 健康评估：{health_assessment}

请给出2-3条专业的健康点评，包含针对该用户的个性化建议。"""

HEALTH_REVIEW_EXERCISE_PROMPT = """请对以下运动分析结果进行健康点评：

运动分析结果：
{exercises_summary}

总消耗：{total_burned:.0f} 大卡

请给出2-3条专业的健康点评。"""

HEALTH_REVIEW_EXERCISE_WITH_USER_PROMPT = """请对以下运动分析结果进行健康点评，并结合用户个人信息给出个性化建议：

运动分析结果：
{exercises_summary}

总消耗：{total_burned:.0f} 大卡

用户信息：
- 性别：{gender}
- 年龄：{age}岁
- 身高：{height_cm}cm
- 体重：{weight_kg}kg
- BMI：{bmi:.2f}
- 每日所需卡路里：{daily_calorie_needs:.0f}大卡
- 健康评估：{health_assessment}

请给出2-3条专业的健康点评，包含针对该用户的个性化建议。"""

HEALTH_REVIEW_BOTH_PROMPT = """请对以下饮食和运动分析结果进行综合健康点评：

饮食分析：
{foods_summary}
总摄入：{total_calories:.0f} 大卡

运动分析：
{exercises_summary}
总消耗：{total_burned:.0f} 大卡

净摄入：{net_calories:.0f} 大卡

请给出3-4条专业的综合健康点评。"""

HEALTH_REVIEW_BOTH_WITH_USER_PROMPT = """请对以下饮食和运动分析结果进行综合健康点评，并结合用户个人信息给出个性化建议：

饮食分析：
{foods_summary}
总摄入：{total_calories:.0f} 大卡

运动分析：
{exercises_summary}
总消耗：{total_burned:.0f} 大卡

净摄入：{net_calories:.0f} 大卡

用户信息：
- 性别：{gender}
- 年龄：{age}岁
- 身高：{height_cm}cm
- 体重：{weight_kg}kg
- BMI：{bmi:.2f}
- 每日所需卡路里：{daily_calorie_needs:.0f}大卡
- 健康评估：{health_assessment}

请给出3-4条专业的综合健康点评，包含针对该用户的个性化建议。"""