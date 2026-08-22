import os
import re
import requests

# 配置
ORG_NAME = "aisec-xjtu-group"
TOKEN = os.getenv("REFRESH_TOKEN")

README_PATH_EN = "profile/README.md"
README_PATH_ZH = "profile/README-zh.md"
REPOS_FILE = "repos.txt"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


def get_repos():
    """从 repos.txt 读取 GitHub 仓库 URL，并获取仓库信息。"""
    repos = []

    try:
        with open(REPOS_FILE, "r", encoding="utf-8") as f:
            repo_urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        raise SystemExit(f"Error: {REPOS_FILE} not found")

    for url in repo_urls:
        match = re.match(
            r"^https://github\.com/([^/\s]+)/([^/\s#?]+?)/?$",
            url,
            flags=re.IGNORECASE,
        )
        if not match:
            print(f"Skip invalid GitHub repository URL: {url}")
            continue

        owner, repo_name = match.groups()
        repo_path = f"{owner}/{repo_name}"
        api_url = f"https://api.github.com/repos/{repo_path}"

        try:
            response = requests.get(api_url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            repos.append(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error fetching repo {repo_path}: {e}")

    return repos


def collect_stats():
    """只请求一次 GitHub API，汇总 README 需要的统计信息。"""
    repos = get_repos()

    return {
        "total_repos": len(repos),
        "total_stars": sum(repo.get("stargazers_count", 0) for repo in repos),
        "total_forks": sum(repo.get("forks_count", 0) for repo in repos),
    }


def generate_stats_card_en(stats):
    """生成 GitHub README 兼容的英文统计表。"""
    return f"""<!-- STATS_CARD_START -->
<table align="center">
<tr>
<th align="center">Metric</th>
<th align="center">Count</th>
</tr>
<tr>
<td align="center"><b>Total Repositories 📚</b></td>
<td align="center">{stats["total_repos"]}</td>
</tr>
<tr>
<td align="center"><b>Total Stars ⭐</b></td>
<td align="center">{stats["total_stars"]}</td>
</tr>
<tr>
<td align="center"><b>Total Forks 🍴</b></td>
<td align="center">{stats["total_forks"]}</td>
</tr>
</table>
<!-- STATS_CARD_END -->"""


def generate_stats_card_zh(stats):
    """生成 GitHub README 兼容的中文统计表。"""
    return f"""<!-- STATS_CARD_START -->
<table align="center">
<tr>
<th align="center">统计项</th>
<th align="center">数量</th>
</tr>
<tr>
<td align="center"><b>总仓库数 📚</b></td>
<td align="center">{stats["total_repos"]}</td>
</tr>
<tr>
<td align="center"><b>总星标数 ⭐</b></td>
<td align="center">{stats["total_stars"]}</td>
</tr>
<tr>
<td align="center"><b>总 Fork 数 🍴</b></td>
<td align="center">{stats["total_forks"]}</td>
</tr>
</table>
<!-- STATS_CARD_END -->"""


def update_readme(readme_path, card):
    """替换 README 中 STATS_CARD_START / STATS_CARD_END 之间的内容。"""
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        raise SystemExit(f"Error: {readme_path} not found")

    pattern = re.compile(
        r"<!-- STATS_CARD_START -->.*?<!-- STATS_CARD_END -->",
        flags=re.DOTALL,
    )

    if not pattern.search(content):
        raise SystemExit(
            f"Error: stats markers not found in {readme_path}. "
            "Please add <!-- STATS_CARD_START --> and <!-- STATS_CARD_END --> first."
        )

    new_content = pattern.sub(card, content, count=1)

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)


def add_star_badges_to_html_readme(readme_path):
    """
    给 HTML 表格中的 GitHub 仓库链接自动添加 Stars badge。

    仅处理 <td>...</td> 单元格：
    - 如果单元格已经包含 GitHub stars badge，则保持不变；
    - 如果单元格中存在 https://github.com/<owner>/<repo> 链接，
      则在该链接后添加 badge。

    这样不会再依赖旧的 Markdown 表格语法。
    """
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: {readme_path} not found")
        return

    td_pattern = re.compile(r"<td\b[^>]*>.*?</td>", flags=re.IGNORECASE | re.DOTALL)

    anchor_pattern = re.compile(
        r'(<a\b[^>]*href=["\']https://github\.com/'
        r'([^/"\'\s<>]+/[^/"\'\s<>?#]+)'
        r'/?["\'][^>]*>.*?</a>)',
        flags=re.IGNORECASE | re.DOTALL,
    )

    def update_td(match):
        cell = match.group(0)

        # 已经有 stars badge 时不重复添加
        if "img.shields.io/github/stars/" in cell:
            return cell

        anchor_match = anchor_pattern.search(cell)
        if not anchor_match:
            return cell

        repo_path = anchor_match.group(2).rstrip("/")
        anchor_html = anchor_match.group(1)
        badge = (
            f'<img alt="Stars" '
            f'src="https://img.shields.io/github/stars/{repo_path}">'
        )

        replacement = f"{anchor_html}<br>{badge}"
        return cell[:anchor_match.start()] + replacement + cell[anchor_match.end():]

    new_content = td_pattern.sub(update_td, content)

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)


def main():
    # 统计数据只获取一次，避免英文/中文 README 重复请求 GitHub API
    stats = collect_stats()

    update_readme(README_PATH_EN, generate_stats_card_en(stats))
    update_readme(README_PATH_ZH, generate_stats_card_zh(stats))

    # HTML 表格版本：英文和中文 README 都检查并补 Stars badge
    add_star_badges_to_html_readme(README_PATH_EN)
    add_star_badges_to_html_readme(README_PATH_ZH)

    print(
        "README stats updated successfully: "
        f"{stats['total_repos']} repos, "
        f"{stats['total_stars']} stars, "
        f"{stats['total_forks']} forks."
    )


if __name__ == "__main__":
    main()
