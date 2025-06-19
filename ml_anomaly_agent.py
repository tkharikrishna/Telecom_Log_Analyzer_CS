from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List

class MLAnomalyAgent:
    def __init__(self, contamination=0.40):
        self.contamination = contamination

    def detect(self, logs: str) -> List[str]:
        lines = logs.splitlines()
        if len(lines) < 100:
            return []

        vectorizer = TfidfVectorizer()
        X = vectorizer.fit_transform(lines)
        model = IsolationForest(n_estimators=300, contamination=self.contamination, random_state=42)
        preds = model.fit_predict(X.toarray())

        anomalies = [lines[i] for i in range(len(lines)) if preds[i] == -1]
        return anomalies
