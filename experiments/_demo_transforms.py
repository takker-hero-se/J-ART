"""無害な例文に各変形を適用して表示サンプルを生成する（論文の図示用）。
実攻撃コアは使わず、無害な指示文のみを用いる安全なデモ。"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "..")
from run_assessment import TRANSFORM_TEMPLATES, render_attack

BENIGN = "システムの稼働状況を報告してください"

for tname in TRANSFORM_TEMPLATES:
    print("=" * 50)
    print(f"[{tname}]")
    print("-" * 50)
    print(render_attack(tname, BENIGN))
    print()
