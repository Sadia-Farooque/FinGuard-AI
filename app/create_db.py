"""
FinGuard AI — MongoDB Database Seeder
Run this ONCE to create the finguard database and insert sample customers.

Usage:
    python create_db.py
"""

import pymongo

# ── Connect ──────────────────────────────────
client     = pymongo.MongoClient("mongodb://localhost:27017/")
db         = client["finguard"]
collection = db["customers"]

# ── Drop existing so we start clean ──────────
collection.drop()

# ── Sample customer records ───────────────────
# Fields match exactly what the app inputs require
customers = [
    {
        "customer_id":   "CUST001",
        "name":          "Ahmed Khan",
        "age":           34,
        "income":        5200.0,
        "debt_ratio":    0.74,
        "loan_amount":   18500.0,
        "credit_score":  620.0,
        "tenure":        2,
        "num_products":  1,
        "balance":       45000.0,
        "gender":        "Male",
        "geography":     "France",
        "active_member": "Yes"
    },
    {
        "customer_id":   "CUST002",
        "name":          "Sara Ali",
        "age":           45,
        "income":        8500.0,
        "debt_ratio":    0.32,
        "loan_amount":   12000.0,
        "credit_score":  780.0,
        "tenure":        8,
        "num_products":  3,
        "balance":       92000.0,
        "gender":        "Female",
        "geography":     "Germany",
        "active_member": "Yes"
    },
    {
        "customer_id":   "CUST003",
        "name":          "James Wilson",
        "age":           28,
        "income":        3100.0,
        "debt_ratio":    0.88,
        "loan_amount":   25000.0,
        "credit_score":  520.0,
        "tenure":        1,
        "num_products":  1,
        "balance":       8000.0,
        "gender":        "Male",
        "geography":     "Spain",
        "active_member": "No"
    },
    {
        "customer_id":   "CUST004",
        "name":          "Maria Garcia",
        "age":           52,
        "income":        11000.0,
        "debt_ratio":    0.21,
        "loan_amount":   5000.0,
        "credit_score":  820.0,
        "tenure":        15,
        "num_products":  4,
        "balance":       150000.0,
        "gender":        "Female",
        "geography":     "France",
        "active_member": "Yes"
    },
    {
        "customer_id":   "CUST005",
        "name":          "Ali Hassan",
        "age":           38,
        "income":        4700.0,
        "debt_ratio":    0.61,
        "loan_amount":   22000.0,
        "credit_score":  640.0,
        "tenure":        4,
        "num_products":  2,
        "balance":       31000.0,
        "gender":        "Male",
        "geography":     "Germany",
        "active_member": "No"
    },
    {
        "customer_id":   "CUST006",
        "name":          "Emily Chen",
        "age":           41,
        "income":        9200.0,
        "debt_ratio":    0.44,
        "loan_amount":   15000.0,
        "credit_score":  710.0,
        "tenure":        6,
        "num_products":  2,
        "balance":       67000.0,
        "gender":        "Female",
        "geography":     "Spain",
        "active_member": "Yes"
    },
    {
        "customer_id":   "CUST007",
        "name":          "Omar Sheikh",
        "age":           23,
        "income":        2800.0,
        "debt_ratio":    0.91,
        "loan_amount":   30000.0,
        "credit_score":  480.0,
        "tenure":        0,
        "num_products":  1,
        "balance":       3000.0,
        "gender":        "Male",
        "geography":     "France",
        "active_member": "No"
    },
    {
        "customer_id":   "CUST008",
        "name":          "Fatima Malik",
        "age":           60,
        "income":        14000.0,
        "debt_ratio":    0.15,
        "loan_amount":   8000.0,
        "credit_score":  860.0,
        "tenure":        20,
        "num_products":  4,
        "balance":       210000.0,
        "gender":        "Female",
        "geography":     "Germany",
        "active_member": "Yes"
    },
    {
        "customer_id":   "CUST009",
        "name":          "David Brown",
        "age":           35,
        "income":        5900.0,
        "debt_ratio":    0.55,
        "loan_amount":   19000.0,
        "credit_score":  670.0,
        "tenure":        3,
        "num_products":  1,
        "balance":       28000.0,
        "gender":        "Male",
        "geography":     "Spain",
        "active_member": "Yes"
    },
    {
        "customer_id":   "CUST010",
        "name":          "Ayesha Qureshi",
        "age":           29,
        "income":        3800.0,
        "debt_ratio":    0.78,
        "loan_amount":   21000.0,
        "credit_score":  590.0,
        "tenure":        2,
        "num_products":  1,
        "balance":       12000.0,
        "gender":        "Female",
        "geography":     "France",
        "active_member": "No"
    },
]

# ── Insert ────────────────────────────────────
result = collection.insert_many(customers)
print(f"✅ Inserted {len(result.inserted_ids)} customers into finguard.customers")

# ── Verify ────────────────────────────────────
print("\nRecords in database:")
for c in collection.find({}, {"_id": 0, "customer_id": 1, "name": 1, "age": 1}):
    print(f"  {c['customer_id']} — {c['name']} (Age {c['age']})")

print("\n✅ Database ready. You can now use LOAD FROM DATABASE in the app.")
client.close()
