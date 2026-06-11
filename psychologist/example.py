from emotion_engine import EmotionEngine
from emotion_engine.models import PersonalityTraits


def main():
    print("=" * 60)
    print("Human Emotion Intelligence Engine - Example")
    print("=" * 60)
    
    personality = PersonalityTraits(
        openness=0.7,
        conscientiousness=0.6,
        extraversion=0.5,
        agreeableness=0.8,
        neuroticism=0.3,
        optimism=0.7,
        compassion=0.8,
        confidence=0.6
    )
    
    engine = EmotionEngine(personality)
    
    print("\nInitial Personality Profile:")
    for trait, value in engine.get_personality().items():
        print(f"  {trait:20s}: {value:.2f}")
    
    test_inputs = [
        "I just got a promotion at work! I'm so happy!",
        "But I'm worried I won't be able to handle the new responsibilities...",
        "To be honest, I've been feeling really stressed lately with all the changes.",
        "My best friend called me today and made me feel so much better!"
    ]
    
    for i, text in enumerate(test_inputs, 1):
        print(f"\n{'=' * 60}")
        print(f"Interaction {i}: {text}")
        print(f"{'=' * 60}")
        
        result = engine.process_input(text)
        
        print(f"\nDominant Emotion: {result['dominant_emotion']}")
        print(f"Response: {result['response']}")
        
        print("\nPrimary Emotions:")
        for emotion, value in result['emotional_state']['primary_emotions'].items():
            if value > 0.01:
                print(f"  {emotion:12s}: {value:.2f} {'#' * int(value * 20)}")
        
        print("\nSecondary Emotions:")
        for emotion, value in result['emotional_state']['secondary_emotions'].items():
            if value > 0.01:
                print(f"  {emotion:12s}: {value:.2f} {'#' * int(value * 20)}")
        
        print(f"\nReasoning Mode: {result['reasoning']['mode']}")
        print(f"Predicted Next Emotions: {result['predictions']['next_emotions']}")
        print(f"Engagement Level: {result['predictions']['engagement']:.2f}")


if __name__ == "__main__":
    main()
