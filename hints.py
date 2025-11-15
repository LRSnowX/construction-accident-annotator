import json
import re
from collections import defaultdict
from copy import deepcopy
from math import exp, log, sqrt
from pathlib import Path
from typing import Dict, List, Set, Tuple

import ahocorasick  # type: ignore
import jieba  # type: ignore

# 轻量在线逻辑回归模型（非建筑业=1，建筑业=0）
# 特征为关键词存在与否（0/1）

DEFAULT_BIAS = 0.0
LEARNING_RATE = 0.2

# 自学习关键词参数
ALPHA = 1.0  # 平滑
MIN_COUNT = 6  # 最小出现次数（总计）
ABS_LOG_ODDS_THRESH = 1.0  # |log((pos+α)/(neg+α))| 阈值
MAX_TOKEN_LENGTH = 20


FEATURE_GROUPS = {
    # 非建筑业强特征：海事/船舶
    "ship": [
        "船舶",
        "渔船",
        "货轮",
        "客轮",
        "轮船",
        "船员",
        "船长",
        "船只",
        "海事",
        "海上",
        "航道",
        "航行",
        "锚地",
        "港口",
        "海域",
        "碰撞",
        "机舱",
    ],
    # 非建筑业强特征：道路/铁路交通
    "traffic": [
        "交通事故",
        "车辆",
        "轿车",
        "公交",
        "卡车",
        "高速",
        "路口",
        "驾驶员",
        "乘客",
        "追尾",
        "侧翻",
        "车祸",
        "列车",
        "铁路",
        "火车",
        "地铁",
    ],
    # 非建筑业强特征：矿山
    "mining": [
        "煤矿",
        "矿井",
        "采区",
        "井下",
        "巷道",
        "掘进",
        "顶板",
        "矿山",
    ],
    # 非建筑业强特征：化工/危化
    "chemical": [
        "化工",
        "危化",
        "危险化学品",
        "泄漏",
        "有毒",
        "罐体",
        "槽罐车",
        "爆燃",
        "中毒",
    ],
    # 建筑业正特征：出现则更可能是建筑业（对“非建筑业”概率起负向作用）
    "construction": [
        "施工",
        "工地",
        "塔吊",
        "脚手架",
        "混凝土",
        "浇筑",
        "吊装",
        "模板",
        "基坑",
        "起重",
        "施工现场",
        "班组",
        "钢筋",
        "桩基",
        "桥梁施工",
        "隧道施工",
        "防护棚",
    ],
}

# 初始化权重（对“非建筑业=1”的倾向）
# 非建筑业组：正权重；建筑业组：负权重
DEFAULT_WEIGHTS = {
    f: 1.5
    for f in (
        FEATURE_GROUPS["ship"]
        + FEATURE_GROUPS["traffic"]
        + FEATURE_GROUPS["mining"]
        + FEATURE_GROUPS["chemical"]
    )
}
DEFAULT_WEIGHTS.update({f: -2.0 for f in FEATURE_GROUPS["construction"]})


def _project_root() -> Path:
    # 本文件位于项目根目录
    return Path(__file__).resolve().parent


def _seed_config_path() -> Path:
    return _project_root() / "data" / "config" / "keyword_seeds.json"


BUILTIN_GROUPS = deepcopy(FEATURE_GROUPS)
BUILTIN_DEFAULT_WEIGHTS = deepcopy(DEFAULT_WEIGHTS)


# 供主程序打印的合并摘要
SEED_LOAD_SUMMARY = {
    "mode": "merge",
    "seeds_groups": 0,
    "seeds_weights": 0,
    "final_features": 0,
    "tokenizer": "jieba",
    "tokenizer_effective": "jieba",
}


# ---------------- 分词资源与分词器 ----------------
_STOPWORDS: Set[str] = {
    "事故",
    "发生",
    "经过",
    "情况",
    "有关",
    "人员",
    "责任",
    "公司",
    "单位",
    "作业",
    "安全",
    "管理",
    "报告",
    "造成",
    "受伤",
    "死亡",
    "调查",
    "建议",
    "目前",
    "当场",
    "现场",
    "处理",
    "部门",
    "年",
    "月",
    "日",
    "时",
    "分",
    "某",
    "该",
    "本",
    "等",
    "以及",
    "并",
    "对",
    "中",
}


