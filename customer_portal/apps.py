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
            
        print("Initializing NLP models for Customer Portal...")
        try:
            from transformers import BertTokenizer, BertForSequenceClassification, pipeline
            import torch
            from django.conf import settings
            
            # 1. Load Custom BERT (Ticket Classifier)
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
                print("BERT correctly loaded into memory!")
            else:
                print(f"Watch out: BERT model not found at {MODEL_PATH}")

            # 2. Load Content Moderation (Toxic Comment Model)
            # CustomerPortalConfig.moderation_pipeline = pipeline("text-classification", model="martin-ha/toxic-comment-model")
            # print("Content Moderation loaded!")

            # 3. Load Intent Classification (Zero-Shot)
            # CustomerPortalConfig.intent_pipeline = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
            # print("Intent Classifier loaded!")
            
        except Exception as e:
            print(f"Error loading models (using mock fallbacks): {e}")
