import os
import re
import joblib
import pandas as pd
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

from django.conf import settings
from django.db import transaction
from .models import ModelPerformance

# Download necessary NLTK data
nltk.download('wordnet', quiet=True)
nltk.download('stopwords', quiet=True)

# =========================================================
# 1. Enhanced Text Preprocessing
# =========================================================
def preprocess_text(text):
    if pd.isna(text):
        return ""

    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))

    # Lowercase and remove URLs/Non-ASCII
    text = text.lower()
    text = re.sub(r"http\S+|www\S+|https\S+", "", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    # Remove numbers and special characters
    text = re.sub(r"\d+", "", text)
    text = re.sub(r"[^a-z\s]", "", text)

    # Tokenize, Remove Stopwords, and Lemmatize
    words = text.split()
    words = [lemmatizer.lemmatize(w) for w in words if w not in stop_words]

    return " ".join(words).strip()

# =========================================================
# 2. Main Training Pipeline
# =========================================================
def train_models_from_dataset(dataset_obj):
    print(f"\n=== Training Models for Dataset: {dataset_obj.name} ===")
    file_path = dataset_obj.file.path
    df = pd.read_csv(file_path)

    # Check columns
    if "message" not in df.columns or "label" not in df.columns:
        raise ValueError("CSV must contain 'message' and 'label' columns")

    # Preprocess text
    df["message"] = df["message"].apply(preprocess_text)
    df = df[df["message"].str.strip() != ""].dropna(subset=["label"])

    # Drop duplicates to avoid train/test leakage
    duplicate_count = df["message"].duplicated().sum()
    if duplicate_count > 0:
        print(f"Dropping {duplicate_count} duplicate messages")
        df = df.drop_duplicates(subset=["message"])

    print(f"Total samples after cleaning: {len(df)}")
    print("Label distribution:\n", df["label"].value_counts())

    if len(df) < 20:
        raise ValueError("Dataset too small. Minimum 20 samples required for reliable training.")

    X = df["message"]
    y = df["label"]

    # Stratified split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")
    print("Test label distribution:\n", y_test.value_counts())

    # TF-IDF Vectorization
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    # Save Vectorizer
    model_dir = os.path.join(settings.MEDIA_ROOT, "trained_models")
    os.makedirs(model_dir, exist_ok=True)
    vec_filename = f"vectorizer_{dataset_obj.id}.pkl"
    joblib.dump(vectorizer, os.path.join(model_dir, vec_filename))
    print(f"Saved vectorizer to {vec_filename}")

    # Define models
    models = {
        "logistic_regression": LogisticRegression(max_iter=1000, class_weight='balanced'),
        "naive_bayes": MultinomialNB()
    }

    for model_name, model_obj in models.items():
        print(f"\n--- Training {model_name} ---")
        model_obj.fit(X_train_vec, y_train)
        preds = model_obj.predict(X_test_vec)

        # Print metrics to terminal
        acc = accuracy_score(y_test, preds)
        prec = precision_score(y_test, preds, average="weighted", zero_division=0)
        rec = recall_score(y_test, preds, average="weighted", zero_division=0)
        f1 = f1_score(y_test, preds, average="weighted", zero_division=0)

        print(f"Accuracy: {acc:.4f}")
        print(f"Precision: {prec:.4f}")
        print(f"Recall: {rec:.4f}")
        print(f"F1-score: {f1:.4f}")
        print("Confusion Matrix:\n", confusion_matrix(y_test, preds))

        # Save to DB and file
        with transaction.atomic():
            save_model_and_metrics(
                model=model_obj,
                model_type=model_name,
                dataset_obj=dataset_obj,
                y_test=y_test,
                predictions=preds,
                model_dir=model_dir
            )

# =========================================================
# 3. Save Model and Metrics
# =========================================================
def save_model_and_metrics(model, model_type, dataset_obj, y_test, predictions, model_dir):
    # Metrics
    metrics = {
        "accuracy": accuracy_score(y_test, predictions),
        "precision": precision_score(y_test, predictions, average="weighted", zero_division=0),
        "recall": recall_score(y_test, predictions, average="weighted", zero_division=0),
        "f1": f1_score(y_test, predictions, average="weighted", zero_division=0)
    }

    # Save metrics to database
    ModelPerformance.objects.create(
        dataset=dataset_obj,
        model_type=model_type,
        accuracy=metrics["accuracy"],
        precision=metrics["precision"],
        recall=metrics["recall"],
        f1_score=metrics["f1"]
    )

    # Save model
    model_filename = f"{model_type}_{dataset_obj.id}.pkl"
    joblib.dump(model, os.path.join(model_dir, model_filename))
    print(f"Saved {model_type} model to {model_filename}")