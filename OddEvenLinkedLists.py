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
    loop_cnt = 0
    valuesFromList = []
    while (listNodeIn) and loop_cnt < 25:
        loop_cnt += 1
        valuesFromList.append(listNodeIn.val)
        listNodeIn = listNodeIn.next
    return valuesFromList

def oddEvenList(head: Optional[ListNode]) -> Optional[ListNode]:
    if head is None:
        return ListNode()

    dummyOdd = ListNode()
    dummyEven = ListNode()
    last_odd = ListNode()
    odd_head = dummyOdd
    even_tail = dummyEven

    odd_toggle = True
    while head:
        if odd_toggle:
            odd_head.next = head
            head = head.next
            odd_head = odd_head.next
        else:
            even_tail.next = head
            head = head.next
            even_tail = even_tail.next
        odd_toggle = not odd_toggle
    last_odd.next = dummyEven.next
    return dummyOdd.next

input = buildList([1,2,3,4,5])
output = [1,3,5,2,4]

out_ll = oddEvenList(input)
assert(output == getValues(out_ll)), f'received {getValues(out_ll)}'

input = buildList([2,1,3,5,6,4,7])
output = [2,3,6,7,1,5,4]

out_ll = oddEvenList(input)
assert(output == getValues(out_ll)), f'received {getValues(out_ll)}'