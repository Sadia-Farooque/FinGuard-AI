import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import classification_report, roc_auc_score
import joblib
import shap
import matplotlib.pyplot as plt
from imblearn.over_sampling import SMOTE

#data loading
df = pd.read_csv('data/Churn_modelling.csv', index_col = 0)
# print("Shape : ",df.shape())
# print(df.head())

#data preprocessing
df.drop(columns=['RowNumber', 'CustomerId', 'Surname'], inplace=True, errors='ignore')

#lable encoding
df['Gender'] = df['Gender'].map({'Male': 1, 'Female':0})

df = pd.get_dummies(df, columns=['Geography'], drop_first=True)


#Feature and target setting
x =df.drop('Exited', axis=1)
y = df['Exited']
# print("Churn rate: ", y.mean())

#train test split
x_train, x_test, y_train, y_test = train_test_split(x,y, test_size=0.2, random_state=42, stratify=y)

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


lr = LogisticRegression(max_iter=2000, solver='saga')
lr.fit(x_train_balanced, y_train_balanced)
print("1st done")

rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(x_train_balanced, y_train_balanced)
print("2nd done")

gb = GradientBoostingClassifier(n_estimators=100, random_state=42)
gb.fit(x_train_balanced, y_train_balanced)
print("3rd done")


#evaluation
for name, model in [("Logistic Regression",lr), ("Random Forest", rf), ("Gradient Boosting", gb)]:
    preds = model.predict(x_test)
    auc = roc_auc_score(y_test, model.predict_proba(x_test)[:,1])
    print(classification_report(y_test, preds))
    print(f"ROC AUC Score: {auc:.4f}\n")


#saving the best model
joblib.dump(gb, 'models/churn_model.pkl')


# SHAP Explainability
explainer = shap.TreeExplainer(gb)
shap_values = explainer.shap_values(x_test)

shap.summary_plot(shap_values, x_test, plot_type="bar")
plt.savefig('notebooks/nootbook1/figures/shap_summary_plot.png', bbox_inches='tight')
