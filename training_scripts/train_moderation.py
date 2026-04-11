import os
from datasets import load_dataset
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification, 
    TrainingArguments, 
    Trainer
)
import evaluate
import numpy as np

def compute_metrics(eval_pred):
    metric = evaluate.load("accuracy")
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return metric.compute(predictions=predictions, references=labels)

def train_content_moderation(sample_size=None):
    print("🚀 Starting Content Moderation Model Training Pipeline...")
    
    # 1. Load a massive "Big Data" dataset (Toxic Comments)
    # Using 'tweets_hate_speech_detection' as a public dataset example
    print("⬇️ Downloading Dataset...")
    dataset = load_dataset("tweet_eval", "hate")
    
    if sample_size:
        print(f"⚠️ Demo Mode: Only training on {sample_size} samples for speed.")
        train_dataset = dataset["train"].select(range(sample_size))
        eval_dataset = dataset["validation"].select(range(min(sample_size, len(dataset["validation"]))))
    else:
        print("🧠 Big Data Mode: Training on full dataset!")
        train_dataset = dataset["train"]
        eval_dataset = dataset["validation"]

    # 2. Tokenization
    model_name = "distilbert-base-uncased"
    print(f"🔨 Initializing Tokenizer: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=128)

    tokenized_train = train_dataset.map(tokenize_function, batched=True)
    tokenized_eval = eval_dataset.map(tokenize_function, batched=True)

    # 3. Model Initialization
    # Label 0: Safe, Label 1: Hate/Toxic
    print("🤖 Loading DistilBERT architecture...")
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

    # 4. Training Configuration
    training_args = TrainingArguments(
        output_dir="./results_moderation",
        evaluation_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=3 if not sample_size else 1, # Fast epoch for demo
        weight_decay=0.01,
        save_strategy="epoch",
        load_best_model_at_end=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_eval,
        compute_metrics=compute_metrics,
    )

    # 5. Execute Training Loop
    print("🔥 Commencing Neural Network Fine-Tuning...")
    trainer.train()

    # 6. Save the Final Model to Disk
    output_path = "../my_fine_tuned_moderator"
    print(f"💾 Saving custom trained model to {output_path}...")
    model.save_pretrained(output_path)
    tokenizer.save_pretrained(output_path)
    print("✅ Training Complete!")

if __name__ == "__main__":
    # NOTE FOR STUDENT: Remove 'sample_size=100' when you want to train on the FULL Big Data dataset overnight.
    train_content_moderation(sample_size=100)
