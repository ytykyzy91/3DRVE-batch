import json
import os

def find_key_paths(obj, target_key, current_path=""):
    """
    在嵌套 JSON 中查找所有 target_key 的完整路径
    返回所有匹配路径（可能多个）
    """

    paths = []

    # dict 情况
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f"{current_path}.{k}" if current_path else k

            if k == target_key:
                paths.append(new_path)

            paths.extend(find_key_paths(v, target_key, new_path))

    # list 情况
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            new_path = f"{current_path}[{i}]"
            paths.extend(find_key_paths(item, target_key, new_path))

    return paths

if __name__ == "__main__":
    json_file = r"D:\Demx_softwares\Plexian_workdic\3D_RVE_calc\RVEtest0610\user_RVE_analysis.json"
    data = json.load(open(json_file, "r", encoding="utf-8"))
    paths = find_key_paths(data, "E")
    print("找到的路径:")
    for p in paths: 
        print(p)