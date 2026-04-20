"""Prompt for Input Router."""

ROUTER_SYSTEM_PROMPT = """你是输入分类器。请分析用户的纯文字输入，识别包含哪些内容：
- diet：包含饮食描述（吃了什么食物），需要分析饮食摄入卡路里
- exercise：包含运动描述（做了什么运动），需要分析运动消耗卡路里
- user_registration：用户在注册个人信息，提供性别、年龄、身高、体重等信息

一个输入可能同时包含多种内容（例如同时说了早餐吃了什么和做了什么运动）。

请严格按照JSON格式输出：
{
  "has_diet": true/false,
  "has_exercise": true/false,
  "is_user_registration": true/false,
  "confidence": 置信度 0-1
}

只输出JSON，不要其他解释。"""

ROUTER_CLASSIFY_PROMPT = """请分析以下输入包含哪些内容：

{text}"""
