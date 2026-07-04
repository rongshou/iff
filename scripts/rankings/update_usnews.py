#!/usr/bin/env python3
"""Update usnews_rank in advisor.db from collected univ_data.json"""

import json
import sqlite3
import re

# Load new US News data
with open('/home/admin/univ_data.json') as f:
    new_data = json.load(f)

# Build English name → rank map
new_rank = {}
for u in new_data:
    r = u.get('global_rank')
    if r:
        new_rank[u['name'].lower().strip()] = r

print(f"New data: {len(new_rank)} ranked universities")

# Comprehensive Chinese → English name mapping
cn_en_map = {
    "哈佛大学": "Harvard University",
    "麻省理工学院": "Massachusetts Institute of Technology",
    "斯坦福大学": "Stanford University",
    "牛津大学": "University of Oxford",
    "剑桥大学": "University of Cambridge",
    "清华大学": "Tsinghua University",
    "加州大学伯克利分校": "University of California--Berkeley",
    "耶鲁大学": "Yale University",
    "伦敦大学学院": "University College London",
    "哥伦比亚大学": "Columbia University",
    "加州大学洛杉矶分校": "University of California--Los Angeles",
    "华盛顿大学": "University of Washington",
    "康奈尔大学": "Cornell University",
    "伦敦帝国学院": "Imperial College London",
    "普林斯顿大学": "Princeton University",
    "新加坡国立大学": "National University of Singapore",
    "约翰斯·霍普金斯大学": "Johns Hopkins University",
    "宾夕法尼亚大学": "University of Pennsylvania",
    "北京大学": "Peking University",
    "多伦多大学": "University of Toronto",
    "密歇根大学安娜堡分校": "University of Michigan--Ann Arbor",
    "密歇根大学": "University of Michigan--Ann Arbor",
    "加州大学旧金山分校": "University of California--San Francisco",
    "加州理工学院": "California Institute of Technology",
    "加州大学圣地亚哥分校": "University of California--San Diego",
    "芝加哥大学": "University of Chicago",
    "西北大学": "Northwestern University",
    "南洋理工大学": "Nanyang Technological University",
    "香港中文大学": "Chinese University Hong Kong",
    "墨尔本大学": "University of Melbourne",
    "杜克大学": "Duke University",
    "悉尼大学": "University of Sydney",
    "圣路易斯华盛顿大学": "Washington University in St. Louis",
    "苏黎世联邦理工学院": "Swiss Federal Institute of Technology Zurich",
    "新南威尔士大学": "University of New South Wales",
    "浙江大学": "Zhejiang University",
    "纽约大学": "New York University",
    "上海交通大学": "Shanghai Jiao Tong University",
    "莫纳什大学": "Monash University",
    "阿姆斯特丹大学": "University of Amsterdam",
    "香港大学": "University of Hong Kong",
    "爱丁堡大学": "University of Edinburgh",
    "伦敦国王学院": "King's College London",
    "不列颠哥伦比亚大学": "University of British Columbia",
    "昆士兰大学": "University of Queensland Australia",
    "哥本哈根大学": "University of Copenhagen",
    "香港城市大学": "City University Hong Kong",
    "鲁汶大学": "KU Leuven",
    "复旦大学": "Fudan University",
    "慕尼黑大学": "University of Munich",
    "香港理工大学": "Hong Kong Polytechnic University",
    "中国科学院大学": "University of Chinese Academy of Sciences",
    "乌得勒支大学": "Utrecht University",
    "北卡罗来纳大学教堂山分校": "University of North Carolina--Chapel Hill",
    "德克萨斯大学奥斯汀分校": "University of Texas--Austin",
    "卡罗林斯卡学院": "Karolinska Institute",
    "匹兹堡大学": "University of Pittsburgh",
    "中国科学技术大学": "University of Science & Technology of China, CAS",
    "威斯康星大学麦迪逊分校": "University of Wisconsin--Madison",
    "莱顿大学": "Leiden University",
    "巴黎大学": "Université de Paris",
    "柏林自由大学": "Freie Universität Berlin",
    "埃默里大学": "Emory University",
    "俄亥俄州立大学": "Ohio State University--Columbus",
    "苏黎世大学": "University of Zurich",
    "索邦大学": "Sorbonne Universite",
    "海德堡大学": "Heidelberg University",
    "麦吉尔大学": "McGill University",
    "曼彻斯特大学": "University of Manchester",
    "范德比尔特大学": "Vanderbilt University",
    "东京大学": "University of Tokyo",
    "慕尼黑工业大学": "Technical University of Munich",
    "中山大学": "Sun Yat-sen University",
    "南加州大学": "University of Southern California",
    "明尼苏达大学双城分校": "University of Minnesota--Twin Cities",
    "南京大学": "Nanjing University",
    "格拉斯哥大学": "University of Glasgow",
    "格罗宁根大学": "University of Groningen",
    "澳洲国立大学": "Australian National University",
    "香港科技大学": "Hong Kong University of Science and Technology",
    "巴黎萨克雷大学": "Universite Paris Saclay",
    "马里兰大学帕克分校": "University of Maryland--College Park",
    "阿德莱德大学": "Adelaide University",
    "悉尼科技大学": "University of Technology Sydney",
    "武汉大学": "Wuhan University",
    "巴塞罗那大学": "University of Barcelona",
    "鹿特丹伊拉斯姆斯大学": "Erasmus University Rotterdam",
    "西澳大学": "University of Western Australia",
    "加州大学圣克鲁兹分校": "University of California--Santa Cruz",
    "迪肯大学": "Deakin University",
    "拉德堡德大学": "Radboud University Nijmegen",
    "贝勒医学院": "Baylor College of Medicine",
    "布朗大学": "Brown University",
    "南开大学": "Nankai University",
    "汉堡大学": "University of Hamburg",
    "利兹大学": "University of Leeds",
    "乌普萨拉大学": "Uppsala University",
    "麦克马斯特大学": "McMaster University",
    "米兰大学": "University of Milan",
    "京都大学": "Kyoto University",
    "华南理工大学": "South China University of Technology",
    "斯威本科技大学": "Swinburne University of Technology",
    "阿尔伯塔大学": "University of Alberta",
    "深圳大学": "Shenzhen University",
    "天津大学": "Tianjin University",
    "莱斯特大学": "University of Leicester",
    "利物浦大学": "University of Liverpool",
    "代尔夫特理工大学": "Delft University of Technology",
    "犹他大学": "University of Utah",
    "昆士兰科技大学": "Queensland University of Technology",
    "麦考瑞大学": "Macquarie University",
    "皇家墨尔本理工大学": "RMIT University",
    "帕多瓦大学": "University of Padua",
    "厦门大学": "Xiamen University",
    "德州农工大学": "Texas A&M University--College Station",
    "哥德堡大学": "University of Gothenburg",
    "亚利桑那州立大学": "Arizona State University--Tempe",
    "波恩大学": "University of Bonn",
    "巴塞尔大学": "University of Basel",
    "中国农业大学": "China Agricultural University",
    "蒂宾根大学": "Eberhard Karls University, Tübingen",
    "斯德哥尔摩大学": "Stockholm University",
    "特拉维夫大学": "Tel Aviv University",
    "科罗拉多大学安舒茨医学校区": "University of Colorado Anschutz Medical Campus",
    "蒙特利尔大学": "University of Montreal",
    "维也纳大学": "University of Vienna",
    "滑铁卢大学": "University of Waterloo",
    "华威大学": "University of Warwick",
    "贝尔法斯特女王大学": "Queen's University Belfast",
    "纽卡斯尔大学": "University of Newcastle",
    "西悉尼大学": "Western Sydney University",
    "成均馆大学": "Sungkyunkwan University",
    "韩国科学技术院": "Korea Advanced Institute of Science and Technology",
    "里斯本大学": "University of Lisbon",
    "艾克斯-马赛大学": "University of Aix-Marseille",
    "沙迦大学": "University of Sharjah",
    "皇家理工学院": "Royal Institute of Technology",
    "爱荷华大学": "University of Iowa",
    "乌得勒支大学": "Utrecht University",
    "埃尔朗根-纽伦堡大学": "Friedrich-Alexander-Universität Erlangen-Nürnberg",
    "卡尔斯鲁厄理工学院": "Karlsruhe Institute of Technology",
    "亚琛工业大学": "RWTH Aachen University",
    "华沙大学": "University of Warsaw",
    "马德里自治大学": "Universidad Autónoma de Madrid",
    "巴塞罗那自治大学": "Universitat Autònoma de Barcelona",
    "隆德大学": "Lund University",
    "奥胡斯大学": "Aarhus University",
    "赫尔辛基大学": "University of Helsinki",
    "奥克兰大学": "University of Auckland",
    "阿德莱德大学": "Adelaide University",
}

