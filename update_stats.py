import requests
import os
import re
from collections import Counter

# 配置
ORG_NAME = "aisec-xjtu-group"  # 替换为实际组织名称，例如 "xai-org"
TOKEN = os.getenv("REFRESH_TOKEN")  # 从环境变量读取 PAT
README_PATH_en = "profile/README.md"
README_PATH_zh = "profile/README-zh.md"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

# def get_repos():
#     """获取组织的所有仓库（包括私有仓库）"""
#     repos = []
#     page = 1
#     while True:
#         url = f"https://api.github.com/orgs/{ORG_NAME}/repos?type=all&page={page}&per_page=100"
#         try:
#             response = requests.get(url, headers=HEADERS)
#             response.raise_for_status()
#             data = response.json()
#             if not data:
#                 break
#             repos.extend(data)
#             page += 1
#         except requests.exceptions.RequestException as e:
#             print(f"Error fetching repos: {e}")
#             exit(1)
#     return repos

def get_repos():
    """从文本文件读取仓库URL以获取所有仓库"""
    repos = []
    try:
        with open("repos.txt", "r", encoding="utf-8") as f:
            repo_urls = [line.strip() for line in f if line.strip()]
        
        for url in repo_urls:
            # 提取仓库名称和组织名称
            repo_path = url.replace("https://github.com/", "").strip('/')
            try:
                repo_name = repo_path.split('/')[-1]
                api_url = f"https://api.github.com/repos/{repo_path}"
                response = requests.get(api_url, headers=HEADERS)
                response.raise_for_status()
                repos.append(response.json())
            except requests.exceptions.RequestException as e:
                print(f"Error fetching repo {repo_path}: {e}")
                continue
    except FileNotFoundError:
        print("Error: repos.txt not found")
        exit(1)
    return repos

def get_languages(repo_name):
    """获取单个仓库的语言统计"""
    url = f"https://api.github.com/repos/{ORG_NAME}/{repo_name}/languages"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching languages for {repo_name}: {e}")
        return {}

def generate_stats_card_en():
    """生成统计卡片的 Markdown 内容"""
    repos = get_repos()
    total_repos = len(repos)
    total_stars = sum(repo["stargazers_count"] for repo in repos)
    total_forks = sum(repo["forks_count"] for repo in repos)

    # 汇总语言
    language_counter = Counter()
    for repo in repos:
        languages = get_languages(repo["name"])
        for lang, bytes in languages.items():
            language_counter[lang] += bytes
    top_languages = language_counter.most_common(3)  # 获取前 3 种语言

    # 生成卡片样式的 Markdown
    card = f"""<!-- STATS_CARD_START -->
<div style="display: flex; justify-content: center;">
  <table style="border-collapse: collapse; width: 80%; background: #f4f4f4; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center;">
    <tr>
      <td style="padding: 10px; font-weight: bold; text-align: center;">Total Repositories 📚</td>
      <td style="padding: 10px; text-align: center;">{total_repos}</td>
    </tr>
    <tr>
      <td style="padding: 10px; font-weight: bold; text-align: center;">Total Stars ⭐</td>
      <td style="padding: 10px; text-align: center;">{total_stars}</td>
    </tr>
    <tr>
      <td style="padding: 10px; font-weight: bold; text-align: center;">Total Forks 🍴</td>
      <td style="padding: 10px; text-align: center;">{total_forks}</td>
    </tr>
    <tr>
      <td style="padding: 10px; font-weight: bold; text-align: center;">Primary Languages 🖨</td>
      <td style="padding: 10px; text-align: center;">
        <ul style="list-style: none; padding: 0; margin: 0;">
          {"".join(f"<li>{lang}: {bytes:,} bytes</li>" for lang, bytes in top_languages)}
        </ul>
      </td>
    </tr>
  </table>
</div>
<!-- STATS_CARD_END -->"""
    return card

def generate_stats_card_zh():
    """生成统计卡片的 Markdown 内容"""
    repos = get_repos()
    total_repos = len(repos)
    total_stars = sum(repo["stargazers_count"] for repo in repos)
    total_forks = sum(repo["forks_count"] for repo in repos)

    # 汇总语言
    language_counter = Counter()
    for repo in repos:
        languages = get_languages(repo["name"])
        for lang, bytes in languages.items():
            language_counter[lang] += bytes
    top_languages = language_counter.most_common(3)  # 获取前 3 种语言

    # 生成卡片样式的 Markdown
    card = f"""<!-- STATS_CARD_START -->
<div style="display: flex; justify-content: center;">
  <table style="border-collapse: collapse; width: 80%; background: #f4f4f4; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center;">
    <tr>
      <td style="padding: 10px; font-weight: bold; text-align: center;">总仓库数 📚</td>
      <td style="padding: 10px; text-align: center;">{total_repos}</td>
    </tr>
    <tr>
      <td style="padding: 10px; font-weight: bold; text-align: center;">总星标数 ⭐</td>
      <td style="padding: 10px; text-align: center;">{total_stars}</td>
    </tr>
    <tr>
      <td style="padding: 10px; font-weight: bold; text-align: center;">总复制数 🍴</td>
      <td style="padding: 10px; text-align: center;">{total_forks}</td>
    </tr>
    <tr>
      <td style="padding: 10px; font-weight: bold; text-align: center;">主要语言 🖨</td>
      <td style="padding: 10px; text-align: center;">
        <ul style="list-style: none; padding: 0; margin: 0;">
          {"".join(f"<li>{lang}: {bytes:,} bytes</li>" for lang, bytes in top_languages)}
        </ul>
      </td>
    </tr>
  </table>
</div>
<!-- STATS_CARD_END -->"""
    return card

def update_readme_en():
    """更新 README.md 的指定部分"""
    try:
        with open(README_PATH_en, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: {README_PATH_en} not found")
        exit(1)

    # 使用正则表达式替换 STATS_CARD_START 和 STATS_CARD_END 之间的内容
    new_content = re.sub(
        r"<!-- STATS_CARD_START -->.*?<!-- STATS_CARD_END -->",
        generate_stats_card_en(),
        content,
        flags=re.DOTALL
    )

    repos = get_repos()
    # 更新表格中的仓库链接
    for repo in repos:
        repo_name = repo["name"]
        stars = repo["stargazers_count"]
        repo_url = f"https://github.com/{ORG_NAME}/{repo_name}"
        badge_url = f"https://img.shields.io/github/stars/{ORG_NAME}/{repo_name}"
        
        # 将仓库行替换为包含星标徽章的版本
        pattern = re.compile(rf"(\[.*\]\({repo_url}\))\s*(\|.*\|)")
        replacement = rf"\1 <img alt='Stars' src='{badge_url}'> \2"
        content = re.sub(pattern, replacement, content)

    # 写回 README.md
    with open(README_PATH_en, "w", encoding="utf-8") as f:
        f.write(new_content)

def update_readme_zh():
    """更新 README.md 的指定部分"""
    try:
        with open(README_PATH_zh, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: {README_PATH_zh} not found")
        exit(1)

    # 使用正则表达式替换 STATS_CARD_START 和 STATS_CARD_END 之间的内容
    new_content = re.sub(
        r"<!-- STATS_CARD_START -->.*?<!-- STATS_CARD_END -->",
        generate_stats_card_zh(),
        content,
        flags=re.DOTALL
    )

    # 写回 README.md
    with open(README_PATH_zh, "w", encoding="utf-8") as f:
        f.write(new_content)

if __name__ == "__main__":
    update_readme_en()
    update_readme_zh()
