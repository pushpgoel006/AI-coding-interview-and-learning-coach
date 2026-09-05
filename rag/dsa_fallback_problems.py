TWO_SUM = {
    "slug": "two-sum",
    "title": "Two Sum",
    "statement": (
        "Given an array of integers nums and an integer target, return the "
        "indices of the two numbers that add up to target. You may assume "
        "each input has exactly one solution, and you may not use the same "
        "element twice.\n\n"
        "Example: nums = [2, 7, 11, 15], target = 9 -> output [0, 1] "
        "(nums[0] + nums[1] == 9).\n\n"
        "Constraints: 2 <= nums.length <= 10^4, -10^9 <= nums[i] <= 10^9, "
        "-10^9 <= target <= 10^9."
    ),
}

CONTAINS_DUPLICATE = {
    "slug": "contains-duplicate",
    "title": "Contains Duplicate",
    "statement": (
        "Given an integer array nums, return true if any value appears at "
        "least twice in the array, and false if every element is distinct.\n\n"
        "Example: nums = [1, 2, 3, 1] -> true. nums = [1, 2, 3, 4] -> false.\n\n"
        "Constraints: 1 <= nums.length <= 10^5, -10^9 <= nums[i] <= 10^9."
    ),
}

VALID_PALINDROME = {
    "slug": "valid-palindrome",
    "title": "Valid Palindrome",
    "statement": (
        "Given a string s, return true if it is a palindrome after "
        "converting all uppercase letters to lowercase and removing all "
        "non-alphanumeric characters.\n\n"
        "Example: s = \"A man, a plan, a canal: Panama\" -> true. "
        "s = \"race a car\" -> false.\n\n"
        "Constraints: 1 <= s.length <= 2 * 10^5, s consists of printable "
        "ASCII characters."
    ),
}

CLIMBING_STAIRS = {
    "slug": "climbing-stairs",
    "title": "Climbing Stairs",
    "statement": (
        "You are climbing a staircase with n steps. Each time you can climb "
        "1 or 2 steps. Return the number of distinct ways to reach the top.\n\n"
        "Example: n = 3 -> 3 (1+1+1, 1+2, 2+1).\n\n"
        "Constraints: 1 <= n <= 45."
    ),
}

BINARY_SEARCH = {
    "slug": "binary-search",
    "title": "Binary Search",
    "statement": (
        "Given a sorted array of distinct integers nums and a target value, "
        "return the index of target if it exists, otherwise return -1. Must "
        "run in O(log n) time.\n\n"
        "Example: nums = [-1, 0, 3, 5, 9, 12], target = 9 -> 4.\n\n"
        "Constraints: 1 <= nums.length <= 10^4, nums is sorted in ascending "
        "order, all values are unique."
    ),
}

MAX_DEPTH_BINARY_TREE = {
    "slug": "maximum-depth-of-binary-tree",
    "title": "Maximum Depth of Binary Tree",
    "statement": (
        "Given the root of a binary tree, return its maximum depth (the "
        "number of nodes along the longest path from the root down to the "
        "farthest leaf).\n\n"
        "Example: root = [3, 9, 20, null, null, 15, 7] -> 3.\n\n"
        "Constraints: the number of nodes is in the range [0, 10^4], "
        "-100 <= Node.val <= 100."
    ),
}

FIND_PATH_EXISTS = {
    "slug": "find-if-path-exists-in-graph",
    "title": "Find if Path Exists in Graph",
    "statement": (
        "You are given an undirected graph with n nodes labeled 0 to n-1 "
        "and a list of edges, plus a source node and a destination node. "
        "Return true if there is a valid path from source to destination.\n\n"
        "Example: n = 3, edges = [[0,1],[1,2],[2,0]], source = 0, "
        "destination = 2 -> true.\n\n"
        "Constraints: 1 <= n <= 2 * 10^5, no self-loops, no repeated edges."
    ),
}

REVERSE_LINKED_LIST = {
    "slug": "reverse-linked-list",
    "title": "Reverse Linked List",
    "statement": (
        "Given the head of a singly linked list, reverse the list and "
        "return the new head.\n\n"
        "Example: head = [1,2,3,4,5] -> [5,4,3,2,1].\n\n"
        "Constraints: the number of nodes is in the range [0, 5000], "
        "-5000 <= Node.val <= 5000."
    ),
}

