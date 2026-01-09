# UEPluginManager

UE 插件管理工具，统一管理 UE 项目及其关联引擎中的所有插件。

## 功能

- **插件扫描** - 自动扫描项目插件和引擎插件
- **引擎识别** - 支持安装版和源码版引擎
- **搜索筛选** - 按名称、来源、分类筛选
- **依赖分析** - 查看插件依赖和被依赖关系
- **启用管理** - 直接启用/禁用插件（修改 .uproject）
- **快速访问** - 一键打开插件目录

## 运行

```bash
# 创建环境
conda create -n UEPluginManager python=3.11 -y
conda activate UEPluginManager
pip install -r requirements.txt

# 启动
python Main.py
```

## 使用

1. 点击「浏览」选择 UE 项目目录
2. 工具自动扫描项目和引擎插件
3. 使用搜索框或筛选器定位插件
4. 点击插件查看详情
5. 勾选「在项目中启用」管理插件状态