# Connect to DB
conn = sqlite3.connect('/home/admin/tianquan/backend/data/advisor.db')
cur = conn.cursor()

# Get all DB universities
all_db = cur.execute('SELECT id, name, usnews_rank FROM universities').fetchall()
print(f"DB total: {len(all_db)} universities")

# Count existing non-zero usnews_rank
existing_nonzero = sum(1 for r in all_db if r[2] and r[2] > 0)
print(f"DB with existing usnews_rank > 0: {existing_nonzero}")

matched = []
unmatched_json = []
unmatched_cn = []

# Match via cn_en_map
seen_ids = set()
for cn_name, en_name in cn_en_map.items():
    en_key = en_name.lower().strip()
    if en_key in new_rank:
        row = cur.execute('SELECT id, usnews_rank FROM universities WHERE name = ?', (cn_name,)).fetchone()
        if row:
            matched.append((row[0], cn_name, en_name, new_rank[en_key], row[1]))
            seen_ids.add(row[0])

# Try fuzzy matching for remaining JSON entries
matched_en_names = {cn_en_map.get(cn, '').lower() for cn in cn_en_map}
for en_name, rank in new_rank.items():
    if en_name in matched_en_names:
        continue
    # Try to find by partial name match
    found = False
    for db_id, db_name, _ in all_db:
        if db_id in seen_ids:
            continue
        # Check if English name parts appear in DB name
        en_parts = en_name.replace('--', ' ').replace('-', ' ').lower().split()
        db_lower = db_name.lower()
        # Try matching key parts
        key_words = [w for w in en_parts if len(w) > 3]
        if len(key_words) >= 2 and all(kw in db_lower for kw in key_words):
            matched.append((db_id, db_name, en_name, rank, None))
            seen_ids.add(db_id)
            found = True
            break
    if not found:
        unmatched_json.append((en_name, rank))

# Report
print(f"\n=== Update Summary ===")
print(f"Matched & to update: {len(matched)}")

changes = 0
same = 0
cur.execute('BEGIN')
for db_id, cn_name, en_name, new_val, old_val in matched:
    if old_val != new_val:
        cur.execute('UPDATE universities SET usnews_rank = ? WHERE id = ?', (new_val, db_id))
        changes += 1
    else:
        same += 1
cur.execute('COMMIT')

print(f"Updated: {changes}")
print(f"Already same: {same}")

if unmatched_json:
    print(f"\nUnmatched in JSON (no DB match found): {len(unmatched_json)}")
    for name, rank in sorted(unmatched_json, key=lambda x: x[1])[:20]:
        print(f"  #{rank} {name}")

conn.close()
print("\nDone!")
