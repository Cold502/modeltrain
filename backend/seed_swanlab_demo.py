"""生成 SwanLab 示例训练数据，让 SwanBoard 有内容可展示"""
import swanlab
import random
import math
import os
import sys

def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "swanlab_data")
    os.makedirs(data_dir, exist_ok=True)

    # 已有数据则跳过
    if os.listdir(data_dir):
        print(f"[SwanLab] Data already exists in {data_dir}, skip seeding.")
        return

    print(f"[SwanLab] Generating demo training data in {data_dir} ...")
    run = swanlab.init(
        project="example",
        experiment_name="example-sft-training",
        mode="local",
        logdir=data_dir,
        description="示例训练数据",
    )

    for step in range(100):
        loss = 2.5 * math.exp(-0.03 * step) + random.uniform(-0.05, 0.05)
        lr = 2e-5 * (1 - step / 100)
        acc = min(0.95, 0.3 + 0.007 * step + random.uniform(-0.02, 0.02))
        eval_loss = 2.8 * math.exp(-0.025 * step) + random.uniform(-0.08, 0.08)
        swanlab.log({
            "train/loss": loss,
            "train/learning_rate": lr,
            "train/accuracy": acc,
            "eval/loss": eval_loss,
            "eval/accuracy": acc - random.uniform(0, 0.05),
        }, step=step)

    swanlab.finish()
    print(f"[SwanLab] Demo data generated successfully.")

if __name__ == "__main__":
    main()
