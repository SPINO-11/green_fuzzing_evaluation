g = {}


def t(a):
    global g
    print(g)
    g[a] = "HÄÄÄ"
    print(g)
    print()


a = [1,2,3]
print(a[0:0])