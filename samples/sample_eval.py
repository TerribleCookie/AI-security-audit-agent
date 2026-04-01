def run_user_expression():
    user_input = input("请输入表达式: ")
    result = eval(user_input)
    print("结果:", result)

if __name__ == "__main__":
    run_user_expression()