def nested_logic_demo(x):
    if x > 5:
        if x > 10:  
            return "OK"
        else:
            return "大于5小于10"
    return "Less or equal to 5"