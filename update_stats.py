import requests
import os
import re
from collections import Counter

# 配置
ORG_NAME = "aisec-xjtu-group"  # 替换为实际组织名称，例如 "xai-org"
TOKEN = os.getenv("REFRESH_TOKEN")  # 从环境变量读取 PAT
README_PATH = "profile/README.md"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

def get_repos():
    """获取组织的所有仓库（包括私有仓库）"""
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/orgs/{ORG_NAME}/repos?type=all&page={page}&per_page=100"
        try:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            data = response.json()
            if not data:
                break
            repos.extend(data)
            page += 1
        except requests.exceptions.RequestException as e:
            print(f"Error fetching repos: {e}")
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

def generate_stats_card():
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
<div style="background: linear-gradient(135deg, #ffffff 0%, #e0e7ff 100%); padding: 24px; border-radius: 12px; box-shadow: 0 6px 12px rgba(0,0,0,0.15); margin: 16px 0; transition: transform 0.3s ease; max-width: 500px;">
  <h3 style="font-size: 24px; color: #1e3a8a; margin-bottom: 16px;">📊 组织统计</h3>
  <div style="display: flex; align-items: center; margin-bottom: 12px;">
    <span style="font-size: 20px; margin-right: 8px;">📚</span>
    <p style="margin: 0;"><strong>总仓库数</strong>: {total_repos}</p>
  </div>
  <div style="display: flex; align-items: center; margin-bottom: 12px;">
    <span style="font-size: 20px; margin-right: 8px;">⭐</span>
    <p style="margin: 0;"><strong>总星标数</strong>: {total_stars}</p>
  </div>
  <div style="display: flex; align-items: center; margin-bottom: 12px;">
    <span style="font-size: 20px; margin-right: 8px;">🍴</span>
    <p style="margin: 0;"><strong>总复制数</strong>: {total_forks}</p>
  </div>
  <p style="font-weight: bold; color: #1e3a8a; margin-bottom: 8px;">主要语言:</p>
  <ul style="list-style: none; padding: 0; margin: 0;">
    {"".join(f'<li style="margin-bottom: 6px;">🔹 {lang}: {bytes:,} bytes</li>' for lang, bytes in top_languages)}
  </ul>
</div>
<style>
  div:hover {{ transform: translateY(-4px); }}
</style>
<!-- STATS_CARD_END -->"""
    return card

def update_readme():
    """更新 README.md 的指定部分"""
    try:
        with open(README_PATH, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: {README_PATH} not found")
        exit(1)

    # 使用正则表达式替换 STATS_CARD_START 和 STATS_CARD_END 之间的内容
    new_content = re.sub(
        r"<!-- STATS_CARD_START -->.*?<!-- STATS_CARD_END -->",
        generate_stats_card(),
        content,
        flags=re.DOTALL
    )

    # 写回 README.md
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

if __name__ == "__main__":
    update_readme()
