# 南水北调中线水源区排污口数据分析

## 项目简介
本项目对南水北调中线水源区排污口数据进行分析，包括数据质量分析、统计分析和报告生成。

## 项目结构
```
.
├── src/
│   └── data_analysis.py    # 数据分析主脚本
├── reports/                # 分析报告目录
├── 南水北调中线水源区排污口.xlsx  # 原始数据
└── requirements.txt        # 项目依赖
```

## 环境配置
1. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法
1. 运行分析脚本：
```bash
python src/data_analysis.py
```

2. 查看报告：
分析报告将生成在 `reports/analysis_report.md` 文件中。

## 分析内容
- 数据基本信息分析
- 缺失值分析
- 异常值分析
- 统计结果：
  - 省际分布统计
  - 排口类型统计
  - 废污水排放量统计
  - 冷却水排放统计 