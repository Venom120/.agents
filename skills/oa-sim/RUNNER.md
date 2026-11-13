# Running candidate code

Shared by `oa-sim`, `mock-interview` and `system-design-mock`. Use it whenever you compile, run or time code.

## Clock

Use `date +%s` for Unix seconds. If `date` isn't available or doesn't support `%s` (Windows), use:

```bash
python3 -c "import time; print(int(time.time()))"
```

## Compile and run, per language

Work in a temp directory (`mktemp -d`, or `python3 -c "import tempfile; print(tempfile.mkdtemp())"` on Windows). Feed stdin from a file and capture stdout.

| Language | Compile | Run | Time multiplier |
|---|---|---|---|
| C++ | `g++ -O2 -std=c++17 -o sol sol.cpp` (or `clang++`) | `./sol < in.txt` | 1× |
| C | `gcc -O2 -o sol sol.c` | `./sol < in.txt` | 1× |
| Java | `javac Main.java` | `java -Xss64m Main < in.txt` | 2× |
| Python | none | `python3 sol.py < in.txt` | 3× (5× for heavy recursion or large I/O) |
| JavaScript | none | `node sol.js < in.txt` | 2× |
| Go | `go build -o sol sol.go` | `./sol < in.txt` | 1.5× |

**Time limit** = base limit × multiplier. The base is 2 s unless the problem says otherwise. Always tell the candidate which limit applied ("Python: 6 s per test"). These multipliers are typical of judge platforms, not any company's rules; say so if asked.

Check the toolchain first (`g++ --version`, `javac -version`, `node --version`, `go version`). If the candidate's language isn't installed, say so and fall back to hand-tracing, stated as such.

## Timeouts that work everywhere

`timeout` (Linux) and `gtimeout` (macOS with coreutils) are convenient but often missing. They don't exist on stock macOS or Windows. The portable option is a Python runner, which works on every OS:

```python
import subprocess, sys, time
def run(cmd, stdin_path, limit_s):
    with open(stdin_path) as f:
        t = time.time()
        try:
            p = subprocess.run(cmd, stdin=f, capture_output=True, text=True, timeout=limit_s)
        except subprocess.TimeoutExpired:
            return "TLE", "", time.time() - t
    if p.returncode != 0:
        return "RE", p.stderr[-500:], time.time() - t
    return "OK", p.stdout, time.time() - t
```

Compare outputs after stripping trailing whitespace on each line and at the end. For floating-point answers, compare with a tolerance stated in the problem (default 1e-6).

## Differential (random) testing

Used by `mock-interview` §5 and recommended for `oa-sim`:

1. Have three programs: the **candidate's**, your **reference** (optimal), and a **brute force** (obviously correct, slow).
2. Write a small **generator** that prints one random valid input from a seed, sized so that the brute force finishes quickly (for example n ≤ 8).
3. Before the candidate ever sees the problem, run the reference against the brute force on a few hundred seeds. **If they disagree, fix yours first.** Never grade with an unverified reference.
4. When grading, loop over seeds and compare the candidate's output with the brute force. Stop at the first mismatch, or when you hit the count (default 2,000, up to 20,000) or a 20-second wall-clock cap. Report `N random inputs, M mismatches`, and show the first failing **input only**.
5. Then run one **maximum-size** input against the reference only, to check the time limit.
