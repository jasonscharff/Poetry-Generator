__author__ = 'jasonscharff'


f = open('output.txt', 'w')
base = open('shakespeareSonnets.txt', 'r')
for line in base:
    if "href" in line:
        pass
    else:
        f.write(line)
