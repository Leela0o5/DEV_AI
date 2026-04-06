# Example Tasks for Multi-Agent Pipeline

## Example 1: Research + Code
```bash
python main.py "Research Python async patterns and write a concurrent web scraper"
```

**Expected outcome:**
- Research worker: Explains asyncio, async/await, event loops
- Coder worker: Writes concurrent web scraper code
- Synthesized result: Comprehensive guide with working code

---

## Example 2: Research + Analysis
```bash
python main.py "Research sorting algorithms and analyze their time complexity trade-offs"
```

**Expected outcome:**
- Research worker: Describes various sorting algorithms
- Analyst worker: Analyzes time/space complexity and use cases
- Synthesized result: Comparison with recommendations

---

## Example 3: All Three Workers
```bash
python main.py "Research Python generators, write an iterator class example, and analyze memory efficiency"
```

**Expected outcome:**
- Research worker: Explains generator concepts
- Coder worker: Implements iterator class
- Analyst worker: Analyzes memory usage patterns
- Synthesized result: Complete educational content

---

## Example 4: Code + Analysis
```bash
python main.py "Write a binary search implementation and analyze its performance characteristics"
```

**Expected outcome:**
- Coder worker: Implements binary search
- Analyst worker: Analyzes time complexity and edge cases
- Synthesized result: Code with detailed analysis

---

## Interactive Mode
```bash
python main.py --interactive
```

Then enter tasks one at a time:
```
> Task: Explain dependency injection patterns
> Task: Write a simple DI container in Python
> Task: exit
```

---

## Verification Test
Run this task to verify all components work:
```bash
python main.py "Research Python async patterns, write a concurrent web scraper, and analyze performance bottlenecks"
```

Check LangSmith trace to verify:
1. Task decomposition into 3 subtasks
2. Parallel worker execution (check timestamps)
3. Successful synthesis of all results
