#!/usr/bin/env python3
"""SlimCheck - Calorie management multi-agent system."""

import click
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from src.graph.calorie_graph import create_calorie_graph
from src.graph.state import CalorieState
from src.utils.image_utils import load_image_from_file, image_to_base64
from src.models import AnalysisResult
from src.storage import get_user_storage
from src.utils.logger import logger

console = Console()
app = create_calorie_graph()

@click.group()
def cli():
    """SlimCheck - 卡路里管理多智能体系统."""
    pass

@cli.command()
@click.option('--gender', '-g', required=True, type=click.Choice(['male', 'female']), help='性别: male/female')
@click.option('--age', '-a', required=True, type=int, help='年龄')
@click.option('--height', '-H', required=True, type=float, help='身高(厘米)')
@click.option('--weight', '-w', required=True, type=float, help='体重(公斤)')
@click.option('--activity', '-A', default='moderate', type=click.Choice(['sedentary', 'light', 'moderate', 'active', 'very_active']), help='活动水平')
@click.option('--name', '-n', help='姓名(可选)')
def register(gender, age, height, weight, activity, name):
    """注册新用户，创建个人健康档案."""
    from src.models import UserProfile

    # Format input text for extraction
    text_parts = [
        f"性别: {gender}",
        f"年龄: {age}",
        f"身高: {height}cm",
        f"体重: {weight}kg",
        f"活动水平: {activity}",
    ]
    if name:
        text_parts.append(f"姓名: {name}")
    text = "\n".join(text_parts)

    initial_state: CalorieState = {
        "input_type": "text_only",
        "image_data": None,
        "image_base64": None,
        "text_input": text,
        "person_id": None,
        "user_profile": None,
        "content_type": "user_registration",
        "analyzed_foods": None,
        "analyzed_exercise": None,
        "_has_diet": False,
        "_has_exercise": False,
        "_is_user_registration": False,
        "analysis_result": None,
        "requires_user_input": False,
        "missing_fields": None,
        "error_message": None,
    }

    with console.status("[bold green]处理中..."):
        result = app.invoke(initial_state)

    if result.get("requires_user_input"):
        missing = result.get("missing_fields", [])
        console.print(f"[yellow]需要补充信息: {', '.join(missing)}[/yellow]")
        return

    if result.get("error_message"):
        console.print(f"[red]错误: {result['error_message']}[/red]")
        return

    analysis = result.get("analysis_result")
    profile = analysis.user_profile

    console.print(Panel.fit(
        f"[bold green]OK 用户档案创建成功[/]\n\n"
        f"人物ID: [bold]{profile.person_id}[/]\n"
        f"姓名: {profile.name or '-'}\n"
        f"性别: {'男' if profile.gender == 'male' else '女'}\n"
        f"年龄: {profile.age} 岁\n"
        f"身高: {profile.height_cm} cm\n"
        f"体重: {profile.weight_kg} kg\n"
        f"BMI: [bold]{profile.bmi:.2f}[/]\n"
        f"基础代谢: {profile.bmr:.0f} 大卡/天\n"
        f"每日所需: {profile.daily_calorie_needs:.0f} 大卡/天\n"
        f"评估: {profile.health_assessment}\n\n"
        f"[dim]请保存好人物ID，后续分析可以使用 --person-id 参数[/]",
        title="注册结果"
    ))

@cli.command()
@click.argument('image_path', type=click.Path(exists=True))
@click.option('--text', '-t', help='附加文字描述')
@click.option('--person-id', '-p', help='人物ID(可选，用于个性化建议)')
def image(image_path, text, person_id):
    """分析图片中的食物，计算卡路里."""
    image_bytes = load_image_from_file(image_path)
    if not image_bytes:
        console.print(f"[red]无法加载图片: {image_path}[/red]")
        sys.exit(1)

    image_b64 = image_to_base64(image_bytes)
    input_type = "image_with_text" if text and text.strip() else "image"

    initial_state: CalorieState = {
        "input_type": input_type,
        "image_data": image_bytes,
        "image_base64": image_b64,
        "text_input": text,
        "person_id": person_id,
        "user_profile": None,
        "content_type": None,
        "analyzed_foods": None,
        "analyzed_exercise": None,
        "_has_diet": False,
        "_has_exercise": False,
        "_is_user_registration": False,
        "analysis_result": None,
        "requires_user_input": False,
        "missing_fields": None,
        "error_message": None,
    }

    with console.status("[bold green]AI 分析图片中..."):
        result = app.invoke(initial_state)

    display_result(result)

@cli.command()
@click.argument('text', type=str)
@click.option('--person-id', '-p', help='人物ID(可选，用于个性化建议)')
def diet(text, person_id):
    """分析纯文字描述的饮食，计算卡路里."""
    initial_state: CalorieState = {
        "input_type": "text_only",
        "image_data": None,
        "image_base64": None,
        "text_input": text,
        "person_id": person_id,
        "user_profile": None,
        "content_type": "diet",
        "analyzed_foods": None,
        "analyzed_exercise": None,
        "_has_diet": False,
        "_has_exercise": False,
        "_is_user_registration": False,
        "analysis_result": None,
        "requires_user_input": False,
        "missing_fields": None,
        "error_message": None,
    }

    with console.status("[bold green]分析饮食中..."):
        result = app.invoke(initial_state)

    display_result(result)