def _tokenizer_resources_dir() -> Path:
    return _project_root() / "data" / "config"


def _init_tokenizer_resources():
    # 扩展停用词
    sw = _tokenizer_resources_dir() / "stopwords.txt"
    if sw.exists():
        try:
            with open(sw, "r", encoding="utf-8") as f:
                for line in f:
                    s = line.strip()
                    if s:
                        _STOPWORDS.add(s)
        except Exception:
            pass
    # 加载用户词典
    ud = _tokenizer_resources_dir() / "user_dict.txt"
    if ud.exists():
        try:
            jieba.load_userdict(str(ud))
        except Exception:
            pass


# ---------------- AC 自动机（关键词匹配） ----------------
_AC = None
_AC_KEYMAP: Dict[str, str] = {}


def _all_feature_keys() -> Set[str]:
    # 使用 DEFAULT_WEIGHTS 的键覆盖所有内置/外置/学习特征
    return set(DEFAULT_WEIGHTS.keys()).union(
        FEATURE_GROUPS.get("_learned", []), FEATURE_GROUPS.get("_custom", [])
    )


def _rebuild_automaton():
    global _AC, _AC_KEYMAP
    A = ahocorasick.Automaton()
    keymap: Dict[str, str] = {}
    for k in _all_feature_keys():
        kl = str(k).lower()
        if not kl:
            continue
        if kl not in keymap:
            keymap[kl] = k
        A.add_word(kl, kl)  # 存 lower 值作为 payload
    A.make_automaton()
    _AC = A
    _AC_KEYMAP = keymap


def _merge_seeds_into_defaults():
    path = _seed_config_path()
    if not path.exists():
        # 无外置配置，统计基于内置
        SEED_LOAD_SUMMARY.update(
            {
                "mode": "builtin-only",
                "seeds_groups": 0,
                "seeds_weights": 0,
                "final_features": len(DEFAULT_WEIGHTS),
            }
        )
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        SEED_LOAD_SUMMARY.update(
            {
                "mode": "load-error",
                "seeds_groups": 0,
                "seeds_weights": 0,
                "final_features": len(DEFAULT_WEIGHTS),
                "tokenizer": "jieba",
                "tokenizer_effective": "jieba",
            }
        )
        return

    groups = data.get("groups", {}) or {}
    weights_override = data.get("weights", {}) or {}
    mode = str(data.get("mode", "merge")).lower()

    # mode: replace -> 外置作为唯一真相，重置分组与默认权重
    if mode == "replace":
        FEATURE_GROUPS.clear()
        DEFAULT_WEIGHTS.clear()
        # 也允许回退到极简：若外置为空，则使用内置
        if not groups and not weights_override:
            FEATURE_GROUPS.update(deepcopy(BUILTIN_GROUPS))
            DEFAULT_WEIGHTS.update(deepcopy(BUILTIN_DEFAULT_WEIGHTS))
            mode = "replace-empty-fallback"

    # 合并分组关键词（去重）
    for group_name, key_list in groups.items():
        if not isinstance(key_list, list):
            continue
        existing = set(FEATURE_GROUPS.get(group_name, []))
        for k in key_list:
            try:
                k_l = str(k).strip()
            except Exception:
                continue
            if not k_l:
                continue
            existing.add(k_l)
        FEATURE_GROUPS[group_name] = sorted(existing)

    # 将分组新增的关键词赋默认权重
    for group_name, key_list in FEATURE_GROUPS.items():
        for k in key_list:
            if k not in DEFAULT_WEIGHTS:
                if group_name == "construction":
                    DEFAULT_WEIGHTS[k] = -2.0
                else:
                    DEFAULT_WEIGHTS[k] = 1.5

    # 自定义权重：也将这些词加入到特征组，避免只在权重里但无法被提取
    if weights_override:
        custom = set(FEATURE_GROUPS.get("_custom", []))
        for k, w in weights_override.items():
            try:
                k_l = str(k).strip()
                w_f = float(w)
            except Exception:
                continue
            if not k_l:
                continue
            DEFAULT_WEIGHTS[k_l] = w_f
            custom.add(k_l)
        FEATURE_GROUPS["_custom"] = sorted(custom)

    SEED_LOAD_SUMMARY.update(
        {
            "mode": mode,
            "seeds_groups": sum(len(v) for v in groups.values()) if groups else 0,
            "seeds_weights": len(weights_override),
            "final_features": len(DEFAULT_WEIGHTS),
            "tokenizer": "jieba",
            "tokenizer_effective": "jieba",
        }
    )
    # 初始化分词资源（固定使用 jieba）
    _init_tokenizer_resources()
    # 构建关键词 AC 自动机
    _rebuild_automaton()


