import os
import logging
import re
from typing import List, Dict, Any
# Simplified sentiment analysis without heavy AI dependencies
# from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
# import torch

logger = logging.getLogger(__name__)

class SwedishSentimentAnalyzer:
    def __init__(self):
        self.analyzer = None
        self.tokenizer = None
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize enhanced Swedish sentiment analysis"""
        try:
            # Enhanced Swedish sentiment analysis with more comprehensive word lists
            self.positive_words = {
                # Swedish positive words
                'bra', 'fantastisk', 'utmärkt', 'perfekt', 'underbar', 'toppenklass',
                'rekommenderar', 'nöjd', 'glad', 'lysande', 'grym', 'suverän',
                'strålande', 'magnifik', 'outstanding', 'förtjusande', 'härlig',
                'fenomenal', 'otrolig', 'enastående', 'felfri', 'imponerande',
                'tillfredsställande', 'prisvärd', 'effektiv', 'snabb', 'hjälpsam',
                'vänlig', 'professionell', 'kvalitet', 'värd', 'rekommenderar starkt',
                'älskar', 'fantastisk service', 'bästa', 'toppen', 'superbra',
                'kämpa', 'tacksam', 'imponerad', 'överträffade förväntningar',
                
                # English positive words
                'excellent', 'amazing', 'great', 'good', 'perfect', 'wonderful',
                'love', 'awesome', 'best', 'brilliant', 'outstanding', 'fantastic',
                'superb', 'marvelous', 'exceptional', 'impressive', 'satisfying',
                'pleased', 'delighted', 'thrilled', 'happy', 'satisfied',
                'recommend', 'worth', 'value', 'quality', 'fast', 'friendly',
                'helpful', 'professional', 'efficient', 'exceeded expectations'
            }
            
            self.negative_words = {
                # Swedish negative words  
                'dålig', 'hemsk', 'fruktansvärd', 'besviken', 'sämst', 'trasig',
                'problem', 'fel', 'kass', 'usel', 'ruskig', 'otillfredsställande',
                'besvikelse', 'irriterande', 'förfärlig', 'katastrofal', 'värdelös',
                'opålitlig', 'långsam', 'dyr', 'överpris', 'svårt', 'komplicerat',
                'otrevlig', 'oprofessionell', 'slarvig', 'bristfällig', 'misslyckad',
                'ånger', 'slöseri', 'inte värt', 'rekommenderar inte', 'undvik',
                'bedrägeri', 'bluff', 'skandal', 'försenad', 'förlorad', 'skadad',
                
                # English negative words
                'bad', 'terrible', 'awful', 'worst', 'horrible', 'hate',
                'disappointed', 'broken', 'failed', 'poor', 'wrong', 'disgusting',
                'useless', 'waste', 'scam', 'fraud', 'delayed', 'damaged',
                'unreliable', 'slow', 'expensive', 'overpriced', 'complicated',
                'unprofessional', 'rude', 'regret', 'avoid', 'not recommend'
            }
            
            # Negation words that can flip sentiment
            self.negation_words = {
                'inte', 'icke', 'ej', 'aldrig', 'ingenting', 'inget', 'ingen',
                'not', 'no', 'never', 'nothing', 'none', 'neither', 'nor'
            }
            
            # Intensifiers that increase sentiment strength
            self.intensifiers = {
                'mycket': 1.5, 'väldigt': 1.5, 'extremt': 2.0, 'otroligt': 2.0,
                'helt': 1.3, 'verkligen': 1.4, 'absolut': 1.8, 'definitivt': 1.4,
                'very': 1.5, 'extremely': 2.0, 'absolutely': 1.8, 'really': 1.4,
                'incredibly': 2.0, 'totally': 1.6, 'completely': 1.7, 'quite': 1.2
            }
            
            logger.info("Loaded enhanced Swedish sentiment analyzer")
                
        except Exception as e:
            logger.error(f"Failed to initialize sentiment model: {e}")
            self.analyzer = None
    
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess Swedish text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        return text
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Enhanced sentiment analysis with Swedish language support"""
        if not text:
            return {
                'sentiment': 'neutral',
                'score': 0.5,
                'confidence': 0.0,
                'scores': {}
            }
        
        try:
            # Preprocess text
            clean_text = self.preprocess_text(text).lower()
            
            if len(clean_text) < 3:  # Too short to analyze
                return {
                    'sentiment': 'neutral',
                    'score': 0.5,
                    'confidence': 0.1,
                    'scores': {}
                }
            
            # Tokenize text
            words = clean_text.split()
            
            positive_score = 0
            negative_score = 0
            word_count = 0
            
            # Analyze each word with context
            for i, word in enumerate(words):
                # Check for negation before this word
                negated = False
                if i > 0 and words[i-1] in self.negation_words:
                    negated = True
                elif i > 1 and words[i-2] in self.negation_words:
                    negated = True
                
                # Check for intensifiers before this word
                intensity = 1.0
                if i > 0 and words[i-1] in self.intensifiers:
                    intensity = self.intensifiers[words[i-1]]
                elif i > 1 and words[i-2] in self.intensifiers:
                    intensity = self.intensifiers[words[i-2]]
                
                # Calculate sentiment for this word
                if word in self.positive_words:
                    score = 1.0 * intensity
                    if negated:
                        negative_score += score
                    else:
                        positive_score += score
                    word_count += 1
                    
                elif word in self.negative_words:
                    score = 1.0 * intensity
                    if negated:
                        positive_score += score
                    else:
                        negative_score += score
                    word_count += 1
            
            # Calculate final sentiment
            if word_count == 0:
                # No sentiment words found, return neutral with low confidence
                return {
                    'sentiment': 'neutral',
                    'score': 0.5,
                    'confidence': 0.2,
                    'scores': {'positive': 0, 'negative': 0, 'word_count': 0}
                }
            
            # Normalize scores
            total_score = positive_score + negative_score
            if total_score == 0:
                sentiment_score = 0.5
                confidence = 0.1
            else:
                sentiment_score = positive_score / total_score
                confidence = min(word_count / len(words), 1.0)
            
            # Determine sentiment category
            if sentiment_score > 0.6:
                sentiment = 'positive'
            elif sentiment_score < 0.4:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'
            
            return {
                'sentiment': sentiment,
                'score': sentiment_score,
                'confidence': confidence,
                'scores': {
                    'positive': positive_score,
                    'negative': negative_score,
                    'word_count': word_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {
                'sentiment': 'neutral',
                'score': 0.5,
                'confidence': 0.0,
                'scores': {}
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {
                'sentiment': 'neutral',
                'score': 0.5,
                'confidence': 0.0,
                'scores': {}
            }
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from Swedish text"""
        if not text:
            return []
        
        # Simple keyword extraction based on common Swedish patterns
        # In a production environment, you'd use more sophisticated NLP
        
        # Remove common Swedish stop words
        stop_words = {
            'och', 'i', 'att', 'det', 'som', 'på', 'de', 'av', 'för', 'till', 'är', 'en', 'den', 
            'har', 'inte', 'var', 'om', 'med', 'kan', 'man', 'så', 'från', 'ut', 'när', 'bara',
            'sina', 'där', 'nu', 'över', 'skulle', 'då', 'hade', 'upp', 'mot', 'också', 'än',
            'mycket', 'bra', 'dålig', 'dåligt', 'bättre', 'sämre', 'helt', 'väldigt', 'riktigt'
        }
        
        # Clean and tokenize
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # Filter out stop words and short words
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        
        # Count frequency and return most common
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, freq in sorted_keywords[:max_keywords]]
    
    def batch_analyze(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Analyze sentiment for multiple texts"""
        results = []
        for text in texts:
            result = self.analyze_sentiment(text)
            result['keywords'] = self.extract_keywords(text)
            results.append(result)
        
        return results

# Global instance
sentiment_analyzer = SwedishSentimentAnalyzer()
