cdef float prod(float __iterable):
    cdef float total = 1

    cdef float i
    for i in __iterable:
        total *= i

    return total

print("HelloWorld")
