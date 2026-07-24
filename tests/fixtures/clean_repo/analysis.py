def centered(values):
    average = sum(values) / len(values)
    return [value - average for value in values]

