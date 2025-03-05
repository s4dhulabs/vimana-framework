
from d4m8 import siddhi

with open('urls', 'r') as file:
    urls = [u.strip() for u in file.readlines()]
#for url in urls:
#    print(url)

siddhi(**{'target_url':urls}).start()
