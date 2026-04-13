import re
import string
import os
from django.conf import settings
from .apps import CustomerPortalConfig
import json

# Categories from the NLP Case Study
CATEGORIES = {
    0: "Bank Account Services",
    1: "Credit Card / Prepaid Card",
    2: "Others",
    3: "Theft / Dispute Reporting",
    4: "Mortgages / Loans"
}

def clean_text(text):
    """Regex based cleaning identical to the Case Study."""
    text = text.lower()
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'[%s]' % re.escape(string.punctuation), '', text)
    text = re.sub(r'\w*\d\w*', '', text)
    return text

class NLPClassifier:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NLPClassifier, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized: return
        self._initialized = True
        self.api_key = os.environ.get('GOOGLE_API_KEY')
        if self.api_key:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.model_gemini = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model_gemini = None

    def classify_ticket(self, text):
        """
        Uses the fine-tuned BERT model to categorize the ticket.
        Falls back to keyword matching if the model is unavailable.
        """
        tokenizer = CustomerPortalConfig.tokenizer
        model = CustomerPortalConfig.model
        
        if tokenizer and model:
            try:
                import torch
                inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=128)
                with torch.no_grad():
                    outputs = model(**inputs)
                
                probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
                prediction_id = torch.argmax(probabilities, dim=-1).item()
                confidence = probabilities[0][prediction_id].item() * 100

                # Map BERT indices to our labels
                # Note: The BERT model might have different labels than SEED_DATA
                # Based on views.py, it expects: {0: "Technical Discrepancy", 1: "Account/Billing", 2: "Operational Feedback"}
                # But nlp_pipeline.py originally had financial categories.
                # We will stick to the enterprise narrative:
                labels = {0: "Technical Discrepancy", 1: "Account/Billing", 2: "Operational Feedback"}
                return labels.get(prediction_id, "Inquiry"), round(confidence, 2)
            except Exception as e:
                print(f"[NLP Pipeline] BERT prediction error: {e}")

        if CustomerPortalConfig.remote_mode and self.model_gemini:
            try:
                prompt = f"Categorize this support ticket text into one of these: [Technical Discrepancy, Account/Billing, Operational Feedback]. Text: '{text}'. Return only JSON: {{\"category\": \"CATEGORY_NAME\", \"confidence\": 95}}"
                response = self.model_gemini.generate_content(prompt)
                extracted_text = response.text.strip('` \n').replace('json', '')
                res_data = json.loads(extracted_text)
                return res_data.get('category', 'Inquiry'), res_data.get('confidence', 90.0)
            except Exception as e:
                print(f"[NLP Pipeline] Gemini Triage Error: {e}")

        # Keyword Fallback
        processed = clean_text(text)
        mapping = [
            ("Account/Billing", ["bill", "pay", "charge", "refund", "credit", "card"]),
            ("Technical Discrepancy", ["error", "bug", "broken", "fail", "slow", "crash"]),
            ("Operational Feedback", ["suggestion", "improvement", "love", "great", "ux"])
        ]
        
        for label, keywords in mapping:
            if any(re.search(r'\b' + re.escape(w), processed) for w in keywords):
                return label, 85.0
                
        return "Others", 70.0

    def get_urgency_and_priority(self, text):
        """
        Uses Zero-Shot classification to determine urgency and priority.
        """
        pipeline = CustomerPortalConfig.intent_pipeline
        input_lower = text.lower()
        
        priority = "P3"
        urgency_label = "Standard"
        confidence = 0.0

        if pipeline:
            try:
                candidate_labels = ["Critical Emergency", "High Urgency", "Standard Request"]
                result = pipeline(text, candidate_labels)
                top_label = result['labels'][0]
                confidence = result['scores'][0]

                if top_label == "Critical Emergency":
                    priority = "P1"
                    urgency_label = "Critical"
                elif top_label == "High Urgency":
                    priority = "P2"
                    urgency_label = "High"
                else:
                    priority = "P3"
                    urgency_label = "Standard"
            except Exception as e:
                print(f"[NLP Pipeline] Urgency detection error: {e}")

        if CustomerPortalConfig.remote_mode and self.model_gemini and confidence < 0.1:
            try:
                prompt = f"Analyze urgency for this ticket: '{text}'. Categories: [Critical Emergency, High Urgency, Standard Request]. Return JSON: {{\"label\": \"LABEL\", \"priority\": \"P1/P2/P3\", \"confidence\": 0.9}}"
                response = self.model_gemini.generate_content(prompt)
                res_data = json.loads(response.text.strip('` \n').replace('json', ''))
                urgency_label = res_data.get('label', 'Standard')
                priority = res_data.get('priority', 'P3')
                confidence = res_data.get('confidence', 0.8)
            except Exception as e:
                print(f"[NLP Pipeline] Gemini Urgency Error: {e}")

        # Keyword boost
        p1_keywords = ["emergency", "outage", "production down", "critical failure", "security breach", "data loss", "cannot access"]
        if any(w in input_lower for w in p1_keywords):
            priority = "P1"
            urgency_label = "Critical (Override)"

        return priority, urgency_label, round(confidence * 100, 2)

    def get_sentiment(self, text):
        """
        Detects customer sentiment (Happy/Neutral vs Angry/Frustrated).
        """
        pipeline = CustomerPortalConfig.moderation_pipeline
        # If moderation_pipeline is not loaded, we can use the intent_pipeline as a fallback for sentiment
        fallback_pipeline = CustomerPortalConfig.intent_pipeline
        
        sentiment = "Neutral"
        score = 0.0

        if pipeline:
            try:
                result = pipeline(text)[0]
                label = result['label'].lower()
                score = result['score']
                
                # Handling cardiffnlp labels: negative, neutral, positive
                if label == 'negative':
                    sentiment = "Angry/Frustrated"
                elif label == 'positive':
                    sentiment = "Happy/Satisfied"
                elif label == 'neutral':
                    sentiment = "Professional"
                # Fallback for toxic-comment-model if used instead
                elif label == 'toxic':
                    sentiment = "Angry/Frustrated"
                else:
                    sentiment = "Professional"
            except:
                pass
        elif fallback_pipeline:
            try:
                labels = ["Angry/Frustrated", "Neutral", "Happy/Satisfied"]
                result = fallback_pipeline(text, labels)
                sentiment = result['labels'][0]
                score = result['scores'][0]
            except:
                pass
        
        return sentiment, round(score * 100, 2)

    def get_assigned_squad(self, text):
        """Determines which squad should handle the ticket."""
        creative_keywords = ["button", "css", "layout", "visual", "ui", "ux", "responsive", "frontend", "color", "header", "footer", "interface", "animation", "style", "display"]
        systems_keywords = ["api", "database", "server", "slow", "performance", "backend", "connection", "error 500", "db", "auth", "infrastructure", "latency", "system", "offline", "crash"]
        
        input_lower = text.lower()
        if any(w in input_lower for w in creative_keywords):
            return "Creative Architecture"
        elif any(w in input_lower for w in systems_keywords):
            return "Systems Engine"
        
        return "Neural Insights"

# Singleton instance
classifier = NLPClassifier()

