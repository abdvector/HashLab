"""Hand-written hash tables. No Python dict is used to store table entries."""

from dataclasses import dataclass, field
from typing import Optional

STRATEGIES = ("Separate chaining", "Linear probing", "Double hashing")
EMPTY = None
DELETED = "DELETED"


def is_prime(number: int) -> bool:
    return number >= 2 and all(number % d for d in range(2, int(number**0.5) + 1))


@dataclass
class Node:
    key: int
    next: Optional["Node"] = None


@dataclass
class Step:
    index: int
    message: str
    kind: str = "visit"


@dataclass
class Result:
    operation: str
    key: int
    status: str = ""
    probes: int = 0
    comparisons: int = 0
    collisions: int = 0
    steps: list[Step] = field(default_factory=list)


class HashTable:
    """Integer keys stored in the custom table.

    A collision is one unequal live key encountered during insertion. A probe
    is a bucket/slot visit. A comparison is an equality check against a live key.
    """

    def __init__(self, size: int = 11, strategy: str = STRATEGIES[0]):
        if not is_prime(size):
            raise ValueError("Use a prime table size (at least 2).")
        if strategy not in STRATEGIES:
            raise ValueError("Unknown collision-resolution strategy.")
        self.size, self.strategy, self.count = size, strategy, 0
        self.slots = [EMPTY] * size

    def snapshot(self) -> list[list[int] | int | str | None]:
        if self.strategy != STRATEGIES[0]:
            return self.slots.copy()
        buckets = []
        for head in self.slots:
            keys = []
            while head is not None:
                keys.append(head.key)
                head = head.next
            buckets.append(keys)
        return buckets

    def indices(self, key: int):
        step = 1 if self.strategy != STRATEGIES[2] else 1 + key % (self.size - 1)
        for attempt in range(self.size):
            yield (key % self.size + attempt * step) % self.size

    def operate(self, operation: str, key: int, trace: bool = True) -> Result:
        if operation not in ("Insert", "Search", "Delete"):
            raise ValueError("Unknown operation.")
        if not isinstance(key, int):
            raise TypeError("Keys must be integers.")
        result = Result(operation, key)

        def log(index, message, kind="visit"):
            if trace:
                result.steps.append(Step(index, message, kind))

        if self.strategy == STRATEGIES[0]:
            index = key % self.size
            result.probes = 1
            node, previous = self.slots[index], None
            log(index, f"h({key}) = {key} mod {self.size} = {index}. Visit bucket {index}.")
            while node is not None:
                result.comparisons += 1
                if node.key == key:
                    if operation == "Delete":
                        if previous is None:
                            self.slots[index] = node.next
                        else:
                            previous.next = node.next
                        self.count -= 1
                        result.status = "Deleted"
                    else:
                        result.status = "Already present" if operation == "Insert" else "Found"
                    log(index, f"Compare with {node.key}: match. {result.status}.", "success")
                    return result
                if operation == "Insert":
                    result.collisions += 1
                log(index, f"Compare with {node.key}: different key. Follow the next link.", "collision")
                previous, node = node, node.next
            if operation == "Insert":
                if previous is None:
                    self.slots[index] = Node(key)
                else:
                    previous.next = Node(key)
                self.count += 1
                result.status = "Inserted"
                log(index, f"Append {key} to bucket {index}.", "success")
            else:
                result.status = "Not found"
                log(index, "End of chain. Key is not present.", "end")
            return result

        first_deleted = None
        for index in self.indices(key):
            result.probes += 1
            value = self.slots[index]
            if value == DELETED:
                if first_deleted is None:
                    first_deleted = index
                log(index, "Deleted marker: remember this slot and keep looking.")
                continue
            if value is EMPTY:
                if operation == "Insert":
                    target = first_deleted if first_deleted is not None else index
                    self.slots[target] = key
                    self.count += 1
                    result.status = "Inserted"
                    log(index, f"Slot {index} is empty. Duplicate check is complete.")
                    log(target, f"Store {key} at slot {target}.", "success")
                else:
                    result.status = "Not found"
                    log(index, "Empty slot: the key is not present.", "end")
                return result
            result.comparisons += 1
            if value == key:
                if operation == "Delete":
                    self.slots[index] = DELETED
                    self.count -= 1
                    result.status = "Deleted"
                    log(index, f"Found {key}. Leave a deleted marker to preserve the probe path.", "success")
                else:
                    result.status = "Already present" if operation == "Insert" else "Found"
                    log(index, f"Compare with {value}: match. {result.status}.", "success")
                return result
            if operation == "Insert":
                result.collisions += 1
            log(index, f"Slot {index} holds {value}, a different key. Continue probing.", "collision")

        if operation == "Insert" and first_deleted is not None:
            self.slots[first_deleted] = key
            self.count += 1
            result.status = "Inserted"
            log(first_deleted, f"All slots checked. Reuse deleted slot {first_deleted} for {key}.", "success")
        else:
            result.status = "Table full" if operation == "Insert" else "Not found"
            log(key % self.size, f"All {self.size} slots checked. {result.status}.", "end")
        return result
