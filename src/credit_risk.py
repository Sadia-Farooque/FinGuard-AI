import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import joblib
import shap
import matplotlib.pyplot as plt


df = pd.read_csv('data/credit_risk.csv')
print("Shape: ", df.shape)
print(df.head())


# Preprocessing
df.drop(columns=['unnamed: 0'], inplace=True, errors='ignore')

df['MonthlyIncome'] = df['MonthlyIncome'].fillna(df['MonthlyIncome'].median())
df['NumberOfDependents'] = df['NumberOfDependents'].fillna(0)

# print("Missing values: ", df.isnull().sum())

# Features and target
x = df.drop('SeriousDlqin2yrs', axis=1)
y = df['SeriousDlqin2yrs']

# print("Deafaul: ", y.mean())


# Train-test split
x_train , x_text, y_train, y_test = train_test_split(x,y,test_size=0.2, random_state=42, stratify=y)


# #training
# lr = LogisticRegression(max_iter=1000)
# lr.fit(x_train, y_train)
# print("1st done")

# rf = RandomForestClassifier(n_estimators=100, random_state=42)
# rf.fit(x_train, y_train)
# print("2nd done")

# xgb = XGBClassifier(n_estimators=100, random_state=42, use_label_encoder=False, eval_metric='logloss')
# xgb.fit(x_train, y_train)
# print("3rd done")


# for name,model in [("Logistic Regression", lr),("Random forest", rf), ("XGBoost", xgb)]:
#     preds = model.predict(x_text)
#     auc = roc_auc_score(y_test, model.predict_proba(x_text)[:, 1])
#     print(f"\n{'='*40}")
#     print(f" {name}")
#     print(f"{'='*40}")
#     print(classification_report(y_test, preds))
#     print(f"ROC-AUC: {auc:.4f}")