#!/usr/bin/env python3
"""
将 NeoDB API 导出的 index.json 转换为完全兼容 NeoDB 还原格式的压缩包
"""

import csv
import json
import os
import shutil
from datetime import datetime

# 分类映射
CATEGORY_MAP = {
    "book": "book",
    "movie": "movie",
    "tv": "tv",
    "podcast": "podcast",
    "album": "music",
    "game": "game",
    "performance": "performance",
}

# 确保为这些分类生成全套文件
ALL_CATEGORIES = ["book", "movie", "tv", "podcast", "music", "game", "performance"]

SHELF_TYPE_MAP = {
    "wishlist": "wishlist",
    "progress": "progress",
    "complete": "complete",
}


def parse_timestamp(iso_time):
    if not iso_time:
        return ""
    try:
        dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso_time


def get_external_link(item):
    external_resources = item.get("external_resources") or []
    if external_resources:
        for res in external_resources:
            url = res.get("url", "")
            if "douban.com" in url:
                return url
        return external_resources[0].get("url", "")
    return ""


def get_item_info(item):
    parts = []
    credits = item.get("credits") or []
    for credit in credits:
        role = credit.get("role", "")
        name = credit.get("name", "")
        if role and name:
            if role in ["author", "director"]:
                parts.insert(0, name)
            elif role in ["translator"]:
                parts.append(f"译者: {name}")
    if item.get("year"):
        parts.append(str(item["year"]))
    return " / ".join(parts) if parts else ""


def convert_index_to_backup(input_file, output_dir):
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items") or []

    # 初始化所有类别的数据结构，确保即使没数据也会生成对应的空列表
    categorized_data = {
        cat: {"mark": [], "note": [], "review": []} for cat in ALL_CATEGORIES
    }

    for entry in items:
        item = entry.get("item", {})
        category = item.get("category", "unknown")
        file_prefix = CATEGORY_MAP.get(category, category)

        if file_prefix not in categorized_data:
            categorized_data[file_prefix] = {"mark": [], "note": [], "review": []}

        title = item.get("display_title") or item.get("title", "")
        info = get_item_info(item)
        links = get_external_link(item)  # 恢复为 links
        timestamp = parse_timestamp(entry.get("created_time", ""))
        status = SHELF_TYPE_MAP.get(entry.get("shelf_type", ""), "")
        rating = entry.get("rating_grade", "") or ""
        comment = entry.get("comment_text", "") or ""

        tags_raw = entry.get("tags") or []
        tags = ";".join(tags_raw)

        # 改为使用列表按顺序存储，方便后续写入
        categorized_data[file_prefix]["mark"].append(
            [title, info, links, timestamp, status, rating, comment, tags]
        )

    os.makedirs(output_dir, exist_ok=True)
    stats = {}

    for cat in ALL_CATEGORIES:
        data = categorized_data[cat]
        stats[cat] = {"mark": len(data["mark"])}

        # 1. 写入 _mark.csv
        mark_file = os.path.join(output_dir, f"{cat}_mark.csv")
        with open(mark_file, "w", encoding="utf-8", newline="") as f:
            # 强制手动写入严格表头
            f.write("title,info,links,timestamp,status,rating,comment,tags\n")
            writer = csv.writer(f)
            writer.writerows(data["mark"])

        # 2. 写入 _note.csv (应对需要重复 title 的表头)
        note_file = os.path.join(output_dir, f"{cat}_note.csv")
        with open(note_file, "w", encoding="utf-8", newline="") as f:
            f.write("title,info,links,timestamp,progress,title,content\n")
            # JSON 中没有提供 note，所以只生成表头

        # 3. 写入 _review.csv (应对需要重复 title 的表头)
        review_file = os.path.join(output_dir, f"{cat}_review.csv")
        with open(review_file, "w", encoding="utf-8", newline="") as f:
            f.write("title,info,links,timestamp,title,content\n")
            # JSON 中没有提供 review，所以只生成表头

    return stats


def main():
    input_file = r"D:\Aproject\yohakuo.github.io\recover\index.json"
    # 更改目录名以完全贴合图片中的文件夹名
    output_dir = r"D:\Aproject\yohakuo.github.io\recover\neodb_backup"

    print(f"读取: {input_file}")
    print(f"输出目录: {output_dir}\n")

    stats = convert_index_to_backup(input_file, output_dir)

    print("\n转换完成！统计:")
    total = 0
    for category, counts in stats.items():
        if counts["mark"] > 0:
            print(f"  {category}: {counts['mark']} 条标记")
            total += counts["mark"]
    print(f"  总计: {total} 条有效记录已写入")

    print("\n开始生成标准结构压缩包...")
    try:
        zip_path = shutil.make_archive(
            base_name=output_dir, format="zip", root_dir=output_dir
        )
        print(f"成功生成压缩包，可以直接前往 NeoDB 导入: \n  -> {zip_path}")
    except Exception as e:
        print(f"生成压缩包时发生错误: {e}")


if __name__ == "__main__":
    main()
