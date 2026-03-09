def nested_logic_demo(x):
    if x > 5:
        if x < 2:  # 这是一个深层嵌套的矛盾点
            return "Impossible"
        else:
            return "Greater than 5"
    return "Less or equal to 5"