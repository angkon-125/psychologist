#!/usr/bin/env python3
"""
Synthetic Conscious Emotion Architecture (SCEA) Example Simulation
"""

from scea import SCEA
import random
import time


def main():
    print("=" * 70)
    print("Synthetic Conscious Emotion Architecture (SCEA)")
    print("=" * 70)
    
    scea = SCEA()
    
    print("\n[*] Initializing SCEA Organism...")
    print(f"   Step 0: {scea.state.time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    scenario_events = [
        {'type': 'novelty', 'intensity': 0.8, 'satisfy_need': 'exploration'},
        {'type': 'social_connection', 'intensity': 0.6, 'satisfy_need': 'social'},
        {'type': 'achievement', 'intensity': 0.7, 'satisfy_need': 'achievement'},
        {'type': 'positive_event', 'intensity': 0.5},
        {'type': 'threat', 'intensity': 0.4},
        {'type': 'negative_event', 'intensity': 0.3},
        {'type': 'social_connection', 'intensity': 0.7, 'satisfy_need': 'social'},
        {'type': 'novelty', 'intensity': 0.5, 'satisfy_need': 'knowledge'},
        {'type': 'recognition', 'intensity': 0.6, 'satisfy_need': 'achievement'},
        {'type': 'positive_event', 'intensity': 0.8}
    ]
    
    print("\n[*] Simulation starting...")
    print("-" * 70)
    
    history = []
    
    for step in range(1, 21):
        event = scenario_events[(step - 1) % len(scenario_events)]
        
        if step % 3 == 0:
            scea.interact_with_entity(
                entity_id="user_1",
                interaction_type="conversation",
                positive=random.random() > 0.3
            )
        
        result = scea.add_experience(event['type'], intensity=event.get('intensity', 0.5))
        
        history.append(result)
        
        print(f"\n[>] Step {result['step']}")
        print(f"   Decision: {result['decision']['description']}")
        
        print(f"   Emotions:")
        dominant = result['emotions']['dominant']
        valence = result['emotions']['valence']
        intensity = result['emotions']['intensity']
        print(f"     Dominant: {dominant} (valence: {valence:+.2f}, intensity: {intensity:.2f})")
        
        print(f"   Neurochemistry:")
        neuro = result['neurochemistry']
        print(f"     Dopamine: {neuro['dopamine']:.2f}, Serotonin: {neuro['serotonin']:.2f}")
        print(f"     Oxytocin: {neuro['oxytocin']:.2f}, Cortisol: {neuro['cortisol']:.2f}, Adrenaline: {neuro['adrenaline']:.2f}")
        
        print(f"   Identity:")
        identity = result['identity']
        print(f"     Self-confidence: {identity['self_confidence']:.2f}, Consistency: {identity['consistency']:.2f}")
        print(f"     Self-image: {', '.join([f'{k}:{v:.2f}' for k,v in identity['self_image'].items()])}")
        
        print(f"   Cognitive dissonance: {result['cognitive_dissonance']:.2f}")
        print(f"   Attention focus: {result['consciousness']['attention_focus']}")
        
        time.sleep(0.1)
    
    print("\n" + "=" * 70)
    print("Simulation Complete!")
    print("=" * 70)
    
    print("\n[Summary Statistics]")
    total_steps = len(history)
    dominant_emotions = {}
    for h in history:
        d = h['emotions']['dominant']
        dominant_emotions[d] = dominant_emotions.get(d, 0) + 1
    
    print(f"  Total steps: {total_steps}")
    print(f"  Dominant emotions distribution:")
    for emotion, count in sorted(dominant_emotions.items(), key=lambda x: x[1], reverse=True):
        print(f"    {emotion:12s}: {count:3d} ({count/total_steps*100:.1f}%)")
    
    final_identity = history[-1]['identity']
    print(f"\n  Final identity:")
    print(f"    Self-confidence: {final_identity['self_confidence']:.2f}")
    print(f"    Consistency: {final_identity['consistency']:.2f}")
    
    print("\n[*] SCEA has successfully evolved!")


if __name__ == "__main__":
    main()
