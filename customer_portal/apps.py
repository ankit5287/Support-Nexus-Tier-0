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

        print("[Nexus Quantum] Initializing NLP models for Customer Portal...")

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
                print("[Nexus Quantum] ✅ BERT Ticket Classifier loaded into memory!")
            else:
                print(f"[Nexus Quantum] ⚠️  BERT model not found at {MODEL_PATH}. Using simulation fallback.")
        except ImportError:
            print("[Nexus Quantum] ⚠️  'transformers' or 'torch' not installed. BERT model unavailable.")
        except Exception as e:
            print(f"[Nexus Quantum] ⚠️  Error loading BERT model: {e}")

        # 2. Load Content Moderation (Toxic Comment Model) — disabled to save memory
        # Uncomment to enable real ML moderation:
        # try:
        #     from transformers import pipeline
        #     CustomerPortalConfig.moderation_pipeline = pipeline("text-classification", model="martin-ha/toxic-comment-model")
        #     print("[Nexus Quantum] ✅ Content Moderation model loaded!")
        # except Exception as e:
        #     print(f"[Nexus Quantum] ⚠️  Moderation model error: {e}")

        # 3. Load Intent Classification (Zero-Shot) — disabled to save memory
        # Uncomment to enable real ML intent classification:
        # try:
        #     from transformers import pipeline
        #     CustomerPortalConfig.intent_pipeline = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        #     print("[Nexus Quantum] ✅ Intent Classifier loaded!")
        # except Exception as e:
        #     print(f"[Nexus Quantum] ⚠️  Intent model error: {e}")
