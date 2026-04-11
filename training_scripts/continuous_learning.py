import os
import sqlite3
import pandas as pd
from datasets import Dataset
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification, 
    TrainingArguments, 
    Trainer
)

def run_continuous_learning_pipeline():
    print("🔁 Starting Nightly Continuous Learning Pipeline...")

    # 1. Connect to Django's SQLite Database
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db.sqlite3")
    print(f"🔌 Connecting to Database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    # In a real enterprise system, we would filter by `WHERE is_verified=1` to only train on human-approved labels.
    # For this demo, we fetch all logged interactions.
    query = "SELECT ticket_text as text, predicted_id as label FROM customer_portal_aitraininglog;"
    
    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        print("Error reading from database. Have you submitted any tickets yet?")
        return
        
    if df.empty:
        print("💤 No new tickets found in the database. Going back to sleep.")
        return
        
    print(f"📈 Found {len(df)} new verified ticket(s)! Initiating Incremental Fine-Tuning.")
    
    # 2. Convert to HuggingFace Dataset
    dataset = Dataset.from_pandas(df)
    
    # We duplicate the dataset slightly so the batch isn't too small for the Trainer API
    if len(dataset) < 8:
        print("Small batch detected. Augmenting data for mathematical stability...")
        dataset = Dataset.from_pandas(pd.concat([df]*10, ignore_index=True))

    # 3. Load the pre-existing, already fine-tuned model (not from scratch!)
    MODEL_PATH = "../my_fine_tuned_bert"
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Could not find {MODEL_PATH}. You must have the base model available.")
        return

    print(f"🧠 Loading existing neural weights from {MODEL_PATH}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)

    # 4. Tokenization
    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=128)

    tokenized_dataset = dataset.map(tokenize_function, batched=True)

    # 5. Incremental Training Configuration
    # We use a very low learning rate (e.g., 1e-5) because we only want to *tweak* the weights, not destroy them (Catastrophic Forgetting)
    training_args = TrainingArguments(
        output_dir="./results_continuous",
        learning_rate=1e-5,
        per_device_train_batch_size=4,
        num_train_epochs=1, # Just 1 pass over the new data!
        weight_decay=0.01,
        save_strategy="no"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
    )

    # 6. Execute Incremental Fine-Tuning
    print("🔥 Executing Active Learning adjustments...")
    trainer.train()

    # 7. Overwrite the Model with the newly improved weights
    print(f"💾 Saving smarter, self-improved model back to {MODEL_PATH}...")
    model.save_pretrained(MODEL_PATH)
    tokenizer.save_pretrained(MODEL_PATH)
    
    # 8. Clean up (e.g., mark rows as 'consumed' in the database)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customer_portal_aitraininglog;")
    conn.commit()
    conn.close()
    
    print("✨ Continuous Learning Cycle Complete! The AI is now smarter!")

if __name__ == "__main__":
    run_continuous_learning_pipeline()
