def invoice_audit_process(amount):
    # 第一步：基础金额准入检查
    if amount > 5000:
        # 第二步：高额发票需要人工二次确认
        # 故意构造逻辑矛盾：如果进入了 amount > 5000 分支
        # 下面这个嵌套判断 amount < 1000 永远不会成立
        if amount < 1000:
            return "Critical_Error: Logic Conflict"
        else:
            return "Action: Send to Manager for Approval"
    
    # 第三步：小额发票自动报销
    return "Action: Auto Reimbursement"