VALID_PARENTHESES = {
    "slug": "valid-parentheses",
    "title": "Valid Parentheses",
    "statement": (
        "Given a string s containing just the characters '(', ')', '{', "
        "'}', '[' and ']', determine if the input string is valid: every "
        "opening bracket must be closed by the same type of bracket, and in "
        "the correct order.\n\n"
        "Example: s = \"()[]{}\" -> true. s = \"(]\" -> false.\n\n"
        "Constraints: 1 <= s.length <= 10^4."
    ),
}

ASSIGN_COOKIES = {
    "slug": "assign-cookies",
    "title": "Assign Cookies",
    "statement": (
        "Each child i has a greed factor g[i] (the minimum cookie size that "
        "will content them). Each cookie j has a size s[j]. A cookie can "
        "satisfy a child if s[j] >= g[i]; each child gets at most one "
        "cookie. Return the maximum number of content children.\n\n"
        "Example: g = [1,2,3], s = [1,1] -> 1.\n\n"
        "Constraints: 1 <= g.length, s.length <= 3 * 10^4."
    ),
}

BINARY_WATCH = {
    "slug": "binary-watch",
    "title": "Binary Watch",
    "statement": (
        "A binary watch has 4 LEDs for hours (0-11) and 6 LEDs for minutes "
        "(0-59). Given an integer turnedOn representing the number of LEDs "
        "currently lit, return all possible times the watch could show, in "
        "any order, formatted as \"H:MM\".\n\n"
        "Example: turnedOn = 1 -> [\"0:01\",\"0:02\",\"0:04\",\"0:08\","
        "\"0:16\",\"0:32\",\"1:00\",\"2:00\",\"4:00\",\"8:00\"].\n\n"
        "Constraints: 0 <= turnedOn <= 10."
    ),
}

SORT_ARRAY_BY_PARITY = {
    "slug": "sort-array-by-parity",
    "title": "Sort Array By Parity",
    "statement": (
        "Given an integer array nums, move all even integers to the front "
        "followed by all odd integers, and return the resulting array. Any "
        "order within each group is acceptable.\n\n"
        "Example: nums = [3,1,2,4] -> [2,4,3,1] (or any valid arrangement).\n\n"
        "Constraints: 1 <= nums.length <= 5000, 0 <= nums[i] <= 5000."
    ),
}

VALID_ANAGRAM = {
    "slug": "valid-anagram",
    "title": "Valid Anagram",
    "statement": (
        "Given two strings s and t, return true if t is an anagram of s "
        "(uses exactly the same letters, same counts, possibly reordered).\n\n"
        "Example: s = \"anagram\", t = \"nagaram\" -> true. s = \"rat\", "
        "t = \"car\" -> false.\n\n"
        "Constraints: 1 <= s.length, t.length <= 5 * 10^4, lowercase "
        "English letters."
    ),
}

LAST_STONE_WEIGHT = {
    "slug": "last-stone-weight",
    "title": "Last Stone Weight",
    "statement": (
        "You are given an array of stone weights. Repeatedly pick the two "
        "heaviest stones and smash them together: if equal, both are "
        "destroyed; otherwise the lighter is destroyed and the heavier's "
        "new weight is the difference. Return the weight of the last "
        "remaining stone, or 0 if none remain.\n\n"
        "Example: stones = [2,7,4,1,8,1] -> 1.\n\n"
        "Constraints: 1 <= stones.length <= 30, 1 <= stones[i] <= 1000."
    ),
}

MAX_AVERAGE_SUBARRAY = {
    "slug": "maximum-average-subarray-i",
    "title": "Maximum Average Subarray I",
    "statement": (
        "Given an integer array nums and an integer k, find the contiguous "
        "subarray of length k that has the maximum average value, and "
        "return that average.\n\n"
        "Example: nums = [1,12,-5,-6,50,3], k = 4 -> 12.75 "
        "(subarray [12,-5,-6,50]).\n\n"
        "Constraints: n == nums.length, 1 <= k <= n <= 10^5."
    ),
}

PRODUCT_EXCEPT_SELF = {
    "slug": "product-of-array-except-self",
    "title": "Product of Array Except Self",
    "statement": (
        "Given an integer array nums, return an array answer such that "
        "answer[i] is the product of all elements of nums except nums[i], "
        "without using division, in O(n) time.\n\n"
        "Example: nums = [1,2,3,4] -> [24,12,8,6].\n\n"
        "Constraints: 2 <= nums.length <= 10^5, the product of any prefix "
        "or suffix fits in a 32-bit integer."
    ),
}