@cli.command()
@click.argument('text', type=str)
@click.option('--person-id', '-p', help='人物ID(可选，用于个性化建议)')
def exercise(text, person_id):
    """分析纯文字描述的运动，计算卡路里消耗."""
    initial_state: CalorieState = {
        "input_type": "text_only",
        "image_data": None,
        "image_base64": None,
        "text_input": text,
        "person_id": person_id,
        "user_profile": None,
        "content_type": "exercise",
        "analyzed_foods": None,
        "analyzed_exercise": None,
        "_has_diet": False,
        "_has_exercise": False,
        "_is_user_registration": False,
        "analysis_result": None,
        "requires_user_input": False,
        "missing_fields": None,
        "error_message": None,
    }

    with console.status("[bold green]分析运动中..."):
        result = app.invoke(initial_state)

    display_result(result)

@cli.command()
def list_users():
    """列出所有已保存的用户."""
    storage = get_user_storage()
    users = storage.list_users()

    if not users:
        console.print("[yellow]没有找到保存的用户[/yellow]")
        return

    table = Table(title="已保存用户")
    table.add_column("人物ID", style="cyan")
    table.add_column("文件路径", style="dim")

    for user_id in sorted(users):
        table.add_row(user_id, f"data/users/{user_id}.json")

    console.print(table)

@cli.command()
@click.argument('person_id', type=str)
def show_user(person_id):
    """显示用户详细信息."""
    storage = get_user_storage()
    profile = storage.load(person_id)

    if not profile:
        console.print(f"[red]未找到用户: {person_id}[/red]")
        return

    console.print(Panel.fit(
        f"[bold]用户档案[/]\n\n"
        f"人物ID: [bold cyan]{profile.person_id}[/]\n"
        f"姓名: {profile.name or '-'}\n"
        f"性别: {'男' if profile.gender == 'male' else '女'}\n"
        f"年龄: {profile.age} 岁\n"
        f"身高: {profile.height_cm} cm\n"
        f"体重: {profile.weight_kg} kg\n"
        f"活动水平: {profile.activity_level}\n"
        f"BMI: [bold]{profile.bmi:.2f}[/]\n"
        f"基础代谢: {profile.bmr:.0f} 大卡/天\n"
        f"每日所需卡路里: {profile.daily_calorie_needs:.0f} 大卡\n"
        f"健康评估: {profile.health_assessment}\n"
        f"创建时间: {profile.created_at.strftime('%Y-%m-%d %H:%M')}",
        title="用户信息"
    ))

def display_result(result: dict):
    """Display analysis result using rich."""
    if result.get("requires_user_input"):
        missing = result.get("missing_fields", [])
        console.print(Panel(
            f"[yellow]需要补充信息:[/]\n\n{', '.join(missing)}",
            title="信息不完整"
        ))
        return

    if result.get("error_message"):
        console.print(Panel(
            f"[red]{result['error_message']}[/]",
            title="错误"
        ))
        return

    analysis = result.get("analysis_result")
    if not analysis:
        console.print("[yellow]没有分析结果[/yellow]")
        return

    # Display food table if we have food items
    if analysis.food_items:
        table = Table(title="食物分析结果")
        table.add_column("食物", style="bold")
        table.add_column("重量(g)", justify="right")
        table.add_column("卡路里", justify="right", style="green")
        table.add_column("蛋白质(g)", justify="right")
        table.add_column("碳水(g)", justify="right")
        table.add_column("脂肪(g)", justify="right")

        for food in analysis.food_items:
            table.add_row(
                food.food_name,
                f"{food.estimated_grams:.0f}",
                f"{food.calories:.0f}",
                f"{food.protein_g:.1f}",
                f"{food.carbs_g:.1f}",
                f"{food.fat_g:.1f}",
            )

        console.print(table)

    # Display exercise table if we have exercise items
    if analysis.exercise_items:
        table = Table(title="运动分析结果")
        table.add_column("运动", style="bold")
        table.add_column("时长(分钟)", justify="right")
        table.add_column("强度", justify="center")
        table.add_column("消耗卡路里", justify="right", style="green")

        for exercise in analysis.exercise_items:
            intensity_color = {
                "low": "blue",
                "moderate": "yellow",
                "high": "red",
            }.get(exercise.intensity, "white")
            table.add_row(
                exercise.exercise_type,
                f"{exercise.duration_minutes:.0f}",
                f"[{intensity_color}]{exercise.intensity}[/{intensity_color}]",
                f"{exercise.calories_burned:.0f}",
            )

        console.print(table)

    # Summary
    if analysis.food_items or analysis.exercise_items:
        summary_parts = []
        if analysis.total_calories_intake is not None:
            summary_parts.append(
                f"[bold]饮食总计:[/] {analysis.total_calories_intake:.0f} 大卡 | "
                f"蛋白质 {analysis.total_protein:.1f}g | "
                f"碳水 {analysis.total_carbs:.1f}g | "
                f"脂肪 {analysis.total_fat:.1f}g"
            )

        if analysis.total_calories_burned is not None:
            summary_parts.append(
                f"[bold]运动消耗:[/] {analysis.total_calories_burned:.0f} 大卡"
            )

        if analysis.user_profile and analysis.total_calories_intake:
            daily_need = analysis.user_profile.daily_calorie_needs
            percentage = analysis.total_calories_intake / daily_need * 100
            summary_parts.append(
                f"\n饮食占每日推荐摄入量 ({daily_need:.0f} 大卡) 的 {percentage:.0f}%"
            )

        console.print(Panel("\n".join(summary_parts), title="汇总"))

        if analysis.recommendations:
            console.print(Panel(
                "\n".join(f"• {rec}" for rec in analysis.recommendations),
                title="建议"
            ))

    # User registration already displayed in register command
    console.print(f"\n[bold green]{analysis.summary}[/]")

if __name__ == '__main__':
    cli()
