/**
 * 天枢 · 八字排盘(纯 JS 版)
 * 公历 → 农历 → 四柱干支 → 日主 → 五行 → 喜用神
 */

// ===== 农历数据(1900-2100) =====
// 每个数字编码 16 位二进制:高 4 位表示闰月月份,低 12 位表示每月大小(1=大 30 天,0=小 29 天)
const LUNAR_INFO = [
  0x04bd8,0x04ae0,0x0a570,0x054d5,0x0d260,0x0d950,0x16554,0x056a0,0x09ad0,0x055d2,//1900-1909
  0x04ae0,0x0a5b6,0x0a4d0,0x0d250,0x1d255,0x0b540,0x0d6a0,0x0ada2,0x095b0,0x14977,//1910-1919
  0x04970,0x0a4b0,0x0b4b5,0x06a50,0x06d40,0x1ab54,0x02b60,0x09570,0x052f2,0x04970,//1920-1929
  0x06566,0x0d4a0,0x0ea50,0x06e95,0x05ad0,0x02b60,0x186e3,0x092e0,0x1c8d7,0x0c950,//1930-1939
  0x0d4a0,0x1d8a6,0x0b550,0x056a0,0x1a5b4,0x025d0,0x092d0,0x0d2b2,0x0a950,0x0b557,//1940-1949
  0x06ca0,0x0b550,0x15355,0x04da0,0x0a5b0,0x14573,0x052b0,0x0a9a8,0x0e950,0x06aa0,//1950-1959
  0x0aea6,0x0ab50,0x04b60,0x0aae4,0x0a570,0x05260,0x0f263,0x0d950,0x05b57,0x056a0,//1960-1969
  0x096d0,0x04dd5,0x04ad0,0x0a4d0,0x0d4d4,0x0d250,0x0d558,0x0b540,0x0b6a0,0x195a6,//1970-1979
  0x095b0,0x049b0,0x0a974,0x0a4b0,0x0b27a,0x06a50,0x06d40,0x0af46,0x0ab60,0x09570,//1980-1989
  0x04af5,0x04970,0x064b0,0x074a3,0x0ea50,0x06b58,0x055c0,0x0ab60,0x096d5,0x092e0,//1990-1999
  0x0c960,0x0d954,0x0d4a0,0x0da50,0x07552,0x056a0,0x0abb7,0x025d0,0x092d0,0x0cab5,//2000-2009
  0x0a950,0x0b4a0,0x0baa4,0x0ad50,0x055d9,0x04ba0,0x0a5b0,0x15176,0x052b0,0x0a930,//2010-2019
  0x07954,0x06aa0,0x0ad50,0x05b52,0x04b60,0x0a6e6,0x0a4e0,0x0d260,0x0ea65,0x0d530,//2020-2029
  0x05aa0,0x076a3,0x096d0,0x04afb,0x04ad0,0x0a4d0,0x1d0b6,0x0d250,0x0d520,0x0dd45,//2030-2039
  0x0b5a0,0x056d0,0x055b2,0x049b0,0x0a577,0x0a4b0,0x0aa50,0x1b255,0x06d20,0x0ada0,//2040-2049
  0x14b63,0x09370,0x049f8,0x04970,0x064b0,0x168a6,0x0ea50,0x06b20,0x1a6c4,0x0aae0,//2050-2059
  0x0a2e0,0x0d2e3,0x0c960,0x0d557,0x0d4a0,0x0da50,0x05d55,0x056a0,0x0a6d0,0x055d4,//2060-2069
  0x052d0,0x0a9b8,0x0a950,0x0b4a0,0x0b6a6,0x0ad50,0x055a0,0x0aba4,0x0a5b0,0x052b0,//2070-2079
  0x0b273,0x06930,0x07337,0x06aa0,0x0ad50,0x14b55,0x04b60,0x0a570,0x054e4,0x0d160,//2080-2089
  0x0e968,0x0d520,0x0daa0,0x16aa6,0x056d0,0x04ae0,0x0a9d4,0x0a2d0,0x0d150,0x0f252,//2090-2099
  0x0d520 //2100
];

