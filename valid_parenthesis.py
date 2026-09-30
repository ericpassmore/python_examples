class Solution:
    def isValid(self, s:str) -> bool:
        matching_brackets: dict[str, str] = {
            "(": ")",
            "[": "]",
            "{": "}"
        }

        stack = []
        if len(s) % 2 != 0:
            return False
        for char in s:
            # remember opening brackets
            if char in matching_brackets:
                stack.append(char)
            # closing brackets need a matching opening bracket
            else:
                if not stack:
                    return False

                opening_bracket = stack.pop()
                if matching_brackets[opening_bracket] != char:
                    return False
        return not stack



sol = Solution()
for term, expected in [
    ("[",False),
    ("()",True),
    ("){",False),
    ("()[]{}",True),
    ("({})",True),
    ("([])", True),
    ("(]",False),
    ("([)]",False),
    ("{[)]", False),
    ("(([]){})",True),
    ("([)]",False),
    ("(){}}{",False),
    ("[({(())}[()])]", True)
    ]:
    if sol.isValid(term) != expected:
        print(f'Expected term {term} to be {expected}')