GROUP_ANAGRAMS = {
    "slug": "group-anagrams",
    "title": "Group Anagrams",
    "statement": (
        "Given an array of strings strs, group the anagrams together. You "
        "may return the answer in any order.\n\n"
        "Example: strs = [\"eat\",\"tea\",\"tan\",\"ate\",\"nat\",\"bat\"] "
        "-> [[\"bat\"],[\"nat\",\"tan\"],[\"ate\",\"eat\",\"tea\"]].\n\n"
        "Constraints: 1 <= strs.length <= 10^4, 0 <= strs[i].length <= 100, "
        "lowercase English letters."
    ),
}

THREE_SUM = {
    "slug": "3sum",
    "title": "3Sum",
    "statement": (
        "Given an integer array nums, return all unique triplets "
        "[nums[i], nums[j], nums[k]] such that i != j != k and they sum to "
        "0. The solution set must not contain duplicate triplets.\n\n"
        "Example: nums = [-1,0,1,2,-1,-4] -> [[-1,-1,2],[-1,0,1]].\n\n"
        "Constraints: 3 <= nums.length <= 3000, -10^5 <= nums[i] <= 10^5."
    ),
}

COIN_CHANGE = {
    "slug": "coin-change",
    "title": "Coin Change",
    "statement": (
        "Given an array of coin denominations and an amount, return the "
        "fewest number of coins needed to make up that amount. Return -1 "
        "if it cannot be made up.\n\n"
        "Example: coins = [1,2,5], amount = 11 -> 3 (5+5+1).\n\n"
        "Constraints: 1 <= coins.length <= 12, 0 <= amount <= 10^4."
    ),
}

SEARCH_ROTATED_SORTED_ARRAY = {
    "slug": "search-in-rotated-sorted-array",
    "title": "Search in Rotated Sorted Array",
    "statement": (
        "An ascending, distinct-valued array is rotated at an unknown "
        "pivot. Given the rotated array nums and a target, return the "
        "index of target, or -1 if not present. Must run in O(log n).\n\n"
        "Example: nums = [4,5,6,7,0,1,2], target = 0 -> 4.\n\n"
        "Constraints: 1 <= nums.length <= 5000, all values are unique."
    ),
}

LEVEL_ORDER_TRAVERSAL = {
    "slug": "binary-tree-level-order-traversal",
    "title": "Binary Tree Level Order Traversal",
    "statement": (
        "Given the root of a binary tree, return the level order traversal "
        "of its nodes' values (left to right, level by level).\n\n"
        "Example: root = [3,9,20,null,null,15,7] -> [[3],[9,20],[15,7]].\n\n"
        "Constraints: the number of nodes is in the range [0, 2000]."
    ),
}

NUMBER_OF_ISLANDS = {
    "slug": "number-of-islands",
    "title": "Number of Islands",
    "statement": (
        "Given an m x n 2D binary grid representing '1' (land) and '0' "
        "(water), return the number of islands (groups of horizontally or "
        "vertically connected land).\n\n"
        "Example: grid = [[\"1\",\"1\",\"0\"],[\"1\",\"0\",\"0\"],"
        "[\"0\",\"0\",\"1\"]] -> 2.\n\n"
        "Constraints: 1 <= m, n <= 300."
    ),
}

ADD_TWO_NUMBERS = {
    "slug": "add-two-numbers",
    "title": "Add Two Numbers",
    "statement": (
        "Two non-negative integers are represented as linked lists in "
        "reverse order, one digit per node. Add the two numbers and return "
        "the sum as a linked list in the same reversed-digit format.\n\n"
        "Example: l1 = [2,4,3], l2 = [5,6,4] -> [7,0,8] (342 + 465 = 807).\n\n"
        "Constraints: each list has between 1 and 100 nodes, "
        "0 <= Node.val <= 9."
    ),
}

DAILY_TEMPERATURES = {
    "slug": "daily-temperatures",
    "title": "Daily Temperatures",
    "statement": (
        "Given an array of daily temperatures, return an array answer "
        "where answer[i] is the number of days until a warmer temperature; "
        "0 if there isn't one.\n\n"
        "Example: temperatures = [73,74,75,71,69,72,76,73] -> "
        "[1,1,4,2,1,1,0,0].\n\n"
        "Constraints: 1 <= temperatures.length <= 10^5."
    ),
}

