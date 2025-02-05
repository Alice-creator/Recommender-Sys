from collections import defaultdict

# Constants
minU = 0
K = 10
top_k_pattern = []

# Step 1: Calculate minU
for transaction in databaseTable3:
    for quantity, profit in zip(transaction["quantities"], transaction["profits"]):
        minU += quantity * profit if quantity * profit < 0 else 0

# Step 2: Classify items
def classify_items(database):
    positive_items = set()
    negative_items = set()
    hybrid_items = set()

    for transaction in database:
        for item, profit in zip(transaction['items'], transaction['profits']):
            if profit > 0:
                positive_items.add(item)
            elif profit < 0:
                negative_items.add(item)

    hybrid_items = positive_items.intersection(negative_items)
    positive_items -= hybrid_items
    negative_items -= hybrid_items

    return list(positive_items), list(negative_items), list(hybrid_items)

positive_items, negative_items, hybrid_items = classify_items(databaseTable3)

# Step 3: Calculate RTU and RTWU
def calculate_RTU(transaction):
    return sum(profit * quantity for profit, quantity in zip(transaction['profits'], transaction['quantities']) if profit > 0)

def calculate_RTWU(database, items):
    RTWU = defaultdict(int)
    for transaction in database:
        RTU = calculate_RTU(transaction)
        for item in transaction['items']:
            if item in items:
                RTWU[item] += RTU
    return RTWU

RTWU = calculate_RTWU(databaseTable3, positive_items + hybrid_items)

# Step 4: Find Secondary items
def find_Secondary(RTWU, minU):
    return [item for item, value in RTWU.items() if value >= minU]

Secondary = find_Secondary(RTWU, minU)

# Step 5: Sort items
def sort_items(Secondary, negative_items, RTWU):
    positive_secondary = [item for item in Secondary if item in positive_items]
    hybrid_secondary = [item for item in Secondary if item in hybrid_items]
    negative_secondary = [item for item in Secondary if item in negative_items]
    negative_only = [item for item in negative_items if item not in Secondary]

    positive_secondary.sort(key=lambda x: RTWU.get(x, 0))
    hybrid_secondary.sort(key=lambda x: RTWU.get(x, 0))
    negative_secondary.sort(key=lambda x: RTWU.get(x, 0))
    negative_only.sort(key=lambda x: RTWU.get(x, 0))

    return positive_secondary + hybrid_secondary + negative_secondary, negative_only

sorted_secondary, sorted_negative_items = sort_items(Secondary, negative_items, RTWU)

# Step 6: Prune and sort transactions
def prune_and_sort_transactions(database, sorted_secondary, sorted_negative_items):
    combined_order = sorted_secondary + sorted_negative_items
    pruned_database = []

    for transaction in database:
        pruned_items = []
        pruned_quantities = []
        pruned_profits = []

        for item, quantity, profit in zip(transaction['items'], transaction['quantities'], transaction['profits']):
            if item in combined_order:
                pruned_items.append(item)
                pruned_quantities.append(quantity)
                pruned_profits.append(profit)

        if pruned_items:
            sorted_indices = sorted(range(len(pruned_items)), key=lambda x: combined_order.index(pruned_items[x]))
            pruned_database.append({
                'tid': transaction['tid'],
                'items': [pruned_items[i] for i in sorted_indices],
                'quantities': [pruned_quantities[i] for i in sorted_indices],
                'profits': [pruned_profits[i] for i in sorted_indices]
            })

    return pruned_database

pruned_database = prune_and_sort_transactions(databaseTable3, sorted_secondary, sorted_negative_items)

# Step 7: Search for top-k patterns
def search(eta, X, database, primary_items, secondary_items, minU, processing_top_k_pattern):
    for iter, i in enumerate(primary_items):
        beta = X + [i]
        projected_db, u_beta = project_database(beta, database)

        index = 0
        while index < len(processing_top_k_pattern):
            if u_beta > processing_top_k_pattern[index][1]:
                break
            index += 1

        processing_top_k_pattern.insert(index, (beta, u_beta))
        if len(processing_top_k_pattern) > K:
            processing_top_k_pattern = processing_top_k_pattern[:K]
            minU = processing_top_k_pattern[-1][1]

        if u_beta > minU:
            processing_top_k_pattern = search(eta, beta, projected_db, primary_items[iter + 1:], secondary_items[iter + 1:], minU, processing_top_k_pattern)

    return processing_top_k_pattern

# Step 8: Project database
def project_database(itemset, database):
    projected_db = []
    u_beta = 0

    for transaction in database:
        if itemset[-1] in transaction['items']:
            last_index = transaction['items'].index(itemset[-1])
            projected_items = transaction['items'][last_index + 1:]
            projected_profits = transaction['profits'][last_index + 1:]
            projected_quantities = transaction.get('quantities', [1] * len(transaction['items']))[last_index + 1:]

            u_project = transaction['quantities'][last_index] * transaction['profits'][last_index] + transaction.get("u_project", 0)
            u_beta += u_project

            if projected_items:
                projected_db.append({
                    'tid': transaction['tid'],
                    'items': projected_items,
                    'profits': projected_profits,
                    'quantities': projected_quantities,
                    'u_project': u_project
                })

    return projected_db, u_beta

# Step 9: Run the search
final_top_k_pattern = search(sorted_negative_items, [], pruned_database, Primary, sorted_secondary, minU, top_k_pattern)
print("Top-K Patterns:", final_top_k_pattern)