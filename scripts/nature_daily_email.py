import argparse
import json
import os
import re
import smtplib
import ssl
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path
from zoneinfo import ZoneInfo

from openai import OpenAI


ROOT = Path(__file__).resolve().parents[1]
SENT_FILE = ROOT / "sent_articles.json"

JOURNALS = [
    "Nature",
    "Nature Energy",
    "Nature Sustainability",
    "Nature Climate Change",
    "Nature Communications",
    "Nature Health",
    "Nature Food",
    "Nature Cities",
    "Nature Water",
    "Nature Machine Intelligence",
    "Nature Computational Science",
    "Nature Sensors",
]


def load_sent_articles():
    if not SENT_FILE.exists():
        return {"sent": []}
    return json.loads(SENT_FILE.read_text(encoding="utf-8"))


def save_sent_articles(data):
    SENT_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def normalize(value):
    return re.sub(r"\s+", " ", (value or "").strip()).lower()


def already_sent(candidate, sent_items):
    doi = normalize(candidate.get("doi"))
    url = normalize(candidate.get("url"))
    title = normalize(candidate.get("title"))
    for item in sent_items:
        if doi and doi == normalize(item.get("doi")):
            return True
        if url and url == normalize(item.get("url")):
            return True
        if title and title == normalize(item.get("title")):
            return True
    return False


def parse_recipients(value):
    return [item.strip() for item in re.split(r"[,;]", value or "") if item.strip()]


def extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])


def build_prompt(sent_items, date_string):
    sent_summary = json.dumps(sent_items, ensure_ascii=False, indent=2)
    journals = "、".join(JOURNALS)
    return f"""
你是一个严格的 Nature Portfolio 每日论文筛选和中文邮件写作代理。

今天日期：{date_string}，时区：Asia/Shanghai。

任务：
1. 从以下 Nature Portfolio 期刊的新发表或最近 14 天高价值文章中，选择 1 篇此前没有发送过的文章：{journals}。
2. 只能选择主要通过统计、计算、建模、机器学习、数据分析、仿真、遥感/GIS、计算社会科学、计算生物学、计算流行病学、计算气候科学、计算能源系统、计算城市科学等“用电脑完成核心研究”的文章。
3. 优先原创研究、Analysis、Resource 或方法论文。
4. 不要选择主要靠实验室材料制备、化学合成、催化实验、湿实验生物学、动物实验、纯器件制造或纯材料表征完成的研究；除非这些实验只是辅助验证，而文章核心贡献明确是计算/统计/模型/数据方法。
5. 必须用 Nature 官方文章页、DOI、论文页面、作者机构主页、ORCID、GitHub/Zenodo 等可核验来源。
6. 不要重复以下已经发送过的 DOI、URL 或标题：
{sent_summary}

输出必须是一个 JSON object，不要使用 Markdown 代码块，不要输出 JSON 之外的任何文字。字段如下：
{{
  "title": "英文原题",
  "doi": "DOI，不带 https://doi.org/ 前缀也可以",
  "url": "Nature 官方文章 URL",
  "subject": "Thomas-Nature 每日精选计算统计文章图文解读-XJTLU-{date_string}-中文短标题",
  "html": "完整 HTML 邮件正文"
}}

html 正文必须为中文，适合 Gmail 直接阅读，必须包含这些小节：
0. 选文合规说明：3-5 句话说明为什么符合计算/统计规则，并写 1 句去重检查。
1. 标题：英文原题、中文直译标题、期刊、发表日期、文章类型、DOI 或 Nature 链接、为什么今天选。
2. 作者详细信息：通讯作者、第一作者、关键作者；只能写公开可核验信息，查不到就写“公开资料未核验到”。
3. 五句话讲明白文章做什么：正好 5 句话，本科生语言。
4. 数据集有哪些：必须用 bullet points。
5. 方法：必须用 bullet points。
6. 前四个图以及详细解释：Figure 1-4，每个 figure 用 bullet points，说明“这张图想证明什么”、subfigure 逐个解释、整张图总结。图像可直接嵌入时使用 Nature 官方图片链接；不能嵌入时提供官方 Figure 页面链接并说明原因。
7. 本文重要结论：5-8 条，区分作者直接证明和合理延伸/应用启发，最后附原文与核验来源链接。

质量要求：
- 所有事实性信息必须可核验。
- 不要生成多篇文章汇总。
- 不要重复 sent 列表里的文章。
- 邮件 subject 必须严格以 Thomas-Nature 每日精选计算统计文章图文解读-XJTLU-{date_string}- 开头。
"""


def generate_email(sent_items, date_string):
    client = OpenAI()
    model = os.getenv("OPENAI_MODEL", "gpt-5")
    effort = os.getenv("OPENAI_REASONING_EFFORT", "medium")
    response = client.responses.create(
        model=model,
        reasoning={"effort": effort},
        tools=[
            {
                "type": "web_search",
                "filters": {
                    "allowed_domains": [
                        "www.nature.com",
                        "nature.com",
                        "doi.org",
                        "orcid.org",
                        "github.com",
                        "zenodo.org",
                    ]
                },
            }
        ],
        input=build_prompt(sent_items, date_string),
    )
    data = extract_json(response.output_text)
    required = ["title", "doi", "url", "subject", "html"]
    missing = [key for key in required if not data.get(key)]
    if missing:
        raise ValueError(f"Model output missing required fields: {missing}")
    return data


def send_email(subject, html):
    username = os.environ["SMTP_USERNAME"]
    password = os.environ["SMTP_PASSWORD"]
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    sender = os.getenv("EMAIL_FROM", username)
    to_recipients = parse_recipients(os.getenv("EMAIL_TO", username))
    cc_recipients = parse_recipients(os.getenv("EMAIL_CC", ""))
    bcc_recipients = parse_recipients(os.getenv("EMAIL_BCC", ""))
    all_recipients = to_recipients + cc_recipients + bcc_recipients
    if not all_recipients:
        raise ValueError("At least one recipient is required in EMAIL_TO, EMAIL_CC, or EMAIL_BCC")

    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    if to_recipients:
        msg["To"] = ", ".join(to_recipients)
    if cc_recipients:
        msg["Cc"] = ", ".join(cc_recipients)

    context = ssl.create_default_context()
    with smtplib.SMTP(host, port) as server:
        server.starttls(context=context)
        server.login(username, password)
        server.sendmail(sender, all_recipients, msg.as_string())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    date_string = now.strftime("%Y-%m-%d")
    sent_data = load_sent_articles()
    sent_items = sent_data.setdefault("sent", [])

    email = generate_email(sent_items, date_string)
    if already_sent(email, sent_items):
        raise RuntimeError(
            f"Generated article was already sent: {email.get('title')} / {email.get('doi')}"
        )

    if args.dry_run:
        print(json.dumps(email, ensure_ascii=False, indent=2))
        return

    send_email(email["subject"], email["html"])
    sent_items.append(
        {
            "title": email["title"],
            "doi": email["doi"],
            "url": email["url"],
            "subject": email["subject"],
            "sent_at": now.isoformat(timespec="seconds"),
        }
    )
    save_sent_articles(sent_data)
    print(f"Sent: {email['subject']}")


if __name__ == "__main__":
    main()