// 天干
const TIANGAN = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"];
// 地支
const DIZHI = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"];
// 农历月份名
const LUNAR_MONTH_NAMES = ["正","二","三","四","五","六","七","八","九","十","冬","腊"];
// 农历日期名(初一~三十)
const LUNAR_DAY_NAMES = [
  "初一","初二","初三","初四","初五","初六","初七","初八","初九","初十",
  "十一","十二","十三","十四","十五","十六","十七","十八","十九","二十",
  "廿一","廿二","廿三","廿四","廿五","廿六","廿七","廿八","廿九","三十"
];

// ===== 农历工具函数 =====

// 农历某年总天数
function lunarYearDays(year) {
  let sum = 348; // 12 * 29
  for (let i = 0x8000; i > 0x8; i >>= 1) {
    sum += (LUNAR_INFO[year-1900] & i) ? 1 : 0;
  }
  return sum + leapDays(year);
}

// 农历闰月月份(0 表示无闰月)
function leapMonth(year) {
  return LUNAR_INFO[year-1900] & 0xf;
}

// 农历闰月天数
function leapDays(year) {
  if (leapMonth(year)) {
    return (LUNAR_INFO[year-1900] & 0x10000) ? 30 : 29;
  }
  return 0;
}

// 农历某月天数
function monthDays(year, month) {
  return (LUNAR_INFO[year-1900] & (0x10000 >> month)) ? 30 : 29;
}

// 公历 → 农历
function solarToLunar(year, month, day) {
  if (year < 1900 || year > 2100) return null;
  // 1900-01-31 是农历 1900 年正月初一
  const baseDate = new Date(1900, 0, 31);
  const objDate = new Date(year, month - 1, day);
  let offset = Math.floor((objDate - baseDate) / 86400000);

  let lunarYear = 1900;
  let temp = 0;
  while (lunarYear < 2101 && offset > 0) {
    temp = lunarYearDays(lunarYear);
    if (offset < temp) break;
    offset -= temp;
    lunarYear++;
  }

  const leap = leapMonth(lunarYear);
  let isLeap = false;
  let lunarMonth = 1;
  while (lunarMonth < 13 && offset >= 0) {
    // 闰月
    if (leap > 0 && lunarMonth === leap + 1 && !isLeap) {
      --lunarMonth;
      isLeap = true;
      temp = leapDays(lunarYear);
    } else {
      temp = monthDays(lunarYear, lunarMonth);
    }
    if (isLeap && lunarMonth === leap + 1) {
      isLeap = false;
    }
    if (offset < temp) break;
    offset -= temp;
    lunarMonth++;
  }

  if (offset === 0 && leap > 0 && lunarMonth === leap + 1) {
    if (isLeap) {
      isLeap = false;
    } else {
      isLeap = true;
      --lunarMonth;
    }
  }
  if (offset < 0) {
    offset += temp;
    --lunarMonth;
  }

  const lunarDay = offset + 1;
  return { year: lunarYear, month: lunarMonth, day: lunarDay, isLeap };
}

// ===== 排盘函数 =====

// 天干五行
const TG_WUXING = {
  "甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土",
  "庚":"金","辛":"金","壬":"水","癸":"水"
};
// 地支五行
const DZ_WUXING = {
  "子":"水","亥":"水","寅":"木","卯":"木","巳":"火","午":"火",
  "申":"金","酉":"金","辰":"土","丑":"土","未":"土","戌":"土"
};

// 年柱(以立春为界简化处理:春节前后统一用农历年)
function yearPillar(lunarYear) {
  // 公元 4 年 = 甲子
  const idx = (lunarYear - 4) % 60;
  return TIANGAN[idx % 10] + DIZHI[idx % 12];
}

// 月柱 - 五虎遁年起月法
function monthPillar(yearTg, lunarMonth) {
  const yearToStart = {
    "甲":"丙","己":"丙","乙":"戊","庚":"戊","丙":"庚","辛":"庚",
    "丁":"壬","壬":"壬","戊":"甲","癸":"甲"
  };
  const start = yearToStart[yearTg];
  const idx = (TIANGAN.indexOf(start) + (lunarMonth - 1)) % 10;
  const base = ["寅","卯","辰","巳","午","未","申","酉","戌","亥","子","丑"];
  return TIANGAN[idx] + base[lunarMonth - 1];
}

// 日柱:1900-01-01 是甲戌(索引 10)
function dayPillar(solarDate) {
  const anchor = new Date(1900, 0, 1); // 注意:1900-01-01 是甲戌日
  const deltaDays = Math.floor((solarDate - anchor) / 86400000);
  const idx = (10 + deltaDays) % 60;
  return TIANGAN[idx % 10] + DIZHI[idx % 12];
}

