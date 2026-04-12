import streamlit as st
from transformers import BertTokenizer, BertForSequenceClassification
import torch

# --- CONFIGURATION ---
MODEL_PATH = "./my_fine_tuned_bert"

# --- CACHED MODEL LOADING ---
# We use @st.cache_resource so it loads only once and stays in memory
@st.cache_resource
def load_model():
    print("Loading model...")
    tokenizer = BertTokenizer.from_pretrained(MODEL_PATH)
    
    # CRITICAL FIX: low_cpu_mem_usage=False forces it to load REAL weights, not "Meta" ghosts
    model = BertForSequenceClassification.from_pretrained(
        MODEL_PATH,
        low_cpu_mem_usage=False,  
        ignore_mismatched_sizes=True
    )
    
    # Force model to use CPU (Macs hate Meta tensors without this)
    model.to("cpu")
    model.eval()
    return tokenizer, model

try:
    tokenizer, model = load_model()
    model_loaded = True
except Exception as e:
    st.error(f"Error loading model: {e}")
    model_loaded = False

# --- UI LAYOUT ---
st.title("SmartSupport AI")
st.markdown("### Intelligent Customer Ticket Classification")

# Input Area
user_input = st.text_area("Enter Customer Support Ticket:", height=150, placeholder="e.g., I was charged twice for my subscription!")

# Classify Button
if st.button("Classify Ticket"):
    if not user_input.strip():
        st.warning("Please enter some text first.")
    elif not model_loaded:
        st.error("Model failed to load. Check your folder path.")
    else:
        # --- PREDICTION LOGIC ---
        with st.spinner("Analyzing..."):
            # 1. Tokenize Input
            inputs = tokenizer(user_input, return_tensors="pt", padding=True, truncation=True, max_length=128)
            
            # 2. Run Inference (Disable Gradient Calculation for speed)
            with torch.no_grad():
                outputs = model(**inputs)
            
            # 3. Get Prediction
            probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
            prediction_id = torch.argmax(probabilities, dim=-1).item()
            confidence = probabilities[0][prediction_id].item()

            # 4. Map Labels (Must match your Colab training script!)
            # 0 = Bug, 1 = Billing, 2 = Praise
            labels = {
                0: "Bug Report", 
                1: "Billing Issue", 
                2: "Praise"
            }
            
            predicted_label = labels.get(prediction_id, "Unknown")

            # --- DISPLAY RESULTS ---
            st.success(f"Category: **{predicted_label}**")
            st.info(f"Confidence: **{confidence * 100:.2f}%**")

            # Simple logic for routing (The "Real World" part)
            if prediction_id == 0: # Bug
                st.write("Action: Route to Engineering Team (JIRA)")
            elif prediction_id == 1: # Billing
                st.write("Action: Route to Finance Support Queue")
            elif prediction_id == 2: # Praise
                st.write("Action: Send 'Thank You' Auto-Reply")