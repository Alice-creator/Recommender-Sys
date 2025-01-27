from dataclasses import dataclass
from typing import Dict, List, Set, Tuple
from collections import defaultdict

@dataclass
class Transaction:
    tid: str
    items: List[str]
    quantities: List[int]

@dataclass
class EPMParams:
    min_util: int
    min_per: int
    max_per: int
    min_avg: float
    max_avg: float

class PeriodicHighUtilityMiner:
    def __init__(self, dataset: List[dict], unit_utility: Dict[str, int], epm_params: EPMParams):
        self.dataset = [Transaction(d['Tid'], d['Item'], d['Quantity']) for d in dataset]
        self.unit_utility = unit_utility
        self.epm_params = epm_params
        self.twu_dict = defaultdict(int)
        self.twu_transaction_dict = defaultdict(int)
        self.transaction_dict = defaultdict(list)
        self.ps_dict = defaultdict(list)
        self.eucs_dict = {}
        self.order_list = []

    def _calculate_twu(self) -> None:
        """Calculate Transaction Weighted Utility for each item and transaction."""
        for transaction in self.dataset:
            self.twu_transaction_dict[transaction.tid] = 0
            
            for item, qty in zip(transaction.items, transaction.quantities):
                if item not in self.transaction_dict:
                    self.transaction_dict[item] = []
                self.transaction_dict[item].append(int(transaction.tid[1:]))
                if self.unit_utility[item] > 0:
                    self.twu_transaction_dict[transaction.tid] += qty * self.unit_utility[item]
            
            for item in transaction.items:
                self.twu_dict[item] += self.twu_transaction_dict[transaction.tid]

    def _calculate_periods(self) -> None:
        """Calculate periods for each item."""
        for item, transactions in self.transaction_dict.items():
            self.ps_dict[item] = [transactions[0]]
            for i in range(1, len(transactions)):
                self.ps_dict[item].append(transactions[i] - transactions[i-1])

    def _create_eucs_dict(self, filtered_dataset: List[Transaction]) -> Dict[str, int]:
        """Create EUCS dictionary for item pairs."""
        eucs_dict = defaultdict(int)
        for transaction in filtered_dataset:
            for i in range(len(transaction.items) - 1):
                for j in range(i + 1, len(transaction.items)):
                    item_pair = transaction.items[i] + transaction.items[j]
                    eucs_dict[item_pair] += self.twu_transaction_dict[transaction.tid]
        return eucs_dict

    def preprocess_dataset(self) -> Tuple[List[Transaction], Dict[str, int], List[str]]:
        """Preprocess the dataset and return filtered transactions."""
        self._calculate_twu()
        self._calculate_periods()
        
        filtered_dataset = []
        order_set = set()

        for transaction in self.dataset:
            temp_items = []
            for item, qty in zip(transaction.items, transaction.quantities):
                avg_period = sum(self.ps_dict[item]) / len(self.ps_dict[item])
                if (self.twu_dict[item] >= self.epm_params.min_util and 
                    max(self.ps_dict[item]) <= self.epm_params.max_per and
                    avg_period >= self.epm_params.min_avg):
                    temp_items.append((item, qty, self.unit_utility[item], self.twu_dict[item]))
                    order_set.add((item, self.unit_utility[item], self.twu_dict[item]))
            
            temp_items.sort(key=lambda x: (x[2], x[3]))
            
            if temp_items:
                filtered_dataset.append(Transaction(
                    transaction.tid,
                    [x[0] for x in temp_items],
                    [x[1] for x in temp_items]
                ))

        order_list = sorted(list(order_set), key=lambda x: (x[1], x[2]))
        order_list = [x[0] for x in order_list]
        
        eucs_dict = self._create_eucs_dict(filtered_dataset)
        return filtered_dataset, eucs_dict, order_list

    @staticmethod
    def construct(prefix_list: List[List], x: List[List], y: List[List]) -> List[List]:
        """Construct a new itemset from two existing ones."""
        result = []
        pre_ptr = x_ptr = y_ptr = 0
        
        while x_ptr < len(x) and y_ptr < len(y):
            if x[x_ptr][0] < y[y_ptr][0]:
                x_ptr += 1
            elif x[x_ptr][0] > y[y_ptr][0]:
                y_ptr += 1
            else:
                if prefix_list is not None:
                    while prefix_list[pre_ptr][0] < x[x_ptr][0]:
                        pre_ptr += 1
                    result.append([
                        pre_ptr,
                        x[x_ptr][1] + y[y_ptr][1] - prefix_list[pre_ptr][1],
                        min(x[x_ptr][2], y[y_ptr][2])
                    ])
                    pre_ptr += 1
                else:
                    result.append([
                        x_ptr,
                        x[x_ptr][1] + y[y_ptr][1],
                        min(x[x_ptr][2], y[y_ptr][2])
                    ])
                x_ptr += 1
                y_ptr += 1
        return result

    def check_periodic_conditions(self, itemset_list: List) -> Tuple[bool, float, float, float]:
        """Check periodic conditions for an itemset."""
        if not itemset_list:
            return False, 0, 0, 0
            
        periods = [itemset_list[0][0] + 1]
        for i in range(len(itemset_list) - 1):
            periods.append(itemset_list[i + 1][0] - itemset_list[i][0])
            
        max_period = max(periods)
        min_period = min(periods)
        avg_period = sum(periods) / len(periods)
        
        meets_conditions = (min_period >= self.epm_params.min_per and
                          max_period <= self.epm_params.max_per and
                          avg_period >= self.epm_params.min_avg and
                          avg_period <= self.epm_params.max_avg)
        
        return meets_conditions, max_period, min_period, avg_period

    def mine_patterns(self, utility_lists: Dict[str, List], order_list: List[str]) -> Set[str]:
        """Mine periodic high utility patterns."""
        def search(prefix: str, prefix_list: List, lists: Dict[str, List], current_order: List[str]) -> Set[str]:
            result = set()
            key_lists = [k for k in current_order if k in lists]
            
            for i in key_lists:
                current_list = lists[i]
                
                # Check utility condition
                util_sum = sum(item[1] for item in current_list)
                ru_sum = sum(item[2] for item in current_list)
                
                meets_periodic, max_per, _, avg_per = self.check_periodic_conditions(current_list)
                
                if util_sum >= self.epm_params.min_util and meets_periodic:
                    result.add(i)
                
                if (ru_sum >= self.epm_params.min_util and 
                    max_per <= self.epm_params.max_per and 
                    avg_per <= self.epm_params.max_avg):
                    
                    new_lists = {}
                    new_order = []
                    
                    for j in key_lists[key_lists.index(i) + 1:]:
                        item_pair = i[-1] + j[-1]
                        if item_pair in self.eucs_dict and self.eucs_dict[item_pair] >= self.epm_params.min_util:
                            new_item = item_pair if prefix is None else prefix + item_pair
                            new_lists[new_item] = self.construct(prefix_list, current_list, lists[j])
                            new_order.append(new_item)
                    
                    if new_lists:
                        result.update(search(i, current_list, new_lists, new_order))
            
            return result

        return search(None, None, utility_lists, order_list)

    def run(self) -> Set[str]:
        """Run the complete mining process."""
        filtered_dataset, self.eucs_dict, self.order_list = self.preprocess_dataset()
        
        # Calculate utility lists
        utility_lists = defaultdict(list)
        for transaction in filtered_dataset:
            total = 0
            for item, qty in zip(reversed(transaction.items), reversed(transaction.quantities)):
                util = self.unit_utility[item] * qty
                tid_num = int(transaction.tid[1:])
                utility_lists[item].append([tid_num, util, total])
                if self.unit_utility[item] > 0:
                    total += util
        
        return self.mine_patterns(utility_lists, self.order_list)

