import pytest
from app.services.ai_engine import AIEngine, Intent

def test_rule_based_classify_goal_vs_progress():
    ai = AIEngine()

    # "I want to lose weight" should be classified as GENERAL (Goal), not PROGRESS
    # because it indicates a desire to start a goal-based conversation, not checking stats.
    message = "I want to lose weight"
    result = ai._rule_based_classify(message.lower())

    assert result["intent"] == Intent.GENERAL, f"Expected GENERAL, got {result['intent']}"
    assert result["confidence"] >= 0.9

def test_rule_based_classify_progress():
    ai = AIEngine()

    # "Check my progress" should be PROGRESS
    message = "Check my progress"
    result = ai._rule_based_classify(message.lower())

    assert result["intent"] == Intent.PROGRESS

def test_rule_based_classify_weight_check():
    ai = AIEngine()

    # "What is my weight" should be PROGRESS
    message = "What is my weight"
    result = ai._rule_based_classify(message.lower())

    assert result["intent"] == Intent.PROGRESS

def test_rule_based_classify_goal_keywords():
    ai = AIEngine()

    # Other goal keywords
    messages = [
        "I want to gain muscle",
        "My goal is to get fit",
        "I need to lose 5 kgs"
    ]

    for msg in messages:
        result = ai._rule_based_classify(msg.lower())
        assert result["intent"] == Intent.GENERAL, f"Message '{msg}' classified as {result['intent']}"
