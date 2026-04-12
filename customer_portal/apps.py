from django.apps import AppConfig
import os

class CustomerPortalConfig(AppConfig):
    name = 'customer_portal'

    tokenizer = None
    model = None
    moderation_pipeline = None
    intent_pipeline = None
    
    def ready(self):
        # Prevent double-loading in Django's runserver reloading
        if os.environ.get('RUN_MAIN', None) != 'true':
            return

        print("[Nexus Quantum] Initializing Case Triage Systems...")

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
                    ignore_mismatched_sizes=True
                )
                CustomerPortalConfig.model.to("cpu")
                CustomerPortalConfig.model.eval()
                print("[Nexus Quantum] ✅ Intelligent Triage Engine Online!")
            else:
                print("[Nexus Quantum] WARNING: Triage engine model not found. Using operational fallback.")
        except ImportError:
            print("[Nexus Quantum] WARNING: Essential processing libraries not installed. Triage engine unavailable.")
        except Exception as e:
            print(f"[Nexus Quantum] WARNING: Error initializing triage engine: {e}")

        # 2. Load Content Analytics (Sentiment/Tone Analysis)
        # try:
        #     from transformers import pipeline
        #     CustomerPortalConfig.moderation_pipeline = pipeline("text-classification", model="martin-ha/toxic-comment-model")
        #     print("[Nexus Quantum] ✅ Analytic Tone Analysis Online!")
        # except Exception as e:
        #     print(f"[Nexus Quantum] WARNING: Moderation model error: {e}")

        # 3. Load Intent Classification (Zero-Shot) — disabled to save memory
        # Uncomment to enable real ML intent classification:
        # try:
        #     from transformers import pipeline
        #     CustomerPortalConfig.intent_pipeline = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        #     print("[Nexus Quantum] ✅ Intent Classifier loaded!")
        # except Exception as e:
        #     print(f"[Nexus Quantum] WARNING: Intent model error: {e}")