# 在模块导入时合并外置种子
_merge_seeds_into_defaults()


def get_seed_load_summary() -> str:
    m = SEED_LOAD_SUMMARY.get("mode", "")
    g = SEED_LOAD_SUMMARY.get("seeds_groups", 0)
    w = SEED_LOAD_SUMMARY.get("seeds_weights", 0)
    f = SEED_LOAD_SUMMARY.get("final_features", 0)
    t = SEED_LOAD_SUMMARY.get("tokenizer", "jieba")
    te = SEED_LOAD_SUMMARY.get("tokenizer_effective", "jieba")
    return f"关键词加载: 模式={m}，外置组词={g}，外置权重={w}，最终特征数={f}，分词器={t}({te})"


def sigmoid(x: float) -> float:
    if x < -50:
        return 0.0
    if x > 50:
        return 1.0
    return 1.0 / (1.0 + exp(-x))


def model_path_from_base(base_output_path: str) -> Path:
    p = Path(base_output_path)
    return p.parent / f"{p.stem}_hint_model.json"


def load_hint_model(base_output_path: str) -> Dict:
    path = model_path_from_base(base_output_path)
    if not path.exists():
        return {
            "bias": DEFAULT_BIAS,
            "weights": DEFAULT_WEIGHTS.copy(),
            "token_stats": {},  # token -> {"pos": int, "neg": int}
        }
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 保护性合并（新关键词加入时）
        weights = DEFAULT_WEIGHTS.copy()
        weights.update(data.get("weights", {}))
        return {
            "bias": data.get("bias", DEFAULT_BIAS),
            "weights": weights,
            "token_stats": data.get("token_stats", {}),
        }
    except Exception:
        return {
            "bias": DEFAULT_BIAS,
            "weights": DEFAULT_WEIGHTS.copy(),
            "token_stats": {},
        }


