def fibonacci(n):
    """
    Returns the n-th Fibonacci number.
    fibonacci(0) = 0
    fibonacci(1) = 1
    fibonacci(2) = 1
    fibonacci(n) = fibonacci(n-1) + fibonacci(n-2)
    """
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        # BUG: It should be fibonacci(n-1) + fibonacci(n-2)
        # BUG 2: missing return statement for recursion
        fibonacci(n-1) - fibonacci(n-2)
