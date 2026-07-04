#!/usr/bin/env python3
"""Compare DB qs_rank vs QS 2027 rankings"""

import sqlite3

# QS World University Rankings 2027 (top 50+)
QS_2027 = {
    "Massachusetts Institute of Technology": 1,
    "Imperial College London": 2,
    "Stanford University": 2,
    "University of Oxford": 4,
    "Harvard University": 5,
    "University of Cambridge": 6,
    "California Institute of Technology": 7,
    "ETH Zurich": 8,
    "University College London": 8,
    "National University of Singapore": 10,
    "University of Hong Kong": 11,
    "Nanyang Technological University": 12,
    "Peking University": 13,
    "Tsinghua University": 14,
    "University of Pennsylvania": 15,
    "Yale University": 16,
    "Chinese University of Hong Kong": 17,
    "University of New South Wales": 18,
    "Johns Hopkins University": 19,
    "University of California--Berkeley": 20,
    "EPFL": 21,
    "University of Melbourne": 22,
    "University of Chicago": 24,
    "Technical University of Munich": 25,
    "University of California--Los Angeles": 27,
    "Fudan University": 28,
    "University of Sydney": 29,
    "Australian National University": 30,
    "McGill University": 31,
    "Monash University": 32,
    "University of Toronto": 33,
    "Hong Kong University of Science and Technology": 34,
    "University of Edinburgh": 35,
    "Shanghai Jiao Tong University": 36,
    "King's College London": 37,
    "Seoul National University": 38,
    "University of Tokyo": 39,
    "University of Manchester": 40,
    "University of Queensland": 41,
    "Yonsei University": 42,
    "Institut Polytechnique de Paris": 43,
    "Northwestern University": 44,
    "University of British Columbia": 45,
    "Zhejiang University": 46,
    "Delft University of Technology": 47,
    "Hong Kong Polytechnic University": 48,
    "University of Michigan--Ann Arbor": 49,
    "City University of Hong Kong": 52,
    "National Taiwan University": 52,
    "Carnegie Mellon University": 54,
    "University of Bristol": 56,
    "New York University": 57,
    "University of Amsterdam": 58,
    "Ludwig Maximilian University of Munich": 59,
    "London School of Economics": 60,
    "Kyoto University": 62,
    "University of Auckland": 63,
    "University of Warwick": 64,
    "University of Birmingham": 65,
    "University of Texas at Austin": 67,
    "Sorbonne University": 68,
    "University of Illinois--Urbana-Champaign": 69,
    "Université Paris-Saclay": 70,
    "University of Western Australia": 71,
    "University of California--San Diego": 72,
    "KTH Royal Institute of Technology": 73,
    "Nanjing University": 74,
    "Pennsylvania State University": 75,
    "University of Zurich": 76,
    "Purdue University": 77,
    "University of Washington": 78,
    "University of Nottingham": 79,
    "University of Adelaide": 80,
    "RMIT University": 122,  # approximate
}

