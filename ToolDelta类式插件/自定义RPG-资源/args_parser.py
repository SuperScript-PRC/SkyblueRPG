def parse_comments(string: str):
    return {i.split(":")[0]: i.split(":", 1)[1] for i in string.split(",") if i}

def generate_comments(dic: dict):
    return ",".join([f"{i}:{dic[i]}" for i in dic])
