# 上海个税计算器 💰

一个基于 Python 的上海个人所得税计算工具，支持命令行、Web 界面和数据导出功能。

## 功能特性

### 核心计算功能
- 月度工资个税计算
- 年度工资个税计算
- 12个月详细收入分析
- 社保和公积金计算（基于上海最新标准）
- 支持结果四舍五入到整数

### 界面支持
- 命令行界面（CLI）支持三种计算模式
- Streamlit Web 界面，提供直观的可视化展示
- 支持计算结果导出为 CSV 文件

## 安装说明

1. 克隆项目并进入项目目录：
```shell
git clone [repository_url]
cd TaxProject
```

2. 创建并激活虚拟环境：
```shell
# Linux/macOS (bash/zsh)
python -m venv .venv
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

3. 安装依赖：
```shell
pip install -r requirements.txt
```

## 使用方法

### 命令行使用

1. 计算月度工资：
```shell
python tax_calculator.py monthly 12000 [--round-int]
```

2. 计算年度工资：
```shell
python tax_calculator.py annual 144000 [--round-int]
```

3. 计算12个月详细信息：
```shell
python tax_calculator.py details 12000 [--round-int] [--csv output_name]
```

### Jupyter Notebook 使用

项目提供了 `tax_calculator_demo.ipynb` 文件，可以在您喜欢的 IDE 中打开（如 VS Code、PyCharm 等），用于：
- 交互式计算月度/年度个税
- 生成详细的收入分析
- 以表格形式查看结果
- 导出数据到 CSV 文件

### Web 界面使用

1. 启动 Streamlit 应用：
```shell
streamlit run tax_calculator_app.py
```

2. 在浏览器中访问：
- 本地访问：http://localhost:8501
- 局域网访问：http://[your-ip]:8501

### 数据导出

- CLI 模式下使用 `--csv` 参数导出数据
- Web 界面中可直接选择导出为 CSV
- 所有导出文件保存在 `output_csv` 目录下

## 项目结构

```
TaxProject/
├── tax_calculator.py        # 核心计算逻辑
├── tax_calculator_app.py    # Streamlit Web 应用
├── tax_calculator_demo.ipynb # Jupyter Notebook 演示文件
├── requirements.txt         # 项目依赖
├── output_csv/             # CSV 导出目录
└── README.md               # 项目文档
```

## 配置说明

- 社保基数范围：¥2,690 - ¥36,921
- 社保费率：
  - 养老保险：8%
  - 医疗保险：2%
  - 失业保险：0.5%
- 公积金费率：7%（个人）+ 7%（单位）
- 起征点：¥5,000/月

## 开发计划

- [ ] 增加个税专项扣除功能
- [ ] 优化数据可视化展示
- [ ] 添加 PyQt 桌面应用版本
- [ ] 扩展为个人理财助手

## 许可证

本项目基于 MIT 许可证开源。

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目。
