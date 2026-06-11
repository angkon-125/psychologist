try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    import networkx as nx
    VIZ_AVAILABLE = True
except ImportError:
    VIZ_AVAILABLE = False

from typing import Dict, List
import json
from datetime import datetime


class EmotionDashboard:
    def __init__(self):
        self.available = VIZ_AVAILABLE
        self.history = []

    def add_state(self, state: dict):
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'state': state
        })

    def plot_emotion_history(self, output_path: str = "emotion_history.png"):
        if not self.available or len(self.history) < 2:
            return False
        
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            emotions = [
                'happiness', 'sadness', 'anger', 'fear', 
                'surprise', 'disgust', 'anxiety', 'excitement'
            ]
            timestamps = []
            values = {e: [] for e in emotions}
            
            for entry in self.history:
                state = entry['state']
                ts = datetime.fromisoformat(entry['timestamp'])
                timestamps.append(ts)
                for e in emotions:
                    val = 0
                    if 'primary_emotions' in state and e in state['primary_emotions']:
                        val = state['primary_emotions'][e]
                    elif 'secondary_emotions' in state and e in state['secondary_emotions']:
                        val = state['secondary_emotions'][e]
                    values[e].append(val)
            
            for emotion in emotions:
                ax.plot(timestamps, values[emotion], label=emotion, linewidth=2)
            
            ax.set_title('Emotion History', fontsize=14, pad=20)
            ax.set_xlabel('Time')
            ax.set_ylabel('Intensity (0-1)')
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax.grid(alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            return True
        except Exception as e:
            print(f"Error plotting: {e}")
            return False

    def plot_personality_radar(self, personality: Dict[str, float], output_path: str = "personality_radar.png"):
        if not self.available:
            return False
        
        try:
            fig = plt.figure(figsize=(8, 8))
            ax = fig.add_subplot(111, polar=True)
            
            categories = list(personality.keys())[:8]
            values = [personality[c] for c in categories]
            N = len(categories)
            
            angles = [n / float(N) * 2 * 3.14159 for n in range(N)]
            angles += angles[:1]
            values += values[:1]
            
            ax.plot(angles, values, 'o-', linewidth=2, label='Personality')
            ax.fill(angles, values, alpha=0.25)
            
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories)
            ax.set_ylim(0, 1)
            ax.set_title('Personality Profile', size=14, pad=20)
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=300)
            plt.close()
            return True
        except Exception as e:
            print(f"Error plotting: {e}")
            return False

    def plot_emotion_network(self, output_path: str = "emotion_network.png"):
        if not self.available:
            return False
        
        try:
            fig = plt.figure(figsize=(10, 10))
            
            G = nx.Graph()
            
            emotions = [
                'happiness', 'sadness', 'anger', 'fear',
                'surprise', 'excitement', 'anxiety', 'trust'
            ]
            G.add_nodes_from(emotions)
            
            connections = [
                ('happiness', 'excitement'), ('happiness', 'trust'),
                ('sadness', 'anxiety'), ('anger', 'sadness'),
                ('fear', 'anxiety'), ('surprise', 'excitement')
            ]
            G.add_edges_from(connections)
            
            pos = nx.spring_layout(G, seed=42)
            nx.draw_networkx_nodes(G, pos, node_size=2000, node_color='skyblue', alpha=0.8)
            nx.draw_networkx_edges(G, pos, width=2, alpha=0.6)
            nx.draw_networkx_labels(G, pos, font_size=12, font_weight='bold')
            
            plt.title('Emotion Connection Network', fontsize=14, pad=20)
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(output_path, dpi=300)
            plt.close()
            return True
        except Exception as e:
            print(f"Error plotting: {e}")
            return False

    def export_report(self, output_path: str = "emotion_report.json"):
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_states': len(self.history),
            'history': self.history
        }
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        return True
