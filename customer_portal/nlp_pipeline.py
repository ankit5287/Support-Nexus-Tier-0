import re
import string
import os

# Categories from the NLP Case Study
CATEGORIES = {
    0: "Bank Account Services",
    1: "Credit Card / Prepaid Card",
    2: "Others",
    3: "Theft / Dispute Reporting",
    4: "Mortgages / Loans"
}

# Seed Dataset for training a demonstration model
SEED_DATA = [
    ("How do I change my bank account password for my savings account?", 0),
    ("I need to open a new checking account with your bank.", 0),
    ("My debit card is not working at the ATM.", 0),
    ("Can you help me set up direct deposit for my salary?", 0),
    ("I lost my credit card and need a replacement immediately.", 1),
    ("Why was I charged a late fee on my credit card bill?", 1),
    ("I want to increase the credit limit on my platinum card.", 1),
    ("How do I activate my new prepaid card?", 1),
    ("The mobile app keeps crashing whenever I try to log in.", 2),
    ("I love the new design of the portal, great job!", 2),
    ("There is a typo in the user manual for the digital wallet.", 2),
    ("How do I contact customer support via email?", 2),
    ("There is a fraudulent transaction on my account that I didn't authorize.", 3),
    ("I want to report a stolen identity and lock my accounts.", 3),
    ("Someone used my card to buy things in another country.", 3),
    ("I am disputing a charge from a merchant who never delivered the goods.", 3),
    ("What are the current interest rates for a 30-year fixed home loan?", 4),
    ("I want to apply for a mortgage to buy my first house.", 4),
    ("Can I refinance my student loans with your company?", 4),
    ("I need a statement of my remaining loan balance for tax purposes.", 4),
    # Adding more to ensure variety
    ("My bank statement shows an incorrect balance.", 0),
    ("I want to cancel my credit card.", 1),
    ("The website is slow today.", 2),
    ("Identity theft report.", 3),
    ("Home loan eligibility criteria.", 4)
]

def clean_text(text):
    """Regex based cleaning identical to the Case Study."""
    text = text.lower()
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'[%s]' % re.escape(string.punctuation), '', text)
    text = re.sub(r'\w*\d\w*', '', text)
    return text

# Attempt to import NLP libraries
SKLEARN_AVAILABLE = False
SPACY_AVAILABLE = False
nlp = None

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    SKLEARN_AVAILABLE = True
except ImportError:
    pass

try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
        SPACY_AVAILABLE = True
    except OSError:
        print("[NLP Pipeline] WARNING: spaCy model 'en_core_web_sm' not found. Run 'python -m spacy download en_core_web_sm'")
except ImportError:
    pass

def extract_nouns(text):
    """Extracts only nouns as per the Case Study logic to improve topic accuracy."""
    if not SPACY_AVAILABLE or nlp is None:
        return text # Return cleaned text as fallback
    
    doc = nlp(text)
    return " ".join([token.lemma_ for token in doc if token.pos_ == "NOUN"])

class NLPClassifier:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NLPClassifier, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized: return
        
        self.vectorizer = None
        self.model = None
        self.is_trained = False
        
        if SKLEARN_AVAILABLE:
            try:
                print("[NLP Pipeline] Training demonstration classifier on seed dataset...")
                X = [extract_nouns(clean_text(text)) for text, label in SEED_DATA]
                y = [label for text, label in SEED_DATA]
                
                self.vectorizer = TfidfVectorizer(max_features=1000)
                tfidf_matrix = self.vectorizer.fit_transform(X)
                
                self.model = LogisticRegression(max_iter=1000)
                self.model.fit(tfidf_matrix, y)
                self.is_trained = True
                print("[NLP Pipeline] SUCCESS: Financial routing model ready!")
            except Exception as e:
                print(f"[NLP Pipeline] ERROR: Error training demo model: {e}")
        
        self._initialized = True

    def predict(self, text):
        """Predicts the financial category of the input text."""
        if not self.is_trained:
            # Simple keyword matching fallback (Robust word-boundary search)
            processed = clean_text(text)
            
            # Map of keywords to categories
            mapping = [
                (4, ["loan", "mortgage", "house", "interest", "refinance", "home"]),
                (3, ["stolen", "dispute", "theft", "fraud", "scam", "authorized", "fraudulent"]),
                (1, ["credit", "card", "prepaid", "platinum", "visa", "mastercard"]),
                (0, ["bank", "account", "savings", "atm", "checking", "deposit", "transfer", "statement"])
            ]
            
            for cat_id, keywords in mapping:
                if any(re.search(r'\b' + re.escape(w), processed) for w in keywords):
                    return CATEGORIES[cat_id], 85.0
                    
            return CATEGORIES[2], 70.0
        
        try:
            processed = extract_nouns(clean_text(text))
            X_text = self.vectorizer.transform([processed])
            prediction_id = self.model.predict(X_text)[0]
            probabilities = self.model.predict_proba(X_text)[0]
            confidence = probabilities[prediction_id] * 100
            
            return CATEGORIES.get(prediction_id, "Others"), round(confidence, 2)
        except Exception as e:
            print(f"[NLP Pipeline] Prediction error: {e}")
            return "Others", 0.0

# Singleton instance
classifier = NLPClassifier()
