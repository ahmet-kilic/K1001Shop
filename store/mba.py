
import pandas as pd
from mlxtend.frequent_patterns import apriori
from mlxtend.frequent_patterns import association_rules
from mlxtend.preprocessing import TransactionEncoder
import random as rand
from .models import Product

def get_associated(product):

    dataset = []

    products = Product.objects.values_list('id', flat=True)
    print(product)

    # Create random training data
    for i in range (0,40):
        l_size = rand.randint(10,30)
        order = []
        for j in range(0, l_size):
            order.append(rand.choice(products))
        dataset.append(order)


    # Encode data to use apriori algorithm
    te = TransactionEncoder()
    te_ary = te.fit(dataset).transform(dataset)
    df = pd.DataFrame(te_ary, columns=te.columns_)

    # Apply apriori algorithm and find frequent item sets
    rule_sets = apriori(df, min_support=0.1, use_colnames=True)
    # Apply rules and find associations.
    rules = association_rules(rule_sets, metric="lift", min_threshold=1)
    # Filtering results..
    rules = rules[ (rules['lift'] >= 0.9) & (rules['antecedents'] == frozenset({product}))]
    print(rules)

    rules = rules.sort_values(by=['support'], ascending=False)
    rules = rules[ rules['consequents'].apply(lambda x: len(x) == 1 ) ]['consequents'][0:4]

    print(rules)

    recommended = []

    for i in rules:
        value = list(i)[0]
        recommended.append(Product.objects.get(id=value))

    print(recommended)

    return recommended

