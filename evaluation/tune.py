# Drafted with Claude (Anthropic), reviewed and modified by Aditya Wakase
"""Measure the data before choosing thresholds. Uses DEVELOPMENT tickets only.

    python -m evaluation.tune

Prints three tables you use to make (and defend) the DECISIONS in .env:
  1. Chunking: "whole" vs "section", retrieval hit rate at several relevance thresholds
  2. Classification measured honestly with 5-fold cross-validation. Tickets with
     the same body text are kept in the same fold, because the data contains
     many near-copies and letting a copy appear on both sides inflates accuracy.
  3. Confidence threshold: for each threshold, how many tickets would be
     auto-eligible and how accurate the topic is on those
"""
import json
import re

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold

from src.config import NEVER_AUTO_INTENTS, get_settings
from src.embeddings import get_embedder
from src.ingest import normalise
from src.retrieve import build_passages


def main():
    s = get_settings()
    train = [normalise(t) for t in json.loads(s.train_path.read_text(encoding="utf-8"))]
    texts = [t.text for t in train]
    intents = np.array([t.labels["intent"] for t in train])
    answerable = np.array([bool(t.labels.get("answerable_from_docs")) for t in train])
    expected = [set(t.labels.get("expected_doc_ids", [])) for t in train]

    corpus = texts + [p["text"] for strat in ("whole", "section") for p in build_passages(s.docs_path, strat)]
    emb = get_embedder(s.embedding_backend, s.embedding_model, corpus)
    X = emb.encode(texts)
    print(f"Embedding backend: {emb.name}   tickets: {len(texts)}\n")

    # ---------------------------------------------------------- 1. chunking
    print("1. RETRIEVAL: hit rate on answerable tickets / wrongly-retrieved on unanswerable")
    print(f"   (top_k={s.retrieval_top_k}; 'hit' = an expected document appears above the threshold)")
    thresholds = [0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55]
    for strat in ("whole", "section"):
        passages = build_passages(s.docs_path, strat)
        P = emb.encode([p["text"] for p in passages])
        sims = X @ P.T
        top = np.argsort(-sims, axis=1)[:, :s.retrieval_top_k]
        print(f"\n   chunking='{strat}' ({len(passages)} passages)")
        print("   threshold | hit rate (answerable) | anything returned (unanswerable)")
        for th in thresholds:
            hit, false_ret = [], []
            for i in range(len(texts)):
                kept = [passages[j]["doc_id"] for j in top[i] if sims[i, j] >= th]
                if answerable[i]:
                    hit.append(bool(set(kept) & expected[i]))
                else:
                    false_ret.append(bool(kept))
            print(f"   {th:>9.2f} | {100*np.mean(hit):>21.1f}% | {100*np.mean(false_ret):>31.1f}%")

    # ------------------------------------------------- 2. honest classifier
    groups = [re.sub(r"\W+", " ", t.original_body.lower()).strip()[:60] for t in train]
    group_ids = {g: i for i, g in enumerate(sorted(set(groups)))}
    probs = np.zeros(len(texts))
    preds = np.empty(len(texts), dtype=object)
    for tr, te in GroupKFold(n_splits=5).split(X, intents, [group_ids[g] for g in groups]):
        model = LogisticRegression(C=10.0, max_iter=3000).fit(X[tr], intents[tr])
        p = model.predict_proba(X[te])
        preds[te] = model.classes_[p.argmax(1)]
        probs[te] = p.max(1)
    correct = preds == intents
    print(f"\n2. CLASSIFICATION (5-fold, near-copies kept together): intent accuracy {100*correct.mean():.1f}%")
    print("   calibration: band | n | stated confidence | observed accuracy")
    for lo in np.arange(0, 1.0, 0.2):
        m = (probs >= lo) & (probs < lo + 0.2 + (1e-9 if lo >= 0.8 else 0))
        if m.sum():
            print(f"   {lo:.1f}-{lo+0.2:.1f} | {m.sum():>3} | {100*probs[m].mean():>6.1f}% | {100*correct[m].mean():>6.1f}%")

    # --------------------------------------------- 3. confidence threshold
    eligible = np.array([i not in NEVER_AUTO_INTENTS for i in preds])
    print("\n3. CONFIDENCE THRESHOLD (tickets not on the never-automate list)")
    print("   threshold | share of all tickets passing | topic accuracy on those")
    for th in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
        m = eligible & (probs >= th)
        acc = 100 * correct[m].mean() if m.sum() else float("nan")
        print(f"   {th:>9.1f} | {100*m.mean():>27.1f}% | {acc:>22.1f}%")
    print("\nPick: the chunking + relevance threshold with a high hit rate AND low wrong-retrieval,")
    print("and the lowest confidence threshold whose topic accuracy is at least 85% (Brief target).")


if __name__ == "__main__":
    main()