# Initialize parameters
epm_params = EPMParams(
    min_util=25,
    min_per=1,
    max_per=6,
    min_avg=1,
    max_avg=5
)

DATASET = [
    {
        'Tid': 'T1',
        'Item': ['a', 'b', 'c', 'd'],
        'Quantity': [5,2,1,2]
    },
    {
        'Tid': 'T2',
        'Item': ['a', 'c', 'd', 'g'],
        'Quantity': [1,1,1,3]
    },
    {
        'Tid': 'T3',
        'Item': ['a', 'c', 'f'],
        'Quantity': [1,1,1]
    },
    {
        'Tid': 'T4',
        'Item': ['a', 'f', 'g'],
        'Quantity': [1,4,2]
    },
    {
        'Tid': 'T5',
        'Item': ['a', 'g'],
        'Quantity': [1,2]
    },
    {
        'Tid': 'T6',
        'Item': ['b', 'c', 'd', 'e'],
        'Quantity': [3,2,3,1]
    },
    {
        'Tid': 'T7',
        'Item': ['c', 'e'],
        'Quantity': [6,4]
    },
    {
        'Tid': 'T8',
        'Item': ['e', 'f'],
        'Quantity': [1,3]
    }
]
UNIT_UTILITY = {
    'a': 3,
    'b': 6,
    'c': -3,
    'd': 12,
    'e': -5,
    'f': -2,
    'g': -1
}

# Create miner instance
miner = PeriodicHighUtilityMiner(DATASET, UNIT_UTILITY, epm_params)

# Run mining process
result = miner.run()

print(result)