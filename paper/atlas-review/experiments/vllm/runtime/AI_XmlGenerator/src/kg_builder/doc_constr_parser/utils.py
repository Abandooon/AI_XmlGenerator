import json
import os


def load_json(file_path):
    """加载 JSON 文件。"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误: 文件未找到于 {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"错误: 无法解码 JSON 文件 {file_path}")
        return None

def save_json(data, file_path):
    """将数据保存到 JSON 文件。"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"已将 JSON 保存至 {file_path}")

def save_jsonl(data_list, file_path):
    """将字典列表保存到 JSONL 文件。"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data_list:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"已将 JSONL 保存至 {file_path}")

def load_jsonl(file_path):
    """加载 JSONL 文件，返回字典列表。"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [json.loads(line) for line in f if line.strip()]
    except FileNotFoundError:
        print(f"错误: 文件未找到于 {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"错误: 无法解码 JSONL 文件 {file_path}")
        return []

def load_markdown(file_path):
    """加载 Markdown 文件。"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"错误: 文件未找到于 {file_path}")
        return None

def save_dataframe_to_csv(df, file_path):
    """将 pandas DataFrame 保存到 CSV 文件。"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df.to_csv(file_path, index=False, encoding='utf-8')
    print(f"已将 CSV 保存至 {file_path}")