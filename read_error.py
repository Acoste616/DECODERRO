try:
    with open("cloud_test_output_v2.txt", "rb") as f:
        data = f.read()
        # Filter for printable ascii (32-126) plus newline (10) and carriage return (13)
        printable = bytes(c for c in data if 32 <= c <= 126 or c == 10 or c == 13)
        print(printable.decode('ascii'))
except Exception as e:
    print(f"Fatal error: {e}")