# Chinese name -> English name mapping (same as before)
cn_en = {
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
    "香港中文大学": "Chinese University of Hong Kong",
    "墨尔本大学": "University of Melbourne",
    "杜克大学": "Duke University",
    "悉尼大学": "University of Sydney",
    "圣路易斯华盛顿大学": "Washington University in St. Louis",
    "苏黎世联邦理工学院": "ETH Zurich",
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
    "昆士兰大学": "University of Queensland",
    "哥本哈根大学": "University of Copenhagen",
    "香港城市大学": "City University of Hong Kong",
    "鲁汶大学": "KU Leuven",
    "复旦大学": "Fudan University",
    "慕尼黑大学": "Ludwig Maximilian University of Munich",
    "香港理工大学": "Hong Kong Polytechnic University",
    "中国科学院大学": "University of Chinese Academy of Sciences",
    "乌得勒支大学": "Utrecht University",
    "北卡罗来纳大学教堂山分校": "University of North Carolina--Chapel Hill",
    "德克萨斯大学奥斯汀分校": "University of Texas at Austin",
    "卡罗林斯卡学院": "Karolinska Institute",
    "匹兹堡大学": "University of Pittsburgh",
    "中国科学技术大学": "University of Science & Technology of China",
    "威斯康星大学麦迪逊分校": "University of Wisconsin--Madison",
    "莱顿大学": "Leiden University",
    "巴黎大学": "Université de Paris",
    "柏林自由大学": "Freie Universität Berlin",
    "埃默里大学": "Emory University",
    "俄亥俄州立大学": "Ohio State University--Columbus",
    "苏黎世大学": "University of Zurich",
    "索邦大学": "Sorbonne University",
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
    "巴黎萨克雷大学": "Université Paris-Saclay",
    "马里兰大学帕克分校": "University of Maryland--College Park",
    "阿德莱德大学": "University of Adelaide",
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
    "皇家理工学院": "KTH Royal Institute of Technology",
    "爱荷华大学": "University of Iowa",
    "伊利诺伊大学厄巴纳-香槟分校": "University of Illinois--Urbana-Champaign",
    "卡内基梅隆大学": "Carnegie Mellon University",
    "布里斯托大学": "University of Bristol",
    "伦敦政治经济学院": "London School of Economics",
    "奥克兰大学": "University of Auckland",
    "伯明翰大学": "University of Birmingham",
    "诺丁汉大学": "University of Nottingham",
    "普渡大学": "Purdue University",
    "宾州州立大学": "Pennsylvania State University",
    "宾夕法尼亚州立大学": "Pennsylvania State University",
}

conn = sqlite3.connect('/home/admin/tianquan/backend/data/advisor.db')

print("=" * 100)
print("QS 2027 vs DB 当前 qs_rank 对比")
print("=" * 100)
print(f"{'中文名':<20} {'英文名':<35} {'QS2027':>8} {'DB当前':>8} {'变化':>6}")
print("-" * 100)

changes = []
no_change = []
not_in_db = []
db_no_rank = []

for cn_name, en_name in sorted(cn_en.items(), key=lambda x: QS_2027.get(x[1], 9999)):
    if en_name not in QS_2027:
        continue
    new_rank = QS_2027[en_name]
    
    row = conn.execute('SELECT qs_rank FROM universities WHERE name = ?', (cn_name,)).fetchone()
    if not row:
        not_in_db.append((cn_name, en_name, new_rank))
        continue
    
    old_rank = row[0]
    if old_rank is None or old_rank == 0:
        db_no_rank.append((cn_name, en_name, new_rank))
        continue
    
    diff = old_rank - new_rank  # positive = improved
    if old_rank != new_rank:
        changes.append((cn_name, en_name, new_rank, old_rank, diff))
        arrow = "↑" if diff > 0 else "↓"
        print(f"{cn_name:<20} {en_name:<35} {new_rank:>8} {old_rank:>8} {arrow}{abs(diff):>3}")
    else:
        no_change.append((cn_name, en_name, new_rank))

print("-" * 100)
print(f"\n== 总结 ==")
print(f"有变化: {len(changes)}")
print(f"无变化: {len(no_change)}")
print(f"DB中无此学校: {len(not_in_db)}")
print(f"DB中无排名: {len(db_no_rank)}")

if changes:
    print(f"\n== 变化明细 (按降幅排序) ==")
    changes_sorted = sorted(changes, key=lambda x: x[4], reverse=True)
    print(f"{'中文名':<20} {'英文名':<35} {'QS2027':>8} {'DB当前':>8} {'变化值':>6}")
    print("-" * 100)
    for cn_name, en_name, new_rank, old_rank, diff in changes_sorted:
        arrow = "↑" if diff > 0 else "↓"
        print(f"{cn_name:<20} {en_name:<35} {new_rank:>8} {old_rank:>8} {arrow}{abs(diff):>3}")

conn.close()
