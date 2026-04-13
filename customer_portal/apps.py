from django.apps import AppConfig
import os

class CustomerPortalConfig(AppConfig):
    name = 'customer_portal'

    tokenizer = None
    model = None
    moderation_pipeline = None
    intent_pipeline = None
    remote_mode = False 

    # Semantic Squad Contexts
    SQUAD_CONTEXTS = {
        'Systems Engine': 'Infrastructure, backend servers, database performance, APIs, and low-level system integrity.',
        'Creative Architecture': 'Visual design, user interface components, CSS animations, responsive layouts, and frontend aesthetics.',
        'Neural Insights': 'Data analytics, predictive accuracy, machine learning logic, operational triage, and diagnostic integrity.'
    }
    
    def ready(self):
        if os.environ.get('RUN_MAIN', None) != 'true':
            return

        print("[Logic Stream] Initializing Case Triage Systems...")

        # 1. Load Custom BERT (Ticket Classifier)
        try:
            from transformers import BertTokenizer, BertForSequenceClassification
            import torch
            from django.conf import settings

            MODEL_PATH = os.path.join(settings.BASE_DIR, "my_fine_tuned_bert")
            if os.path.exists(MODEL_PATH):
                CustomerPortalConfig.tokenizer = BertTokenizer.from_pretrained(MODEL_PATH)
                CustomerPortalConfig.model = BertForSequenceClassification.from_pretrained(
                    MODEL_PATH,
                    low_cpu_mem_usage=False,
                    ignore_mismatched_sizes=True,
                    use_safetensors=True
                )
                CustomerPortalConfig.model.to("cpu")
                CustomerPortalConfig.model.eval()
                print("[Logic Stream] ✅ Intelligent Triage Engine Online!")
            else:
                print("[Logic Stream] WARNING: Triage engine model not found.")
        except Exception as e:
            print(f"[Logic Stream] ERROR: Failed to initialize triage engine: {e}")

        # 2. Load Content Analytics (Sentiment)
        try:
            from transformers import pipeline
            CustomerPortalConfig.moderation_pipeline = pipeline("text-classification", model="cardiffnlp/twitter-roberta-base-sentiment-latest")
            print("[Logic Stream] ✅ Analytic Tone Analysis Online!")
        except Exception as e:
            print(f"[Logic Stream] ERROR: Moderation model error: {e}")

        # 3. Load Intent Classification (Zero-Shot)
        try:
            from transformers import pipeline
            CustomerPortalConfig.intent_pipeline = pipeline(
                "zero-shot-classification", 
                model="facebook/bart-large-mnli"
            )
            print("[Logic Stream] ✅ Local Zero-Shot Triage Online!")
        except Exception as e:
            print(f"[Logic Stream] ERROR: Intent pipeline failure: {e}")
            CustomerPortalConfig.remote_mode = True
            print("[Logic Stream] 🌐 Adaptive Fallback: Remote Intelligence Activated.")
