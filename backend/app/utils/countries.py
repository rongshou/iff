VALID_COUNTRIES = {
    "英国", "美国", "澳大利亚", "加拿大", "中国香港", "新加坡",
    "日本", "韩国", "新西兰", "爱尔兰", "中国澳门",
    "德国", "法国", "荷兰", "瑞士", "瑞典", "丹麦",
    "意大利", "西班牙", "俄罗斯", "马来西亚", "泰国",
    "比利时", "奥地利", "芬兰", "挪威", "葡萄牙",
    "捷克", "波兰", "希腊",
}

COUNTRY_ALIAS = {
    "香港": ["香港", "HK", "中国香港"],
    "英国": ["英国", "UK"],
    "美国": ["美国", "US", "USA"],
    "澳大利亚": ["澳大利亚", "AU", "澳洲"],
    "加拿大": ["加拿大", "CA"],
    "新加坡": ["新加坡", "SG"],
    "日本": ["日本", "JP"],
    "德国": ["德国", "DE", "Germany"],
    "韩国": ["韩国", "KR"],
    "新西兰": ["新西兰", "NZ"],
    "法国": ["法国", "FR", "France"],
    "荷兰": ["荷兰", "NL", "Netherlands"],
    "意大利": ["意大利", "IT", "Italy"],
    "中国澳门": ["澳门", "MO", "中国澳门"],
    "马来西亚": ["马来西亚", "MY"],
    "爱尔兰": ["爱尔兰", "IE"],
    "瑞士": ["瑞士", "CH"],
    "瑞典": ["瑞典", "SE"],
    "丹麦": ["丹麦", "DK"],
    "西班牙": ["西班牙", "ES"],
    "俄罗斯": ["俄罗斯", "RU"],
    "比利时": ["比利时", "BE"],
    "奥地利": ["奥地利", "AT"],
    "芬兰": ["芬兰", "FI"],
    "挪威": ["挪威", "NO"],
    "葡萄牙": ["葡萄牙", "PT"],
    "捷克": ["捷克", "CZ"],
    "波兰": ["波兰", "PL"],
    "希腊": ["希腊", "GR"],
}

STUDY_LEVELS = ["本科", "硕士", "博士"]


def expand_countries(country_list: list[str]) -> list[str]:
    expanded = list(country_list)
    for c in country_list:
        for canonical, aliases in COUNTRY_ALIAS.items():
            if c in aliases or c == canonical:
                for a in aliases:
                    if a not in expanded:
                        expanded.append(a)
                break
    return expanded


def validate_countries(country_list: list[str]) -> list[str]:
    return [c for c in country_list if c not in VALID_COUNTRIES]
