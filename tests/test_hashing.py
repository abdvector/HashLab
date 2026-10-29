import random
import unittest

from experiments import run_experiment
from hashing import DELETED, HashTable, STRATEGIES


class HashTableTests(unittest.TestCase):
    def test_collision_counts_and_layout(self):
        for strategy in STRATEGIES:
            table = HashTable(11, strategy)
            results = [table.operate("Insert", key) for key in (1, 12, 23)]
            self.assertEqual(table.count, 3)
            self.assertEqual(results[0].collisions, 0)
            self.assertEqual(results[1].collisions, 1)
            if strategy == STRATEGIES[0]:
                self.assertEqual(table.snapshot()[1], [1, 12, 23])
                self.assertEqual(results[2].comparisons, 2)
            if strategy == STRATEGIES[1]:
                self.assertEqual(table.snapshot()[1:4], [1, 12, 23])
                self.assertEqual(results[2].probes, 3)
            for key in (1, 12, 23):
                self.assertEqual(table.operate("Search", key).status, "Found")

    def test_deletion_preserves_search_and_duplicate_detection(self):
        for strategy in STRATEGIES:
            table = HashTable(7, strategy)
            for key in (1, 8, 15):
                table.operate("Insert", key)
            self.assertEqual(table.operate("Delete", 1).status, "Deleted")
            self.assertEqual(table.operate("Search", 15).status, "Found")
            self.assertEqual(table.operate("Insert", 15).status, "Already present")
            self.assertEqual(table.count, 2)
            self.assertEqual(table.operate("Delete", 8).status, "Deleted")
            self.assertEqual(table.operate("Delete", 15).status, "Deleted")
            self.assertEqual(table.count, 0)

    def test_full_table_and_tombstone_reuse(self):
        for strategy in STRATEGIES[1:]:
            table = HashTable(7, strategy)
            for key in range(7):
                self.assertEqual(table.operate("Insert", key).status, "Inserted")
            full = table.operate("Insert", 99)
            self.assertEqual(full.status, "Table full")
            self.assertEqual(full.probes, 7)
            self.assertEqual(table.operate("Search", 99).probes, 7)
            table.operate("Delete", 2)
            self.assertIn(DELETED, table.snapshot())
            self.assertEqual(table.operate("Insert", 99).status, "Inserted")
            self.assertEqual(table.count, 7)
            self.assertEqual(table.operate("Search", 99).status, "Found")

    def test_double_hash_covers_every_slot(self):
        for size in (2, 7, 11, 31, 101):
            table = HashTable(size, STRATEGIES[2])
            for key in range(-100, 100):
                self.assertEqual(len(set(table.indices(key))), size)

    def test_random_operations_against_reference_set(self):
        for strategy in STRATEGIES:
            rng, reference = random.Random(71), set()
            table = HashTable(11, strategy)
            for _ in range(800):
                key, operation = rng.randrange(-20, 21), rng.choice(["Insert", "Search", "Delete"])
                result = table.operate(operation, key)
                if operation == "Insert":
                    if key in reference:
                        expected = "Already present"
                    elif len(reference) == 11 and strategy != STRATEGIES[0]:
                        expected = "Table full"
                    else:
                        expected = "Inserted"
                        reference.add(key)
                elif operation == "Delete":
                    expected = "Deleted" if key in reference else "Not found"
                    reference.discard(key)
                else:
                    expected = "Found" if key in reference else "Not found"
                self.assertEqual(result.status, expected, (strategy, operation, key))
                self.assertEqual(table.count, len(reference))

    def test_experiments_are_reproducible_and_comparable(self):
        for distribution in ("Random keys", "Same initial bucket"):
            first = run_experiment(31, distribution, 42, 1.0)
            self.assertEqual(first, run_experiment(31, distribution, 42, 1.0))
            rows, summaries, keys = first
            self.assertEqual(len(set(keys)), 31)
            self.assertEqual(len(summaries), 3)
            self.assertTrue(all(r["Keys"] == 31 for r in summaries))
            self.assertTrue(all(r["Load factor"] == 1 for r in summaries))
            if distribution == "Same initial bucket":
                self.assertEqual(summaries[0]["Insertion collisions"], 31 * 30 // 2)
                self.assertEqual(summaries[1]["Insertion collisions"], 31 * 30 // 2)
                self.assertEqual(summaries[1]["Unsuccessful search comparisons"], 31)

    def test_invalid_configuration(self):
        with self.assertRaises(ValueError):
            HashTable(10)
        with self.assertRaises(ValueError):
            HashTable(11, "invalid")



if __name__ == "__main__":
    unittest.main()
