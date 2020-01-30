def oxford_comma(items):
    if len(items) > 2:
        items[-1] = "and " + items[-1]
        return ", ".join(items)
    else:
        return " and ".join(items)