JUMP_GAME = {
    "slug": "jump-game",
    "title": "Jump Game",
    "statement": (
        "Given an integer array nums where nums[i] is the maximum jump "
        "length from index i, return true if you can reach the last index "
        "starting from index 0.\n\n"
        "Example: nums = [2,3,1,1,4] -> true. nums = [3,2,1,0,4] -> false.\n\n"
        "Constraints: 1 <= nums.length <= 10^4, 0 <= nums[i] <= 10^5."
    ),
}

SUBSETS = {
    "slug": "subsets",
    "title": "Subsets",
    "statement": (
        "Given an integer array nums of unique elements, return all "
        "possible subsets (the power set). The solution set must not "
        "contain duplicate subsets, returned in any order.\n\n"
        "Example: nums = [1,2,3] -> [[],[1],[2],[1,2],[3],[1,3],[2,3],"
        "[1,2,3]].\n\n"
        "Constraints: 1 <= nums.length <= 10."
    ),
}

SORT_COLORS = {
    "slug": "sort-colors",
    "title": "Sort Colors",
    "statement": (
        "Given an array nums with n objects colored red (0), white (1), or "
        "blue (2), sort them in place so that objects of the same color "
        "are adjacent, in the order red, white, blue, without using a "
        "library sort function.\n\n"
        "Example: nums = [2,0,2,1,1,0] -> [0,0,1,1,2,2].\n\n"
        "Constraints: n == nums.length, 1 <= n <= 300, nums[i] in {0,1,2}."
    ),
}

LONGEST_SUBSTRING_NO_REPEAT = {
    "slug": "longest-substring-without-repeating-characters",
    "title": "Longest Substring Without Repeating Characters",
    "statement": (
        "Given a string s, find the length of the longest substring "
        "without repeating characters.\n\n"
        "Example: s = \"abcabcbb\" -> 3 (\"abc\"). s = \"bbbbb\" -> 1.\n\n"
        "Constraints: 0 <= s.length <= 5 * 10^4."
    ),
}

TOP_K_FREQUENT = {
    "slug": "top-k-frequent-elements",
    "title": "Top K Frequent Elements",
    "statement": (
        "Given an integer array nums and an integer k, return the k most "
        "frequent elements, in any order.\n\n"
        "Example: nums = [1,1,1,2,2,3], k = 2 -> [1,2].\n\n"
        "Constraints: 1 <= nums.length <= 10^5, k is in the range "
        "[1, number of distinct elements]."
    ),
}

FIRST_MISSING_POSITIVE = {
    "slug": "first-missing-positive",
    "title": "First Missing Positive",
    "statement": (
        "Given an unsorted integer array nums, return the smallest missing "
        "positive integer. Must run in O(n) time using O(1) extra space.\n\n"
        "Example: nums = [3,4,-1,1] -> 2. nums = [1,2,0] -> 3.\n\n"
        "Constraints: 1 <= nums.length <= 10^5, -2^31 <= nums[i] <= 2^31-1."
    ),
}

SUBSTRING_CONCAT_ALL_WORDS = {
    "slug": "substring-with-concatenation-of-all-words",
    "title": "Substring with Concatenation of All Words",
    "statement": (
        "Given a string s and an array of same-length words, return the "
        "starting indices of all substrings in s that are a concatenation "
        "of each word in words exactly once, in any order, with no "
        "characters left over.\n\n"
        "Example: s = \"barfoothefoobarman\", words = [\"foo\",\"bar\"] "
        "-> [0,9].\n\n"
        "Constraints: 1 <= s.length <= 10^4, 1 <= words.length <= 5000."
    ),
}

TRAPPING_RAIN_WATER = {
    "slug": "trapping-rain-water",
    "title": "Trapping Rain Water",
    "statement": (
        "Given n non-negative integers representing an elevation map where "
        "the width of each bar is 1, compute how much water it can trap "
        "after raining.\n\n"
        "Example: height = [0,1,0,2,1,0,1,3,2,1,2,1] -> 6.\n\n"
        "Constraints: n == height.length, 1 <= n <= 2 * 10^4."
    ),
}

