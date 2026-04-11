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

def train_intent_classifier(sample_size=None):
    print("🚀 Starting Intent Classification Model Training Pipeline...")
    
    # 1. Load a Massive Customer Support Dataset
    # Bitext is a famous customer service intent dataset with thousands of rows
    print("⬇️ Downloading Customer Support Dataset...")
    dataset = load_dataset("bitext/Bitext-customer-support-llm-chatbot-training-dataset")
    
    # The bitext dataset has 'instruction' and 'intent'. We must map string intents to ID integers.
    unique_intents = list(set(dataset['train']['intent']))
    intent2id = {intent: idx for idx, intent in enumerate(unique_intents)}
    id2intent = {idx: intent for intent, idx in intent2id.items()}

    def map_labels(example):
        example['label'] = intent2id[example['intent']]
        return example

    dataset = dataset.map(map_labels)

    # For training validation split (since bitext only has 'train' split initially)
    dataset = dataset['train'].train_test_split(test_size=0.1)

    if sample_size:
        print(f"⚠️ Demo Mode: Only training on {sample_size} samples for speed.")
        train_dataset = dataset["train"].select(range(sample_size))
        eval_dataset = dataset["test"].select(range(min(sample_size, len(dataset["test"]))))
    else:
        print("🧠 Big Data Mode: Training on full dataset!")
        train_dataset = dataset["train"]
        eval_dataset = dataset["test"]

    # 2. Tokenization
    model_name = "distilbert-base-uncased"
    print(f"🔨 Initializing Tokenizer: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    def tokenize_function(examples):
        return tokenizer(examples["instruction"], padding="max_length", truncation=True, max_length=128)

    tokenized_train = train_dataset.map(tokenize_function, batched=True)
    tokenized_eval = eval_dataset.map(tokenize_function, batched=True)

    # 3. Model Initialization
    print(f"🤖 Loading DistilBERT for {len(unique_intents)} unique intents...")
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name, 
        num_labels=len(unique_intents),
        id2label=id2intent,
        label2id=intent2id
    )

    # 4. Training Configuration
    training_args = TrainingArguments(
        output_dir="./results_intent",
        evaluation_strategy="epoch",
        learning_rate=3e-5,
        per_device_train_batch_size=32,
        per_device_eval_batch_size=32,
        num_train_epochs=4 if not sample_size else 1,
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
    print("🔥 Commencing Neural Network Fine-Tuning for Customer Intents...")
    trainer.train()

    # 6. Save the Final Model to Disk
    output_path = "../my_fine_tuned_intent"
    print(f"💾 Saving custom trained model to {output_path}...")
    model.save_pretrained(output_path)
    tokenizer.save_pretrained(output_path)
    print("✅ Training Complete!")

if __name__ == "__main__":
    # NOTE FOR STUDENT: Remove 'sample_size=100' when you want to train on the FULL dataset.
    train_intent_classifier(sample_size=100)
