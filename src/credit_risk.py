import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
from imblearn.over_sampling import SMOTE
import joblib
import shap
import matplotlib.pyplot as plt


df = pd.read_csv('data/credit_risk.csv', index_col=0)
# print("Shape: ", df.shape)
# print(df.head())


# Preprocessing
df.drop(columns=['unnamed: 0'], inplace=True, errors='ignore')

df['MonthlyIncome'] = df['MonthlyIncome'].fillna(df['MonthlyIncome'].median())
df['NumberOfDependents'] = df['NumberOfDependents'].fillna(0)

print("Missing values: ", df.isnull().sum())

# Features and target
x = df.drop('SeriousDlqin2yrs', axis=1)
y = df['SeriousDlqin2yrs']

print("Deafaul: ", y.mean())


# Train-test split
x_train , x_test, y_train, y_test = train_test_split(x,y,test_size=0.2, random_state=42, stratify=y)

# Apply SMOTE to handle class imbalance
smote = SMOTE(random_state=42, k_neighbors=5)
x_train_balanced, y_train_balanced = smote.fit_resample(x_train, y_train)

#showing before and after balance
# print(f"Original training set class distribution:")
# print(f"  Class 0: {(y_train == 0).sum()}")
# print(f"  Class 1: {(y_train == 1).sum()}")
# print(f"\nBalanced training set class distribution:")
# print(f"  Class 0: {(y_train_balanced == 0).sum()}")
# print(f"  Class 1: {(y_train_balanced == 1).sum()}")

#training with balanced data
lr = LogisticRegression(max_iter=1000)
lr.fit(x_train_balanced, y_train_balanced)
print("1st done")

rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(x_train_balanced, y_train_balanced)
print("2nd done")

xgb = XGBClassifier(n_estimators=100, random_state=42, use_label_encoder=False, eval_metric='logloss')
xgb.fit(x_train_balanced, y_train_balanced)
print("3rd done")


#model evaluation
for name,model in [("Logistic Regression", lr),("Random forest", rf), ("XGBoost", xgb)]:
    preds = model.predict(x_test)
    auc = roc_auc_score(y_test, model.predict_proba(x_test)[:, 1])
    print(f"\n{'='*40}")
    print(f" {name}")
    print(f"{'='*40}")
    print(classification_report(y_test, preds))
    print(f"ROC-AUC: {auc:.4f}")


#saving best model in pickel file
joblib.dump(xgb, 'models/credit_risk_model.pkl')
#show that it saves
print("Model saved as 'models/credit_risk_model.pkl'")


#adding SHAP explainability
explainer = shap.TreeExplainer(xgb)
shap_values = explainer.shap_values(x_test[:100])

shap.summary_plot(shap_values, x_test[:100], show=False)
plt.savefig('notebooks/nootbook1/figures/credit_risk_shap_summary.png', bbox_inches='tight')
print("SHAP summary plot saved as 'notebooks/notebooks1/figures/credit_risk_shap_summary.png'")