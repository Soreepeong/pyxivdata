def camel_to_underscore(s: str):
    res = []
    for i, c in enumerate(s):
        if i == 0:
            res.append(c.lower())
        elif c.isupper():
            res.append("_")
            res.append(c.lower())
        else:
            res.append(c)
    return "".join(res)