EDIT_DISTANCE = {
    "slug": "edit-distance",
    "title": "Edit Distance",
    "statement": (
        "Given two strings word1 and word2, return the minimum number of "
        "operations (insert, delete, or replace a character) required to "
        "convert word1 to word2.\n\n"
        "Example: word1 = \"horse\", word2 = \"ros\" -> 3.\n\n"
        "Constraints: 0 <= word1.length, word2.length <= 500."
    ),
}

MEDIAN_TWO_SORTED_ARRAYS = {
    "slug": "median-of-two-sorted-arrays",
    "title": "Median of Two Sorted Arrays",
    "statement": (
        "Given two sorted arrays nums1 and nums2, return the median of the "
        "two combined sorted arrays, in O(log(m+n)) time.\n\n"
        "Example: nums1 = [1,3], nums2 = [2] -> 2.0.\n\n"
        "Constraints: 0 <= m, n <= 1000, 1 <= m + n <= 2000."
    ),
}

BINARY_TREE_MAX_PATH_SUM = {
    "slug": "binary-tree-maximum-path-sum",
    "title": "Binary Tree Maximum Path Sum",
    "statement": (
        "Given the root of a binary tree, return the maximum path sum of "
        "any non-empty path (a path need not pass through the root, and "
        "each node is used at most once).\n\n"
        "Example: root = [1,2,3] -> 6 (path 2 -> 1 -> 3).\n\n"
        "Constraints: the number of nodes is in the range [1, 3 * 10^4]."
    ),
}

WORD_LADDER = {
    "slug": "word-ladder",
    "title": "Word Ladder",
    "statement": (
        "Given a beginWord, an endWord, and a wordList, return the number "
        "of words in the shortest transformation sequence from beginWord "
        "to endWord (changing exactly one letter at a time, each "
        "intermediate word must be in wordList), or 0 if none exists.\n\n"
        "Example: beginWord = \"hit\", endWord = \"cog\", "
        "wordList = [\"hot\",\"dot\",\"dog\",\"lot\",\"log\",\"cog\"] -> 5.\n\n"
        "Constraints: 1 <= beginWord.length <= 10, 1 <= wordList.length <= 5000."
    ),
}

MERGE_K_SORTED_LISTS = {
    "slug": "merge-k-sorted-lists",
    "title": "Merge k Sorted Lists",
    "statement": (
        "You are given an array of k linked-lists, each sorted in "
        "ascending order. Merge all the linked-lists into one sorted "
        "linked-list and return it.\n\n"
        "Example: lists = [[1,4,5],[1,3,4],[2,6]] -> [1,1,2,3,4,4,5,6].\n\n"
        "Constraints: 0 <= k <= 10^4, 0 <= total nodes <= 10^4."
    ),
}

LARGEST_RECTANGLE_HISTOGRAM = {
    "slug": "largest-rectangle-in-histogram",
    "title": "Largest Rectangle in Histogram",
    "statement": (
        "Given an array of integers heights representing the histogram's "
        "bar heights where each bar has width 1, return the area of the "
        "largest rectangle that fits entirely within the histogram.\n\n"
        "Example: heights = [2,1,5,6,2,3] -> 10.\n\n"
        "Constraints: 1 <= heights.length <= 10^5."
    ),
}

CANDY = {
    "slug": "candy",
    "title": "Candy",
    "statement": (
        "There are n children standing in a line, each with a rating "
        "value. You must give each child at least one candy; any child "
        "with a higher rating than a neighbor must get more candies than "
        "that neighbor. Return the minimum candies needed.\n\n"
        "Example: ratings = [1,0,2] -> 5 (candies [2,1,2]).\n\n"
        "Constraints: n == ratings.length, 1 <= n <= 2 * 10^4."
    ),
}

N_QUEENS = {
    "slug": "n-queens",
    "title": "N-Queens",
    "statement": (
        "The n-queens puzzle is placing n queens on an n x n chessboard "
        "such that no two queens attack each other. Given n, return all "
        "distinct board configurations, each as a list of strings.\n\n"
        "Example: n = 4 -> 2 distinct solutions.\n\n"
        "Constraints: 1 <= n <= 9."
    ),
}

