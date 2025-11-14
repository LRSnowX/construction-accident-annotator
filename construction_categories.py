"""GB/T 4754-2017 建筑业（E门类 47-50）完整分类树
严格按照GB-T4757-2017.md文件整理
"""

# 完整的4级分类树：代码 -> 名称
import re

from construction_keywords import GB_CONSTRUCTION_KEYWORDS

GB_CONSTRUCTION_TREE = {
    # 47 房屋建筑业
    "4710": "住宅房屋建筑",
    "4720": "体育场馆建筑",
    "4790": "其他房屋建筑业",
    # 48 土木工程建筑业
    # 481 铁路、道路、隧道和桥梁工程建筑
    "4811": "铁路工程建筑",
    "4812": "公路工程建筑",
    "4813": "市政道路工程建筑",
    "4814": "城市轨道交通工程建筑",
    "4819": "其他道路、隧道和桥梁工程建筑",
    # 482 水利和水运工程建筑
    "4821": "水源及供水设施工程建筑",
    "4822": "河湖治理及防洪设施工程建筑",
    "4823": "港口及航运设施工程建筑",
    # 483 海洋工程建筑
    "4831": "海洋油气资源开发利用工程建筑",
    "4832": "海洋能源开发利用工程建筑",
    "4833": "海底隧道工程建筑",
    "4834": "海底设施铺设工程建筑",
    "4839": "其他海洋工程建筑",
    # 484 工矿工程建筑
    "4840": "工矿工程建筑",
    # 485 架线和管道工程建筑
    "4851": "架线及设备工程建筑",
    "4852": "管道工程建筑",
    "4853": "地下综合管廊工程建筑",
    # 486 节能环保工程施工
    "4861": "节能工程施工",
    "4862": "环保工程施工",
    "4863": "生态保护工程施工",
    # 487 电力工程施工
    "4871": "火力发电工程施工",
    "4872": "水力发电工程施工",
    "4873": "核电工程施工",
    "4874": "风能发电工程施工",
    "4875": "太阳能发电工程施工",
    "4879": "其他电力工程施工",
    # 489 其他土木工程建筑
    "4891": "园林绿化工程施工",
    "4892": "体育场地设施工程施工",
    "4893": "游乐设施工程施工",
    "4899": "其他土木工程建筑施工",
    # 49 建筑安装业
    "4910": "电气安装",
    "4920": "管道和设备安装",
    # 499 其他建筑安装业
    "4991": "体育场地设施安装",
    "4999": "其他建筑安装",
    # 50 建筑装饰、装修和其他建筑业
    # 501 建筑装饰和装修业
    "5011": "公共建筑装饰和装修",
    "5012": "住宅装饰和装修",
    "5013": "建筑幕墙装饰和装修",
    # 502 建筑物拆除和场地准备活动
    "5021": "建筑物拆除活动",
    "5022": "场地准备活动",
    "5030": "提供施工设备服务",
    "5090": "其他未列明建筑业",
}


# 3级分类（中类）：代码前3位 -> 名称
GB_CONSTRUCTION_MID = {
    "471": "房屋建筑业",
    "472": "房屋建筑业",
    "479": "房屋建筑业",
    "481": "铁路、道路、隧道和桥梁工程建筑",
    "482": "水利和水运工程建筑",
    "483": "海洋工程建筑",
    "484": "工矿工程建筑",
    "485": "架线和管道工程建筑",
    "486": "节能环保工程施工",
    "487": "电力工程施工",
    "489": "其他土木工程建筑",
    "491": "电气安装",
    "492": "管道和设备安装",
    "499": "其他建筑安装业",
    "501": "建筑装饰和装修业",
    "502": "建筑物拆除和场地准备活动",
    "503": "提供施工设备服务",
    "509": "其他未列明建筑业",
}


# 2级分类（大类）：代码前2位 -> 名称
GB_CONSTRUCTION_MAJOR = {
    "47": "房屋建筑业",
    "48": "土木工程建筑业",
    "49": "建筑安装业",
    "50": "建筑装饰、装修和其他建筑业",
}


def get_category_info(code: str) -> dict:
    """
    根据4位代码获取完整分类信息

    Args:
        code: 4位分类代码，如 "4811"

    Returns:
        {
            "code": "4811",
            "name": "铁路工程建筑",
            "major_code": "48",
            "major_name": "土木工程建筑业",
            "mid_code": "481",
            "mid_name": "铁路、道路、隧道和桥梁工程建筑"
        }
    """
    if not code or len(code) != 4:
        return None

    code = str(code)
    name = GB_CONSTRUCTION_TREE.get(code)

    if not name:
        return None

    major_code = code[:2]
    mid_code = code[:3]

    return {
        "code": code,
        "name": name,
        "major_code": major_code,
        "major_name": GB_CONSTRUCTION_MAJOR.get(major_code, "未知"),
        "mid_code": mid_code,
        "mid_name": GB_CONSTRUCTION_MID.get(mid_code, "未知"),
    }


def is_valid_construction_code(code: str) -> bool:
    """检查是否为有效的建筑业分类代码"""
    return code in GB_CONSTRUCTION_TREE


def suggest_codes_from_text(text: str, top_n: int = 5):
    """根据输入文本，使用关键词匹配产生候选4位分类代码。

    返回列表：[(code, name, score), ...]，按 score 降序排序。
    """
    if not text:
        return []

    # 简单归一化，移除空白字符
    text_norm = re.sub(r"[\s\u3000]+", "", str(text))
    scores = {}  # 使用字典来累加每个code的分数

    for code, kws in GB_CONSTRUCTION_KEYWORDS.items():
        score = 0
        for kw in kws:
            if not kw:
                continue
            # 计数关键词在文本中出现的次数，长关键词权重更高
            cnt = text_norm.count(kw)
            if cnt > 0:
                score += len(kw) * cnt

        if score > 0:
            scores[code] = scores.get(code, 0) + score

    if not scores:
        return []

    # 将字典转换为 (code, score) 元组列表
    ranked_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)

    # 构建最终返回结果
    suggestions = []
    for code, score in ranked_scores[:top_n]:
        suggestions.append((code, GB_CONSTRUCTION_TREE.get(code, ""), float(score)))

    return suggestions
