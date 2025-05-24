# svm_extractor.py

import os
import joblib
import pandas as pd
import re
from sklearn.svm import SVC
from sklearn.utils import shuffle
from sklearn.feature_extraction.text import CountVectorizer

MODEL_FILE = "timestamp_svm_model.pkl"

def train_model():
    positive = ['2023-05-14', '12:34:56', '2023/08/11', '11:59:59', '2000-01-01 00:00:00']
    negative = ['ERROR', 'INFO', 'login', 'user', 'failed', 'connected']

    labels = [1]*len(positive) + [0]*len(negative)
    samples = positive + negative

    vectorizer = CountVectorizer(analyzer='char_wb', ngram_range=(2, 4))
    X = vectorizer.fit_transform(samples)
    X, labels = shuffle(X, labels, random_state=42)

    model = SVC(probability=True)
    model.fit(X, labels)
    joblib.dump((model, vectorizer), MODEL_FILE)
    return model, vectorizer

def load_model():
    if os.path.exists(MODEL_FILE):
        return joblib.load(MODEL_FILE)
    return train_model()

def extract_tokens(lines):
    tokens = set()
    for line in lines:
        tokens.update(line.strip().split())
    return list(tokens)

def detect_timestamps(log_lines):
    model, vectorizer = load_model()
    tokens = extract_tokens(log_lines)
    X_tokens = vectorizer.transform(tokens)
    probs = model.predict_proba(X_tokens)[:, 1]

    results = pd.DataFrame({'token': tokens, 'probability': probs})
    results = results[results['probability'] > 0.99]
    results = results.sort_values(by='probability', ascending=False)
    return results