// 时辰地支
function hourBranch(hour) {
  if (hour === 23 || hour === 0) return "子";
  return DIZHI[(hour + 1) / 2 | 0];
}

// 时柱 - 五鼠遁日起时法
function hourPillar(dayTg, hour) {
  const branch = hourBranch(hour);
  const dayToStart = {
    "甲":"甲","己":"甲","乙":"丙","庚":"丙","丙":"戊","辛":"戊",
    "丁":"庚","壬":"庚","戊":"壬","癸":"壬"
  };
  const start = dayToStart[dayTg];
  const branchIdx = DIZHI.indexOf(branch);
  const idx = (TIANGAN.indexOf(start) + branchIdx) % 10;
  return TIANGAN[idx] + branch;
}

// 性格特质(基于日主五行)
const WUXING_PERSONALITY = {
  "木": "仁慈、向上、条理分明、逻辑清晰,有成长型思维",
  "火": "热情、表达力强、行动力快,善于感染他人",
  "土": "稳重、包容、注重规则与执行,有强落地能力",
  "金": "刚毅、果断、追求精准与秩序,擅长结构化分析",
  "水": "灵活、智慧、善于变通,具备深度思考与适应力"
};
const WUXING_CAREER = {
  "木": "教育、文化、出版、设计、IT、互联网",
  "火": "传媒、新能源、电力、互联网运营、自媒体",
  "土": "建筑、房地产、农业、陶瓷、政府公共管理",
  "金": "金融、银行、证券、机械、硬件、芯片",
  "水": "物流、贸易、航运、水利、哲学研究"
};

// 主排盘函数
function getFourPillars(year, month, day, hour) {
  const solarDate = new Date(year, month - 1, day);
  const lunar = solarToLunar(year, month, day);
  if (!lunar) return { error: "年份超出支持范围(1900-2100)" };

  const yearTg = yearPillar(lunar.year).charAt(0);
  const yearDz = yearPillar(lunar.year).charAt(1);
  const monthP = monthPillar(yearTg, lunar.month);
  const dayP = dayPillar(solarDate);
  const dayTg = dayP.charAt(0);
  const hourP = hourPillar(dayTg, hour);

  // 五行统计
  const allTg = [yearTg, monthP.charAt(0), dayTg, hourP.charAt(0)];
  const allDz = [yearDz, monthP.charAt(1), dayP.charAt(1), hourP.charAt(1)];
  const wuxingCount = {"木":0,"火":0,"土":0,"金":0,"水":0};
  allTg.forEach(t => wuxingCount[TG_WUXING[t]]++);
  allDz.forEach(d => wuxingCount[DZ_WUXING[d]]++);

  const dayMaster = dayTg;
  const dayMasterWx = TG_WUXING[dayTg];

  // 喜用神
  const shengWo = {"木":"水","火":"木","土":"火","金":"土","水":"金"};
  const keWo = {"木":"金","火":"水","土":"木","金":"火","水":"土"};
  const xiZhong = [dayMasterWx, shengWo[dayMasterWx]];
  const jiZhong = [keWo[dayMasterWx]];

  // 最缺五行
  let minWx = "木", minCount = 99;
  for (const k in wuxingCount) {
    if (wuxingCount[k] < minCount) { minCount = wuxingCount[k]; minWx = k; }
  }

  return {
    solar: `${year}-${String(month).padStart(2,"0")}-${String(day).padStart(2,"0")} ${String(hour).padStart(2,"0")}:00`,
    lunar: `${lunar.year}年${LUNAR_MONTH_NAMES[lunar.month-1]}月${LUNAR_DAY_NAMES[lunar.day-1]}`,
    yearZhu: yearTg + yearDz,
    monthZhu: monthP,
    dayZhu: dayP,
    hourZhu: hourP,
    dayMaster: dayTg,
    dayMasterWx: dayMasterWx,
    wuxingCount: wuxingCount,
    minWx: minWx,
    xiZhong: xiZhong,
    jiZhong: jiZhong,
    personality: WUXING_PERSONALITY[dayMasterWx],
    careerFit: WUXING_CAREER[dayMasterWx]
  };
}

// 暴露到全局
if (typeof window !== "undefined") {
  window.TianShuBazi = { getFourPillars, solarToLunar };
}