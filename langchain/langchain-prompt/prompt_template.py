from langchain.prompts import PromptTemplate

# 定义一个提示模板，包含adjective和content两个模板变量，模板变量使用{}包括起来
prompt_template = PromptTemplate.from_template(
    "给我讲一个关于{content}的{adjective}笑话。"

)

# 通过模板参数格式化提示模板
result = prompt_template.format(adjective="冷", content="猴子")
print(result)
