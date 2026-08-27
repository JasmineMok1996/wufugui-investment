#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
吴富贵网格档位计算器
用法: python grid_calculator.py <股票代码> [周期:week|month] [K线数:30]
示例: python grid_calculator.py sh600036 week 30
依赖: westock-data 数据接口 (需自行配置 WESTOCK / NODE 路径)
说明: 输出当前价在周线布林带(20周期)中的位置百分位, 以及五档买卖动作建议
"""
import os
import subprocess
import sys

# ============ 配置：westock-data CLI 路径（按本机实际修改，或用环境变量） ============
WESTOCK = os.environ.get(
    "WESTOCK_INDEX",
    "westock-data/scripts/index.js",  # 默认相对路径；若 westock-data 在 PATH 中可直接写 "westock"
)
NODE = os.environ.get("NODE_BIN", "node")  # Node.js 可执行文件
# ======================================================================

def get_kline(code, period="week", limit=30):
    r = subprocess.run(
        [NODE, WESTOCK, "kline", code, "--period", period, "--limit", str(limit), "--fq", "qfq"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return r.stdout

def parse_close(out):
    """westock-data kline 返回 markdown 表格, 新的在前. 列: date|open|last|high|low|volume|amount|exchange"""
    prices = []
    for line in out.splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 4:
            d = parts[1]
            if len(d) >= 8 and d[:4].isdigit():
                try:
                    prices.append(float(parts[3]))  # last = 收盘
                except ValueError:
                    pass
    return prices  # 新的在前!

def boll_position(prices, n=20, k=2):
    if len(prices) < n:
        return None
    last20 = prices[:n]  # 最近n个
    mid = sum(last20) / n
    var = sum((x - mid) ** 2 for x in last20) / n
    sd = var ** 0.5
    upper, lower = mid + k * sd, mid - k * sd
    cur = prices[0]  # 最新价
    pos = (cur - lower) / (upper - lower) * 100
    return {"cur": cur, "mid": mid, "upper": upper, "lower": lower, "pos": pos}

def band(pos):
    if pos < 10:
        return "周下(极致买点)"
    if pos < 40:
        return "周中偏下(牵手区)"
    if pos < 60:
        return "周中(观望)"
    if pos < 90:
        return "周中偏上(降本区)"
    return "周上(卖出区)"

def action(pos):
    if pos < 40:
        return "可以开始网格牵手(买第一档)"
    if pos < 60:
        return "观望不动"
    if pos < 90:
        return "持有可降本(卖1~2档), 未持有不追"
    return "分批卖出"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python grid_calculator.py <代码> [周期] [K线数]")
        print("示例: python grid_calculator.py sh600036 week 30")
        sys.exit(1)
    code = sys.argv[1]
    period = sys.argv[2] if len(sys.argv) > 2 else "week"
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    prices = parse_close(get_kline(code, period, limit))
    if len(prices) < 20:
        print("数据不足20期, 无法计算")
        sys.exit(1)
    b = boll_position(prices)
    pos = b["pos"]
    print("=" * 56)
    print(f"标的: {code}  周期: {period}  数据基准: 最新收盘")
    print(f"现价: {b['cur']:.3f}  中轨: {b['mid']:.3f}  上轨: {b['upper']:.3f}  下轨: {b['lower']:.3f}")
    print(f"位置百分位: {pos:.1f}%")
    print(f"当前档位: {band(pos)}")
    print(f"操作建议: {action(pos)}")
    print("=" * 56)
    print("记住双信号规则: 先看股息率≥4.5%(价值开关), 再看位置≤40%(节奏)。两者都满足才动手。")
