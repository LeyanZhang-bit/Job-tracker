# 求职进度管理工具

Python + Streamlit + SQLite 个人本地应用。支持记录公司、投递岗位、投递日期、申请状态和备注；可以编辑每一条记录、搜索筛选、删除、查看统计并导出 CSV。

## 在 PyCharm 中运行

建议使用 Python 3.10 或更新版本。用 PyCharm 打开本项目文件夹，在底部 Terminal（终端）中运行：

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

浏览器通常自动打开；也可以访问终端显示的 Local URL，通常为 http://localhost:8501 。停止程序请在终端按 Ctrl+C。启动时应使用 Streamlit 命令，不要直接用普通 Python 运行 app.py。

## 使用方法

1. 左侧选择“新增投递”，填写公司、岗位、日期、状态，点击“添加记录”。
2. 选择“查看与编辑”，在表格下方选择记录，修改后点击“保存修改”。
3. 可搜索公司或岗位，或按状态筛选。
4. 删除需展开删除区域并勾选确认。
5. 左侧可导出全部记录为 CSV，支持 Excel 查看。

## 数据存储与备份

首次运行自动创建 data/applications.db。刷新页面或重启程序不会丢失已保存的数据。数据库位置相对于 app.py 固定，不受终端启动目录影响。

完整备份：停止程序后复制整个 data 文件夹。CSV 是查看和导出格式，当前没有 CSV 导入功能。

## GitHub 与部署

上传 app.py、requirements.txt、README.md 和 .gitignore。不要上传含有真实求职信息的 data 文件夹、虚拟环境或 PyCharm 配置。网页手动上传文件时也需要自己避开这些文件。

当前版本用于个人本地使用，没有账号隔离。如果公开部署，同一个数据库中的数据可能被所有访问者查看和修改；云平台本地磁盘也未必持久保存。公开演示应使用虚构数据。正式多人使用需要增加登录、权限控制和持久化数据库。