COUNT_SMALLER_AFTER_SELF = {
    "slug": "count-of-smaller-numbers-after-self",
    "title": "Count of Smaller Numbers After Self",
    "statement": (
        "Given an integer array nums, return an array counts where "
        "counts[i] is the number of elements to the right of nums[i] that "
        "are smaller than nums[i].\n\n"
        "Example: nums = [5,2,6,1] -> [2,1,1,0].\n\n"
        "Constraints: 1 <= nums.length <= 10^5, -10^4 <= nums[i] <= 10^4."
    ),
}

MINIMUM_WINDOW_SUBSTRING = {
    "slug": "minimum-window-substring",
    "title": "Minimum Window Substring",
    "statement": (
        "Given two strings s and t, return the minimum-length substring of "
        "s that contains every character of t (including duplicates); "
        "return an empty string if no such substring exists.\n\n"
        "Example: s = \"ADOBECODEBANC\", t = \"ABC\" -> \"BANC\".\n\n"
        "Constraints: 1 <= s.length, t.length <= 10^5."
    ),
}

FIND_MEDIAN_DATA_STREAM = {
    "slug": "find-median-from-data-stream",
    "title": "Find Median from Data Stream",
    "statement": (
        "Design a data structure that supports adding integers one at a "
        "time and finding the median of all elements added so far, at any "
        "point, efficiently.\n\n"
        "Example: addNum(1), addNum(2) -> findMedian() = 1.5; "
        "addNum(3) -> findMedian() = 2.\n\n"
        "Constraints: -10^5 <= num <= 10^5, up to 5 * 10^4 calls total."
    ),
}

FALLBACK_PROBLEMS = {
    "array": {
        "easy": [TWO_SUM],
        "medium": [PRODUCT_EXCEPT_SELF],
        "hard": [FIRST_MISSING_POSITIVE],
    },
    "hash-table": {
        "easy": [CONTAINS_DUPLICATE],
        "medium": [GROUP_ANAGRAMS],
        "hard": [SUBSTRING_CONCAT_ALL_WORDS],
    },
    "two-pointers": {
        "easy": [VALID_PALINDROME],
        "medium": [THREE_SUM],
        "hard": [TRAPPING_RAIN_WATER],
    },
    "dynamic-programming": {
        "easy": [CLIMBING_STAIRS],
        "medium": [COIN_CHANGE],
        "hard": [EDIT_DISTANCE],
    },
    "binary-search": {
        "easy": [BINARY_SEARCH],
        "medium": [SEARCH_ROTATED_SORTED_ARRAY],
        "hard": [MEDIAN_TWO_SORTED_ARRAYS],
    },
    "tree": {
        "easy": [MAX_DEPTH_BINARY_TREE],
        "medium": [LEVEL_ORDER_TRAVERSAL],
        "hard": [BINARY_TREE_MAX_PATH_SUM],
    },
    "graph": {
        "easy": [FIND_PATH_EXISTS],
        "medium": [NUMBER_OF_ISLANDS],
        "hard": [WORD_LADDER],
    },
    "linked-list": {
        "easy": [REVERSE_LINKED_LIST],
        "medium": [ADD_TWO_NUMBERS],
        "hard": [MERGE_K_SORTED_LISTS],
    },
    "stack": {
        "easy": [VALID_PARENTHESES],
        "medium": [DAILY_TEMPERATURES],
        "hard": [LARGEST_RECTANGLE_HISTOGRAM],
    },
    "greedy": {
        "easy": [ASSIGN_COOKIES],
        "medium": [JUMP_GAME],
        "hard": [CANDY],
    },
    "backtracking": {
        "easy": [BINARY_WATCH],
        "medium": [SUBSETS],
        "hard": [N_QUEENS],
    },
    "sorting": {
        "easy": [SORT_ARRAY_BY_PARITY],
        "medium": [SORT_COLORS],
        "hard": [COUNT_SMALLER_AFTER_SELF],
    },
    "string": {
        "easy": [VALID_ANAGRAM],
        "medium": [LONGEST_SUBSTRING_NO_REPEAT],
        "hard": [MINIMUM_WINDOW_SUBSTRING],
    },
    "heap-priority-queue": {
        "easy": [LAST_STONE_WEIGHT],
        "medium": [TOP_K_FREQUENT],
        "hard": [FIND_MEDIAN_DATA_STREAM],
    },
    "sliding-window": {
        "easy": [MAX_AVERAGE_SUBARRAY],
        "medium": [LONGEST_SUBSTRING_NO_REPEAT],
        "hard": [MINIMUM_WINDOW_SUBSTRING],
    },
}