def save_hint_model(base_output_path: str, model: Dict):
    path = model_path_from_base(base_output_path)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(model, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def normalize_text(row) -> str:
    parts: List[str] = []
    for field in ("title", "category", "publish_date", "date"):
        if field in row.index and row[field] is not None:
            try:
                parts.append(str(row[field]))
            except Exception:
                pass
    # 限制正文前 4000 字，避免特别长文本影响性能
    try:
        parts.append(str(row["full_text"])[:4000])
    except Exception:
        pass
    return "\n".join(parts).lower()


def extract_features(row) -> Dict[str, int]:
    text = normalize_text(row)
    t = text.lower()
    feats: Dict[str, int] = {}
    A = _AC
    if A is None:
        _rebuild_automaton()
        A = _AC
    if A is None:
        return feats
    matched: Set[str] = set()
    for _, payload in A.iter(t):
        # payload 是 lower 形式
        k = _AC_KEYMAP.get(payload, payload)
        matched.add(k)
    for k in matched:
        feats[k] = 1
    return feats


# ---------------- 自学习关键词（轻量） ----------------


def _tokenize_for_learning(text: str) -> List[str]:
    # 固定使用 jieba 分词，辅以英文、数字+中文模式补充
    tokens: List[str] = []
    # jieba 中文/混合分词
    for w in jieba.lcut(text, cut_all=False):
        w = w.strip().lower()
        if not w:
            continue
        if w.isdigit():
            continue
        if w in _STOPWORDS:
            continue
        if len(w) < 2 or len(w) > MAX_TOKEN_LENGTH:
            continue
        tokens.append(w)
    # 英文/拼音单词补充（≥3）
    t = text.lower()
    for m in re.finditer(r"[a-z]{3,}", t):
        tok = m.group(0)
        if tok in _STOPWORDS:
            continue
        if len(tok) <= MAX_TOKEN_LENGTH:
            tokens.append(tok)
    # 数字+中文/字母组合补充（如 588轮、g123次）
    for m in re.finditer(r"\b\d{2,}[a-z\u4e00-\u9fff]+", t):
        tok = m.group(0)
        if len(tok) <= MAX_TOKEN_LENGTH:
            tokens.append(tok)
    return tokens


def update_token_stats(
    model: Dict, row, label_non_construction: int
) -> Dict[str, Tuple[int, int]]:
    """根据当前案例与标签更新 token 统计，返回本次增量用于撤销。
    label_non_construction: 1=非建筑业, 0=建筑业
    返回: {token: (d_pos, d_neg)}
    """
    if "token_stats" not in model:
        model["token_stats"] = {}
    text = normalize_text(row)
    toks = _tokenize_for_learning(text)
    delta: Dict[str, Tuple[int, int]] = {}
    for tok in toks:
        stat = model["token_stats"].setdefault(tok, {"pos": 0, "neg": 0})
        if label_non_construction == 1:
            stat["pos"] += 1
            delta[tok] = (1, 0)
        else:
            stat["neg"] += 1
            delta[tok] = (0, 1)
    return delta


def rollback_token_stats(model: Dict, delta: Dict[str, Tuple[int, int]]):
    if not delta:
        return
    stats = model.get("token_stats", {})
    for tok, (dp, dn) in delta.items():
        stat = stats.get(tok)
        if not stat:
            continue
        stat["pos"] = max(0, stat.get("pos", 0) - dp)
        stat["neg"] = max(0, stat.get("neg", 0) - dn)


def _log_odds(pos: int, neg: int, alpha: float = ALPHA) -> float:
    from math import log

    return log((pos + alpha) / (neg + alpha))


def maybe_expand_features(model: Dict, max_add: int = 3) -> List[str]:
    """基于 token 统计，筛选高判别力的 token 动态加入为特征，返回新增列表。
    规则：总频次≥MIN_COUNT 且 |log_odds|≥阈值；初始权重=clip(log_odds, -3, 3)
    """
    stats = model.get("token_stats", {})
    weights = model.get("weights", {})
    candidates: List[Tuple[str, float, int]] = []  # (token, log_odds, total)
    for tok, st in stats.items():
        total = st.get("pos", 0) + st.get("neg", 0)
        if total < MIN_COUNT:
            continue
        lo = _log_odds(st.get("pos", 0), st.get("neg", 0))
        if abs(lo) >= ABS_LOG_ODDS_THRESH and tok not in weights:
            candidates.append((tok, lo, total))
    # 先按总频次，再按绝对 log_odds 排序，取前若干
    candidates.sort(key=lambda x: (x[2], abs(x[1])), reverse=True)
    added: List[str] = []
    # 确保存在学习组
    learned_set = set(FEATURE_GROUPS.get("_learned", []))

    for tok, lo, _ in candidates[:max_add]:
        # 初始权重按 log_odds 映射，并结合方向：正值=非建筑业；负值=建筑业
        init_w = max(-3.0, min(3.0, lo))
        weights[tok] = init_w
        learned_set.add(tok)
        added.append(tok)
    model["weights"] = weights
    FEATURE_GROUPS["_learned"] = sorted(learned_set)
    # 新增学习特征后重建 AC 自动机
    if added:
        _rebuild_automaton()
    return added


def remove_learned_features(model: Dict, tokens: List[str]):
    """撤销时移除本次新加入的特征（仅限本次新增）。"""
    if not tokens:
        return
    weights = model.get("weights", {})
    for t in tokens:
        if t in weights:
            # 仅当该词来自学习组且不是内置/外置种子时移除
            # 简单策略：如果不在任何分组（除了_learned和_custom）则留存；否则也可以保留。
            # 这里按保守逻辑：只从weights删除，不动分组以避免影响其他流程。
            try:
                del weights[t]
            except KeyError:
                pass
    model["weights"] = weights
    # 从_learned分组移除
    learned = set(FEATURE_GROUPS.get("_learned", []))
    for t in tokens:
        learned.discard(t)
    FEATURE_GROUPS["_learned"] = sorted(learned)
    # 学习特征移除后重建 AC 自动机
    if tokens:
        _rebuild_automaton()


def predict_non_construction_proba(
    model: Dict, features: Dict[str, int]
) -> Tuple[float, List[Tuple[str, float]]]:
    w = model["weights"]
    z = model.get("bias", 0.0)
    contributions: List[Tuple[str, float]] = []
    for name, x in features.items():
        if not x:
            continue
        c = w.get(name, 0.0) * x
        contributions.append((name, c))
        z += c
    p = sigmoid(z)
    # 根据绝对贡献排序，取前几项解释
    contributions.sort(key=lambda t: abs(t[1]), reverse=True)
    return p, contributions[:5]


def update_model_online(
    model: Dict, features: Dict[str, int], label_non_construction: int
) -> Dict[str, float]:
    # 返回本次应用到权重的增量（用于撤销）
    p, _ = predict_non_construction_proba(model, features)
    error = label_non_construction - p  # y - p
    delta_bias = LEARNING_RATE * error
    model["bias"] = model.get("bias", 0.0) + delta_bias
    delta_w: Dict[str, float] = {}
    for name, x in features.items():
        if not x:
            continue
        dw = LEARNING_RATE * error * x
        model["weights"][name] = model["weights"].get(name, 0.0) + dw
        delta_w[name] = dw
    # 返回增量以便撤销
    return {"bias": delta_bias, "weights": delta_w}


def rollback_update(model: Dict, delta: Dict[str, float]):
    model["bias"] = model.get("bias", 0.0) - delta.get("bias", 0.0)
    for name, dw in delta.get("weights", {}).items():
        model["weights"][name] = model["weights"].get(name, 0.0) - dw


def format_hint_line(prob: float, contributors: List[Tuple[str, float]]) -> str:
    pct = int(round(prob * 100))
    reason_keys = [f for f, _ in contributors if _ != 0]
    if reason_keys:
        reason = "，依据: " + ", ".join(reason_keys[:3])
    else:
        reason = ""
    return f"🔎 智能提示: 非建筑业概率约 {pct}%{reason}"


# ==================== 增强版：在线 TF-IDF + 改进 LR ====================


class OnlineTFIDF:
    """在线 TF-IDF 特征提取器（增量更新文档频率）"""

    def __init__(self, max_features: int = 300):
        self.max_features = max_features
        self.doc_count = 0
        self.term_doc_freq: Dict[str, int] = defaultdict(int)  # 词在多少文档中出现过
        self.vocabulary: Dict[str, int] = {}  # 词 -> 特征索引

    def learn_one(self, tokens: List[str]):
        """增量学习一个文档的词汇"""
        self.doc_count += 1
        unique_tokens = set(tokens)

        # 更新文档频率
        for tok in unique_tokens:
            self.term_doc_freq[tok] += 1
            # 动态扩展词表（限制大小）
            if tok not in self.vocabulary and len(self.vocabulary) < self.max_features:
                self.vocabulary[tok] = len(self.vocabulary)

    def transform_one(self, tokens: List[str]) -> Dict[str, float]:
        """将文档转换为 TF-IDF 特征向量"""
        if self.doc_count == 0:
            return {}

        # 计算 TF（词频）
        term_count = defaultdict(int)
        for tok in tokens:
            if tok in self.vocabulary:
                term_count[tok] += 1

        total_terms = len(tokens)
        if total_terms == 0:
            return {}

        # 计算 TF-IDF
        tfidf_feats: Dict[str, float] = {}
        for tok, count in term_count.items():
            if tok not in self.vocabulary:
                continue

            tf = count / total_terms
            df = self.term_doc_freq.get(tok, 1)
            # IDF = log((N + 1) / (df + 1))
            idf = log((self.doc_count + 1) / (df + 1))
            tfidf_feats[f"tfidf_{tok}"] = tf * idf

        # L2 归一化
        norm = sqrt(sum(v * v for v in tfidf_feats.values()))
        if norm > 0:
            tfidf_feats = {k: v / norm for k, v in tfidf_feats.items()}

        return tfidf_feats

    def to_dict(self) -> Dict:
        return {
            "doc_count": self.doc_count,
            "term_doc_freq": dict(self.term_doc_freq),
            "vocabulary": self.vocabulary,
            "max_features": self.max_features,
        }

    @classmethod
    def from_dict(cls, data: Dict):
        obj = cls(max_features=data.get("max_features", 300))
        obj.doc_count = data.get("doc_count", 0)
        obj.term_doc_freq = defaultdict(int, data.get("term_doc_freq", {}))
        obj.vocabulary = data.get("vocabulary", {})
        return obj


def extract_features_enhanced(model: Dict, row) -> Dict[str, float]:
    """增强版特征提取：关键词特征 + TF-IDF 特征"""
    # 1. 原有关键词特征（二值）
    keyword_feats = extract_features(row)

    # 2. TF-IDF 特征（连续值）
    tfidf_module = model.get("tfidf")
    if tfidf_module is None:
        # 首次使用，初始化
        tfidf_module = OnlineTFIDF(max_features=300)
        model["tfidf"] = tfidf_module

    text = normalize_text(row)
    tokens = _tokenize_for_learning(text)
    tfidf_feats = tfidf_module.transform_one(tokens)

    # 合并特征（关键词权重为1，TF-IDF权重为实际值）
    all_feats: Dict[str, float] = {}
    for k, v in keyword_feats.items():
        all_feats[k] = float(v)
    all_feats.update(tfidf_feats)

    return all_feats


def predict_non_construction_proba_enhanced(
    model: Dict, features: Dict[str, float]
) -> Tuple[float, List[Tuple[str, float]]]:
    """增强版预测（支持连续值特征）"""
    w = model["weights"]
    z = model.get("bias", 0.0)
    contributions: List[Tuple[str, float]] = []

    for name, x in features.items():
        if x == 0:
            continue
        weight = w.get(name, 0.0)
        c = weight * x
        contributions.append((name, c))
        z += c

    p = sigmoid(z)
    contributions.sort(key=lambda t: abs(t[1]), reverse=True)
    return p, contributions[:5]


def update_model_online_enhanced(
    model: Dict, row, features: Dict[str, float], label_non_construction: int
) -> Dict:
    """增强版在线更新（L2正则化 + 自适应学习率）"""
    # 记录训练次数（用于自适应学习率）
    n_updates = model.get("n_updates", 0) + 1
    model["n_updates"] = n_updates

    # 自适应学习率：lr_t = lr_0 / sqrt(t)
    adaptive_lr = LEARNING_RATE / sqrt(n_updates)

    # L2 正则化系数
    l2_lambda = 0.01

    # 预测
    p, _ = predict_non_construction_proba_enhanced(model, features)
    error = label_non_construction - p

    # 更新偏置
    delta_bias = adaptive_lr * error
    model["bias"] = model.get("bias", 0.0) + delta_bias

    # 更新权重（带 L2 正则化）
    delta_w: Dict[str, float] = {}
    for name, x in features.items():
        if x == 0:
            continue
        old_w = model["weights"].get(name, 0.0)
        # 梯度 = error * x - l2_lambda * w
        gradient = error * x - l2_lambda * old_w
        dw = adaptive_lr * gradient
        model["weights"][name] = old_w + dw
        delta_w[name] = dw

    # 更新 TF-IDF 模块
    tfidf_module = model.get("tfidf")
    if tfidf_module is not None:
        text = normalize_text(row)
        tokens = _tokenize_for_learning(text)
        tfidf_module.learn_one(tokens)

    return {"bias": delta_bias, "weights": delta_w}


def load_hint_model_enhanced(base_output_path: str) -> Dict:
    """加载增强版模型（兼容旧版）"""
    model = load_hint_model(base_output_path)

    # 如果存在 TF-IDF 数据，恢复
    if "tfidf" in model and isinstance(model["tfidf"], dict):
        model["tfidf"] = OnlineTFIDF.from_dict(model["tfidf"])
    else:
        model["tfidf"] = OnlineTFIDF(max_features=300)

    if "n_updates" not in model:
        model["n_updates"] = 0

    return model


def save_hint_model_enhanced(base_output_path: str, model: Dict):
    """保存增强版模型"""
    # 序列化 TF-IDF 模块
    model_copy = model.copy()
    tfidf_module = model_copy.get("tfidf")
    if tfidf_module is not None and hasattr(tfidf_module, "to_dict"):
        model_copy["tfidf"] = tfidf_module.to_dict()

    save_hint_model(base_output_path, model_copy)
