# Pattern catalog

Each row lists the pattern, the **signals** in a problem statement that should trigger it, and a ladder of classic practice problems (well-known LeetCode titles) from easy to hard.

| Pattern | Signals | Ladder (easy → hard) |
|---|---|---|
| Hashing / frequency map | "find pair/duplicate", "count occurrences", O(n) needed on unsorted data | Two Sum → Group Anagrams → Longest Consecutive Sequence → Subarray Sum Equals K |
| Two pointers | sorted array, pairs/triplets, in-place partitioning, palindromes | Valid Palindrome → 3Sum → Container With Most Water → Trapping Rain Water |
| Sliding window (fixed/variable) | contiguous subarray/substring, "longest/shortest with condition", "at most K" | Maximum Average Subarray I → Longest Substring Without Repeating Characters → Longest Repeating Character Replacement → Minimum Window Substring |
| Prefix sums | many range-sum queries, "subarray sum = k", 2D region sums | Range Sum Query - Immutable → Subarray Sum Equals K → Continuous Subarray Sum → Range Sum Query 2D |
| Binary search (on index) | sorted / rotated input, O(log n) asked | Binary Search → Search in Rotated Sorted Array → Find Minimum in Rotated Sorted Array → Median of Two Sorted Arrays |
| Binary search on answer | "minimise the maximum", "smallest capacity/speed such that", monotonic feasibility | Koko Eating Bananas → Capacity To Ship Packages Within D Days → Split Array Largest Sum |
| Monotonic stack | "next greater/smaller", spans, histogram areas | Next Greater Element I → Daily Temperatures → Online Stock Span → Largest Rectangle in Histogram |
| Monotonic deque | sliding window max/min | Sliding Window Maximum → Shortest Subarray with Sum at Least K |
| Linked list (fast/slow, reversal) | cycle, middle, k-th from end, reorder in place | Reverse Linked List → Linked List Cycle → Reorder List → Reverse Nodes in k-Group |
| Heap / top-K | "k largest/smallest/most frequent", streaming median, merge k sorted | Kth Largest Element in an Array → Top K Frequent Elements → Merge k Sorted Lists → Find Median from Data Stream |
| Intervals | overlapping ranges, meeting rooms, merge/insert | Merge Intervals → Insert Interval → Non-overlapping Intervals → Meeting Rooms II |
| Tree DFS | path sums, depth, subtree properties, LCA | Maximum Depth of Binary Tree → Path Sum II → Lowest Common Ancestor of a Binary Tree → Binary Tree Maximum Path Sum |
| Tree BFS | level order, right view, min depth | Binary Tree Level Order Traversal → Binary Tree Right Side View → Binary Tree Zigzag Level Order Traversal |
| BST properties | sorted order, k-th smallest, validate | Validate Binary Search Tree → Kth Smallest Element in a BST → Recover Binary Search Tree |
| Graph BFS / DFS | grid islands, connected components, shortest path in unweighted graph | Flood Fill → Number of Islands → Rotting Oranges → Word Ladder |
| Topological sort | prerequisites, dependency order, "is there a cycle" in directed graph | Course Schedule → Course Schedule II → Alien Dictionary |
| Union-Find | dynamic connectivity, grouping, redundant edge | Number of Provinces → Redundant Connection → Accounts Merge |
| Shortest path (weighted) | weighted edges, min cost/time | Network Delay Time → Path With Minimum Effort → Cheapest Flights Within K Stops |
| Backtracking | "all combinations/permutations/subsets", constraint search | Subsets → Permutations → Combination Sum → N-Queens |
| 1D DP | "number of ways", "min/max cost" along a sequence, choices per step | Climbing Stairs → House Robber → Coin Change → Longest Increasing Subsequence |
| 2D / string DP | two strings, grid paths, edit operations | Unique Paths → Longest Common Subsequence → Edit Distance → Regular Expression Matching |
| Knapsack DP | pick items under capacity, partition into equal sums | Partition Equal Subset Sum → Target Sum → Ones and Zeroes |
| Interval DP | merge/burst/split a range optimally | Minimum Cost Tree From Leaf Values → Burst Balloons |
| Greedy | locally optimal choice provably global, sort-then-scan | Assign Cookies → Jump Game → Gas Station → Candy |
| Bit manipulation | XOR tricks, subsets as masks, "single number" | Single Number → Counting Bits → Subsets (bitmask) → Maximum XOR of Two Numbers in an Array |
| Trie | prefix queries, word search over many words | Implement Trie → Design Add and Search Words → Word Search II |
| Design (data structures) | "implement a class with O(1) ops" | Min Stack → LRU Cache → LFU Cache |

When the user's problem is not in this list, identify the pattern from its signals, not by name matching.
