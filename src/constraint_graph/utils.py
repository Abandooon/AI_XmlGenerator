def normalize(tag: str) -> str:
# 统一规则：大小写→小写，连字符/点/空格 → 下划线
    if tag is None:
        return ""
    return tag.lower().replace("-", "_").replace(".", "_").replace(" ", "_")
