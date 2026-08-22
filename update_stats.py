import os
import re
import requests

# =========================
# 配置
# =========================
ORG_NAME = "aisec-xjtu-group"
TOKEN = os.getenv("REFRESH_TOKEN")

README_PATH_EN = "profile/README.md"
README_PATH_ZH = "profile/README-zh.md"
REPOS_FILE = "repos.txt"  # 仅作为兜底，不再作为主要数据源

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


# =========================
# 仓库发现与统计
# =========================
def extract_repo_paths_from_html_readme(readme_path):
    """
    从 HTML README 中提取 GitHub 仓库链接：
    https://github.com/<owner>/<repo>

    自动去重，保持原出现顺序。
    """
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        raise SystemExit(f"Error: {readme_path} not found")

    # 只匹配 <a href="https://github.com/owner/repo">...</a>
    pattern = re.compile(
        r'<a\b[^>]*href=["\']https://github\.com/'
        r'([^/"\'\s<>?#]+)/([^/"\'\s<>?#]+)'
        r'/?(?:["\'?#])',
        flags=re.IGNORECASE,
    )

    repo_paths = []
    seen = set()

    for owner, repo in pattern.findall(content):
        repo_path = f"{owner}/{repo}".rstrip("/")
        key = repo_path.lower()
        if key not in seen:
            seen.add(key)
            repo_paths.append(repo_path)

    return repo_paths


def extract_repo_paths_from_txt():
    """从 repos.txt 读取仓库 URL，作为 README 中没有仓库链接时的兜底方案。"""
    if not os.path.exists(REPOS_FILE):
        return []

    repo_paths = []
    seen = set()

    with open(REPOS_FILE, "r", encoding="utf-8") as f:
        for raw_line in f:
            url = raw_line.strip()
            if not url:
                continue

            match = re.match(
                r"^https://github\.com/([^/\s]+)/([^/\s#?]+?)/?$",
                url,
                flags=re.IGNORECASE,
            )
            if not match:
                print(f"Skip invalid GitHub repository URL in {REPOS_FILE}: {url}")
                continue

            repo_path = f"{match.group(1)}/{match.group(2)}"
            key = repo_path.lower()

            if key not in seen:
                seen.add(key)
                repo_paths.append(repo_path)

    return repo_paths


def get_repo_info(repo_path):
    """通过 GitHub API 获取单个仓库信息。"""
    api_url = f"https://api.github.com/repos/{repo_path}"

    try:
        response = requests.get(api_url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Warning: failed to fetch {repo_path}: {e}")
        return None


def get_repos():
    """
    主要从 profile/README.md 的 HTML Repository 链接生成仓库列表。

    这样以后只要在 HTML 表格中新增/删除 Repository，
    Repository Statistics 就会自动同步，不需要再手动维护 repos.txt。
    """
    repo_paths = extract_repo_paths_from_html_readme(README_PATH_EN)

    if repo_paths:
        print(f"Found {len(repo_paths)} unique repository links in {README_PATH_EN}.")
    else:
        print(
            f"No repository links found in {README_PATH_EN}; "
            f"falling back to {REPOS_FILE}."
        )
        repo_paths = extract_repo_paths_from_txt()

    if not repo_paths:
        raise SystemExit(
            "Error: no GitHub repositories found in README or repos.txt."
        )

    repos = []
    for repo_path in repo_paths:
        repo = get_repo_info(repo_path)
        if repo is not None:
            repos.append(repo)

    if not repos:
        raise SystemExit("Error: GitHub API returned no valid repositories.")

    return repos


def collect_stats():
    """汇总 README 中所有有效 Repository 的数量、Stars 和 Forks。"""
    repos = get_repos()

    stats = {
        "total_repos": len(repos),
        "total_stars": sum(repo.get("stargazers_count", 0) for repo in repos),
        "total_forks": sum(repo.get("forks_count", 0) for repo in repos),
    }

    return stats


# =========================
# Statistics Card
# =========================
def generate_stats_card_en(stats):
    """生成英文统计卡片，保持 GitHub README 兼容。"""
    return f"""<!-- STATS_CARD_START -->
<table>
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
    """生成中文统计卡片，保持 GitHub README 兼容。"""
    return f"""<!-- STATS_CARD_START -->
<table>
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
    """替换 STATS_CARD_START 和 STATS_CARD_END 之间的统计内容。"""
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
            "Please add <!-- STATS_CARD_START --> and "
            "<!-- STATS_CARD_END -->."
        )

    new_content = pattern.sub(card, content, count=1)

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)


# =========================
# HTML Repository Stars Badge
# =========================
def add_star_badges_to_html_readme(readme_path):
    """
    为 HTML 表格 Repository 单元格中的 GitHub 仓库链接补 Stars badge。

    已经存在 img.shields.io/github/stars/... 时不会重复添加。
    """
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Warning: {readme_path} not found")
        return

    td_pattern = re.compile(
        r"<td\b[^>]*>.*?</td>",
        flags=re.IGNORECASE | re.DOTALL,
    )

    anchor_pattern = re.compile(
        r'(<a\b[^>]*href=["\']https://github\.com/'
        r'([^/"\'\s<>]+/[^/"\'\s<>?#]+)'
        r'/?["\'][^>]*>.*?</a>)',
        flags=re.IGNORECASE | re.DOTALL,
    )

    def update_td(match):
        cell = match.group(0)

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

        return (
            cell[:anchor_match.start()]
            + replacement
            + cell[anchor_match.end():]
        )

    new_content = td_pattern.sub(update_td, content)

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)


# =========================
# Main
# =========================
def main():
    stats = collect_stats()

    print(
        "Calculated repository statistics: "
        f"{stats['total_repos']} repositories, "
        f"{stats['total_stars']} stars, "
        f"{stats['total_forks']} forks."
    )

    update_readme(
        README_PATH_EN,
        generate_stats_card_en(stats),
    )

    update_readme(
        README_PATH_ZH,
        generate_stats_card_zh(stats),
    )

    add_star_badges_to_html_readme(README_PATH_EN)
    add_star_badges_to_html_readme(README_PATH_ZH)

    print("README statistics and repository badges updated successfully.")


if __name__ == "__main__":
    main()
