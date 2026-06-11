import re
from typing import Dict, List, Tuple


class SentimentAnalyzer:
    def __init__(self):
        self.positive_words = {
            'happy', 'joy', 'love', 'great', 'excellent', 'amazing', 'wonderful',
            'fantastic', 'beautiful', 'cheerful', 'excited', 'glad', 'pleased',
            'delighted', 'thrilled', 'content', 'peaceful', 'calm', 'grateful',
            'thankful', 'optimistic', 'hopeful', 'proud', 'confident', 'successful',
            'achievement', 'victory', 'win', 'accomplished', 'blessed', 'lucky'
        }
        self.negative_words = {
            'sad', 'unhappy', 'angry', 'mad', 'hate', 'terrible', 'awful',
            'horrible', 'bad', 'worse', 'worst', 'depressed', 'miserable',
            'upset', 'frustrated', 'anxious', 'worried', 'fearful', 'scared',
            'afraid', 'disgusted', 'ashamed', 'guilty', 'regretful', 'lonely',
            'alone', 'hopeless', 'pessimistic', 'disappointed', 'failure',
            'defeat', 'loss', 'suffer', 'pain', 'hurt', 'struggle'
        }
        self.intensifiers = {
            'very', 'extremely', 'incredibly', 'absolutely', 'completely',
            'totally', 'utterly', 'really', 'quite', 'fairly', 'pretty',
            'so', 'too', 'highly', 'deeply', 'strongly'
        }
        self.negators = {
            'not', "n't", 'never', 'no', 'none', 'nothing', 'nobody', 'nowhere'
        }

    def analyze_text(self, text: str) -> Dict:
        words = self._tokenize(text)
        sentiment_score = 0.0
        intensity = 0.0
        word_sentiments = []
        
        i = 0
        while i < len(words):
            word = words[i].lower()
            multiplier = 1.0
            negated = False
            
            if i > 0:
                prev_word = words[i-1].lower()
                if prev_word in self.intensifiers:
                    multiplier = 1.5
                if prev_word in self.negators:
                    negated = True
            
            if word in self.positive_words:
                score = multiplier if not negated else -multiplier
                sentiment_score += score
                word_sentiments.append((word, score))
            elif word in self.negative_words:
                score = -multiplier if not negated else multiplier
                sentiment_score += score
                word_sentiments.append((word, score))
            
            if word in self.intensifiers:
                intensity += 0.2
            
            i += 1
        
        normalized_sentiment = max(-1.0, min(1.0, sentiment_score / max(1, len(word_sentiments))))
        normalized_intensity = min(1.0, intensity + (abs(normalized_sentiment) * 0.5))
        
        return {
            'sentiment': normalized_sentiment,
            'intensity': normalized_intensity,
            'word_sentiments': word_sentiments,
            'positive_count': sum(1 for w, s in word_sentiments if s > 0),
            'negative_count': sum(1 for w, s in word_sentiments if s < 0)
        }

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\b\w+(?:'\w+)?\b", text)

    def detect_emotion_keywords(self, text: str) -> Dict[str, List[str]]:
        words = self._tokenize(text)
        emotions = {
            'happiness': [], 'sadness': [], 'anger': [], 'fear': [],
            'surprise': [], 'disgust': [], 'anxiety': [], 'frustration': []
        }
        
        emotion_keywords = {
            'happiness': ['happy', 'joy', 'love', 'great', 'excellent', 'amazing', 'wonderful', 'cheerful', 'excited', 'glad'],
            'sadness': ['sad', 'unhappy', 'depressed', 'miserable', 'down', 'heartbroken', 'sorrow'],
            'anger': ['angry', 'mad', 'furious', 'outraged', 'irritated', 'annoyed'],
            'fear': ['afraid', 'scared', 'fearful', 'terrified', 'frightened', 'worried'],
            'surprise': ['surprised', 'shocked', 'amazed', 'astonished', 'unexpected'],
            'disgust': ['disgusted', 'revolted', 'nauseated', 'repulsed'],
            'anxiety': ['anxious', 'worried', 'nervous', 'tense', 'uneasy'],
            'frustration': ['frustrated', 'annoyed', 'irritated', 'exasperated']
        }
        
        for word in words:
            lower_word = word.lower()
            for emotion, keywords in emotion_keywords.items():
                if lower_word in keywords:
                    emotions[emotion].append(word)
        
        return emotions
