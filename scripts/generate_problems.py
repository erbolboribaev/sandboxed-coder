"""Writes the full benchmark problem set to problems/*.json. Run once:
    python scripts/generate_problems.py

Expected outputs below were computed with independent reference
implementations (not hand-calculated), to avoid shipping a wrong assertion
that would silently mis-score the benchmark.
"""
import json
from pathlib import Path

PROBLEMS = [
    {
        "name": "two_sum",
        "problem": "Write a Python function `two_sum(nums: list[int], target: int) -> list[int]` that returns the indices of the two numbers in nums that add up to target. Assume exactly one valid answer exists, and you may not use the same element twice.",
        "test_code": "assert two_sum([2, 7, 11, 15], 9) == [0, 1]\nassert two_sum([3, 2, 4], 6) == [1, 2]\nassert two_sum([3, 3], 6) == [0, 1]",
    },
    {
        "name": "longest_substring",
        "problem": "Write a Python function `length_of_longest_substring(s: str) -> int` that returns the length of the longest substring of `s` without repeating characters. The empty string should return 0.",
        "test_code": "assert length_of_longest_substring('abcabcbb') == 3\nassert length_of_longest_substring('bbbbb') == 1\nassert length_of_longest_substring('pwwkew') == 3\nassert length_of_longest_substring('') == 0\nassert length_of_longest_substring(' ') == 1\nassert length_of_longest_substring('dvdf') == 3\nassert length_of_longest_substring('abba') == 2\nassert length_of_longest_substring('tmmzuxt') == 5",
    },
    {
        "name": "three_sum",
        "problem": "Write a Python function `three_sum(nums: list[int]) -> list[list[int]]` that returns all unique triplets [a, b, c] from nums such that a + b + c == 0. Each triplet should be sorted in non-decreasing order, and the result must not contain duplicate triplets.",
        "test_code": "def _norm(result):\n    return sorted(tuple(sorted(t)) for t in result)\n\nassert _norm(three_sum([-1, 0, 1, 2, -1, -4])) == _norm([[-1, -1, 2], [-1, 0, 1]])\nassert _norm(three_sum([0, 1, 1])) == []\nassert _norm(three_sum([0, 0, 0])) == [(0, 0, 0)]\nassert _norm(three_sum([-2, 0, 0, 2, 2])) == [(-2, 0, 2)]\nassert _norm(three_sum([])) == []\nassert _norm(three_sum([0])) == []\nassert _norm(three_sum([1, -1, -1, 0])) == [(-1, 0, 1)]",
    },
    {
        "name": "valid_parentheses",
        "problem": "Write a Python function `is_valid(s: str) -> bool` that returns True if the string, containing only the characters '(', ')', '{', '}', '[' and ']', has valid (correctly matched and nested) bracket pairs.",
        "test_code": "assert is_valid('()') == True\nassert is_valid('()[]{}') == True\nassert is_valid('(]') == False\nassert is_valid('([)]') == False\nassert is_valid('{[]}') == True\nassert is_valid('') == True\nassert is_valid('(') == False",
    },
    {
        "name": "valid_anagram",
        "problem": "Write a Python function `is_anagram(s: str, t: str) -> bool` that returns True if t is an anagram of s (same characters, same multiplicity, any order).",
        "test_code": "assert is_anagram('anagram', 'nagaram') == True\nassert is_anagram('rat', 'car') == False\nassert is_anagram('a', 'ab') == False\nassert is_anagram('', '') == True",
    },
    {
        "name": "max_subarray",
        "problem": "Write a Python function `max_subarray(nums: list[int]) -> int` that returns the largest possible sum of a contiguous, non-empty subarray of nums.",
        "test_code": "assert max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6\nassert max_subarray([1]) == 1\nassert max_subarray([5, 4, -1, 7, 8]) == 23",
    },
    {
        "name": "product_except_self",
        "problem": "Write a Python function `product_except_self(nums: list[int]) -> list[int]` that returns an array `answer` where `answer[i]` is the product of all elements of nums except nums[i]. Do not use division.",
        "test_code": "assert product_except_self([1, 2, 3, 4]) == [24, 12, 8, 6]\nassert product_except_self([-1, 1, 0, -3, 3]) == [0, 0, 9, 0, 0]",
    },
    {
        "name": "group_anagrams",
        "problem": "Write a Python function `group_anagrams(strs: list[str]) -> list[list[str]]` that groups anagrams together. The order of groups and the order of strings within a group do not matter.",
        "test_code": "def _norm(res):\n    return sorted(tuple(sorted(g)) for g in res)\n\nassert _norm(group_anagrams(['eat', 'tea', 'tan', 'ate', 'nat', 'bat'])) == _norm([['eat', 'tea', 'ate'], ['tan', 'nat'], ['bat']])\nassert group_anagrams(['']) == [['']]\nassert group_anagrams(['a']) == [['a']]",
    },
    {
        "name": "top_k_frequent",
        "problem": "Write a Python function `top_k_frequent(nums: list[int], k: int) -> list[int]` that returns the k most frequent elements in nums. The order of elements in the result does not matter.",
        "test_code": "assert sorted(top_k_frequent([1, 1, 1, 2, 2, 3], 2)) == [1, 2]\nassert sorted(top_k_frequent([1], 1)) == [1]",
    },
    {
        "name": "reverse_integer",
        "problem": "Write a Python function `reverse_integer(x: int) -> int` that reverses the digits of a 32-bit signed integer x. If reversing causes the value to go outside the signed 32-bit integer range [-2**31, 2**31 - 1], return 0.",
        "test_code": "assert reverse_integer(123) == 321\nassert reverse_integer(-123) == -321\nassert reverse_integer(120) == 21\nassert reverse_integer(0) == 0\nassert reverse_integer(1534236469) == 0",
    },
    {
        "name": "climbing_stairs",
        "problem": "Write a Python function `climbing_stairs(n: int) -> int` that returns the number of distinct ways to climb to the top of a staircase of n steps, taking either 1 or 2 steps at a time.",
        "test_code": "assert climbing_stairs(2) == 2\nassert climbing_stairs(3) == 3\nassert climbing_stairs(5) == 8",
    },
    {
        "name": "coin_change",
        "problem": "Write a Python function `coin_change(coins: list[int], amount: int) -> int` that returns the fewest number of coins needed to make up `amount` using the given coin denominations (unlimited supply of each). Return -1 if it's not possible. coin_change(coins, 0) should return 0.",
        "test_code": "assert coin_change([1, 2, 5], 11) == 3\nassert coin_change([2], 3) == -1\nassert coin_change([1], 0) == 0",
    },
    {
        "name": "merge_intervals",
        "problem": "Write a Python function `merge_intervals(intervals: list[list[int]]) -> list[list[int]]` that merges all overlapping intervals and returns the merged intervals, sorted by start value.",
        "test_code": "assert merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]\nassert merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]",
    },
    {
        "name": "search_rotated_sorted_array",
        "problem": "Write a Python function `search_rotated(nums: list[int], target: int) -> int` that searches for target in nums, a sorted array that has been rotated at some unknown pivot, and returns its index, or -1 if not found.",
        "test_code": "assert search_rotated([4, 5, 6, 7, 0, 1, 2], 0) == 4\nassert search_rotated([4, 5, 6, 7, 0, 1, 2], 3) == -1\nassert search_rotated([1], 0) == -1",
    },
    {
        "name": "longest_common_subsequence",
        "problem": "Write a Python function `longest_common_subsequence(text1: str, text2: str) -> int` that returns the length of the longest common subsequence of text1 and text2 (characters in relative order, not necessarily contiguous).",
        "test_code": "assert longest_common_subsequence('abcde', 'ace') == 3\nassert longest_common_subsequence('abc', 'abc') == 3\nassert longest_common_subsequence('abc', 'def') == 0",
    },
    {
        "name": "word_break",
        "problem": "Write a Python function `word_break(s: str, word_dict: list[str]) -> bool` that returns True if s can be segmented into a space-separated sequence of one or more words from word_dict (words may be reused).",
        "test_code": "assert word_break('leetcode', ['leet', 'code']) == True\nassert word_break('applepenapple', ['apple', 'pen']) == True\nassert word_break('catsandog', ['cats', 'dog', 'sand', 'and', 'cat']) == False",
    },
    {
        "name": "trapping_rain_water",
        "problem": "Write a Python function `trap(height: list[int]) -> int` that computes how much rainwater can be trapped between bars of the given heights after raining (classic 'Trapping Rain Water' problem).",
        "test_code": "assert trap([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]) == 6\nassert trap([4, 2, 0, 3, 2, 5]) == 9",
    },
    {
        "name": "regex_match",
        "problem": "Write a Python function `is_match(s: str, p: str) -> bool` implementing regular expression matching with support for '.' (matches any single character) and '*' (matches zero or more of the preceding element). The match should cover the entire input string (not partial).",
        "test_code": "assert is_match('aa', 'a') == False\nassert is_match('aa', 'a*') == True\nassert is_match('ab', '.*') == True\nassert is_match('aab', 'c*a*b') == True\nassert is_match('mississippi', 'mis*is*p*.') == False\nassert is_match('', 'a*') == True\nassert is_match('', '.*') == True",
    },
    {
        "name": "longest_valid_parentheses",
        "problem": "Write a Python function `longest_valid_parens(s: str) -> int` that, given a string containing only '(' and ')', returns the length of the longest valid (well-formed) parentheses substring.",
        "test_code": "assert longest_valid_parens('(()') == 2\nassert longest_valid_parens(')()())') == 4\nassert longest_valid_parens('') == 0\nassert longest_valid_parens('()(())') == 6\nassert longest_valid_parens('()(()') == 2",
    },
    {
        "name": "median_two_sorted_arrays",
        "problem": "Write a Python function `find_median_sorted_arrays(nums1: list[int], nums2: list[int]) -> float` that returns the median of the two sorted arrays combined.",
        "test_code": "assert find_median_sorted_arrays([1, 3], [2]) == 2.0\nassert find_median_sorted_arrays([1, 2], [3, 4]) == 2.5\nassert find_median_sorted_arrays([], [1]) == 1.0\nassert find_median_sorted_arrays([2], []) == 2.0\nassert find_median_sorted_arrays([0, 0], [0, 0]) == 0.0",
    },
]


def main():
    out_dir = Path("problems")
    out_dir.mkdir(exist_ok=True)
    for spec in PROBLEMS:
        path = out_dir / f"{spec['name']}.json"
        path.write_text(json.dumps(spec, indent=2))
        print(f"wrote {path}")
    print(f"\n{len(PROBLEMS)} problems written to {out_dir}/")


if __name__ == "__main__":
    main()
