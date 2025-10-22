import string
import random

made_Secret = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(random.randint(10,20)))
print(made_Secret)
