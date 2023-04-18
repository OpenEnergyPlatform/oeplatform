import os
import sys

print("===== Version")
print(sys.version)

print("===== Path")
for p in sys.path:
    print(p)

print("===== Environ")
for k_v in sorted(os.environ.items()):
    print("%s: %s" % k_v)
