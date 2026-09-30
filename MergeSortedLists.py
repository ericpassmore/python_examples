from typing import Optional, List

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def buildList(listIn: list) -> Optional[ListNode]:
    linkedList: Optional[ListNode] = None
    for el in reversed(listIn):
        linkedList = ListNode(el,linkedList) # type: ignore
    return linkedList

def getValues(listNodeIn: Optional[ListNode] | None) -> List:
    if listNodeIn is None:
        return []
    valuesFromList = []
    while (listNodeIn.next is not None):
        valuesFromList.append(listNodeIn.val)
        listNodeIn = listNodeIn.next
    valuesFromList.append(listNodeIn.val)
    return valuesFromList

def mergeTwoLists(list1: Optional[ListNode], list2: Optional[ListNode]) -> Optional[ListNode]:
    if list1 is None:
        return list2
    if list2 is None:
        return list1

    dummy = ListNode()
    current = dummy

    while list1 and list2:
        if list1.val <= list2.val:
            current.next = list1
            list1 = list1.next
        else:
            current.next = list2
            list2 = list2.next
        current = current.next
    current.next = list1 or list2
    return dummy.next

list1 = buildList([1,2,4])
list2 = buildList([1,3,4])
expected = [1,1,2,3,4,4]

out = mergeTwoLists(list1,list2)
assert (expected == getValues(out)), f'Result1: failed {getValues(out)}'
