# Drafted with Claude (Anthropic), reviewed and modified by Aditya Wakase
"""Classify: predict intent and urgency, each with a numeric confidence (A3).

Design choice: NO language model here. We embed the ticket and use a
logistic-regression classifier trained on the 500 labelled development tickets.
Why:
- zero API tokens (the free tier allows ~200K tokens/day; generation needs them)
- fast and deterministic: the same ticket always gets the same answer (A5)
- predict_proba gives a real probability we can check for calibration
"""
import numpy as np
from sklearn.linear_model import LogisticRegression

from src.models import Classification

FALLBACK_INTENT = "unclear_request"


class TicketClassifier:
    def __init__(self, embedder, train_texts, intents, urgencies, answerable, c: float = 10.0):
        self.embedder = embedder
        X = embedder.encode(train_texts)
        self.intent_model = LogisticRegression(C=c, max_iter=3000).fit(X, intents)
        self.urgency_model = LogisticRegression(C=c, max_iter=3000).fit(X, urgencies)
        # Second question, separate from the topic: can the documentation actually
        # solve THIS ticket? Learned from labels.answerable_from_docs.
        self.answerable_model = LogisticRegression(C=c, max_iter=3000).fit(X, answerable)

    def classify(self, text: str) -> Classification:
        """Never raises: returns a defined fallback when it cannot classify."""
        try:
            if not text.strip():
                raise ValueError("empty text")
            x = self.embedder.encode([text])
            ip = self.intent_model.predict_proba(x)[0]
            up = self.urgency_model.predict_proba(x)[0]
            order = np.argsort(-ip)
            best_u = int(np.argmax(up))
            ans_col = list(self.answerable_model.classes_).index(True)
            answerable_prob = float(self.answerable_model.predict_proba(x)[0][ans_col])
            return Classification(
                intent=str(self.intent_model.classes_[order[0]]),
                intent_confidence=round(float(ip[order[0]]), 4),
                urgency=str(self.urgency_model.classes_[best_u]),
                urgency_confidence=round(float(up[best_u]), 4),
                alternatives=[{"value": str(self.intent_model.classes_[i]),
                               "confidence": round(float(ip[i]), 4)} for i in order[1:4]],
                answerable_prob=round(answerable_prob, 4),
            )
        except Exception as exc:  # defined fallback instead of crashing
            return Classification(intent=FALLBACK_INTENT, intent_confidence=0.0,
                                  urgency="medium", urgency_confidence=0.0,
                                  alternatives=[{"value": "error", "confidence": 0.0,
                                                 "note": str(exc)[:200]}])
