from django.apps import AppConfig
import os

class CustomerPortalConfig(AppConfig):
    name = 'customer_portal'

    tokenizer = None
    model = None
    moderation_pipeline = None
    intent_pipeline = None
    
    # Semantic Squad Contexts (for intent-based routing)
    SQUAD_CONTEXTS = {
        'Systems Engine': 'Infrastructure, backend servers, database performance, APIs, and low-level system integrity.',
        'Creative Architecture': 'Visual design, user interface components, CSS animations, responsive layouts, and frontend aesthetics.',
        'Neural Insights': 'Data analytics, predictive accuracy, machine learning logic, operational triage, and diagnostic integrity.'
    }
    
    def ready(self):
        # Prevent double-loading in Django's runserver reloading
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
                print("[Logic Stream] WARNING: Triage engine model not found. Using operational fallback.")
        except ImportError:
            print("[Logic Stream] WARNING: Essential processing libraries not installed. Triage engine unavailable.")
        except Exception as e:
            print(f"[Logic Stream] WARNING: Error initializing triage engine: {e}")

        # 2. Load Content Analytics (Sentiment/Tone Analysis)
        try:
            from transformers import pipeline
            CustomerPortalConfig.moderation_pipeline = pipeline("text-classification", model="cardiffnlp/twitter-roberta-base-sentiment-latest")
            print("[Logic Stream] ✅ Analytic Tone Analysis Online!")
        except Exception as e:
            print(f"[Logic Stream] WARNING: Moderation model error: {e}")

        # 3. Load Intent Classification (Zero-Shot) — The Logic Fallback
        try:
            from transformers import pipeline
            # Using a high-performance model with safetensors support
            CustomerPortalConfig.intent_pipeline = pipeline(
                "zero-shot-classification", 
                model="facebook/bart-large-mnli"
            )
            print("[Logic Stream] ✅ Zero-Shot Triage Online!")
        except Exception as e:
            print(f"[Logic Stream] WARNING: Zero-Shot initialization error: {e}")
