import joblib
import pandas as pd
import sys
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

df = pd.read_csv("synthetic_dataset.csv")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
import config as c  # noqa: E402

# INSUFFICIENT_DATA ya se resuelve con una comprobación simple en labeler() antes
# de llegar aquí -- no aporta nada al modelo entrenar sobre filas con NaN.
df = df[df["label"] != "INSUFFICIENT_DATA"]
df["moisture_vs_baseline"] = df["soil_moisture_(%)"] - df["soil_moisture_baseline"]


X = df[c.FEATURES]
y = df["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = RandomForestClassifier(
    n_estimators=200,
    class_weight="balanced",  # compensa que HYDRIC_STRESS_ALERT sea ~1% frente a OK ~25%
    random_state=42,
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))
print(confusion_matrix(y_test, y_pred, labels=model.classes_))

importances = pd.Series(model.feature_importances_, index=c.FEATURES).sort_values(ascending=False)
print("\nFeature importances:")
print(importances)

joblib.dump(model, c.decision_model_name)
print(f"\nGuardado en decision_model_training/{c.decision_model_name}")