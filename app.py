"""运行：python -m streamlit run app.py"""
import csv
import io
import sqlite3
from contextlib import closing
from datetime import date, datetime
from pathlib import Path

import streamlit as st

DB_PATH = Path(__file__).resolve().parent / "data" / "applications.db"
STATUSES = ["已投递", "筛选中", "笔试", "面试中", "已获 Offer", "已拒绝", "已撤回"]


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def initialize():
    with closing(connect()) as conn, conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            position TEXT NOT NULL,
            applied_on TEXT NOT NULL,
            status TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL
        )""")


def get_records():
    with closing(connect()) as conn:
        return [dict(row) for row in conn.execute(
            "SELECT * FROM applications ORDER BY applied_on DESC, id DESC"
        )]


def save_record(company, position, applied_on, status, notes, record_id=None):
    company, position = company.strip(), position.strip()
    if not company or not position:
        raise ValueError("公司名称和投递岗位不能为空。")
    if status not in STATUSES:
        raise ValueError("申请状态无效。")
    values = (company, position, applied_on.isoformat(), status,
              notes.strip(), datetime.now().isoformat(timespec="seconds"))
    with closing(connect()) as conn, conn:
        if record_id is None:
            conn.execute("""INSERT INTO applications
                (company, position, applied_on, status, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)""", values)
        else:
            cursor = conn.execute("""UPDATE applications SET company=?, position=?,
                applied_on=?, status=?, notes=?, updated_at=? WHERE id=?""",
                values + (record_id,))
            if cursor.rowcount != 1:
                raise ValueError("记录已不存在，请刷新页面。")


def delete_record(record_id):
    with closing(connect()) as conn, conn:
        conn.execute("DELETE FROM applications WHERE id=?", (record_id,))


def csv_bytes(records):
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["编号", "公司", "投递岗位", "投递日期", "申请状态", "备注", "更新时间"])
    for row in records:
        cells = [row[k] for k in
                 ("id", "company", "position", "applied_on", "status", "notes", "updated_at")]
        # 防止用户输入在 Excel 中被解释为公式。
        cells = ["'" + v if isinstance(v, str) and
                 v.lstrip().startswith(("=", "+", "-", "@")) else v for v in cells]
        writer.writerow(cells)
    return output.getvalue().encode("utf-8-sig")


def record_form(record=None):
    """每条记录使用独立表单标识，切换记录时显示对应数据。"""
    existing = record or {}
    record_id = existing.get("id")
    form_key = f"record_{record_id}" if record else f"new_{st.session_state.get('new_version', 0)}"
    with st.form(form_key):
        left, right = st.columns(2)
        company = left.text_input("公司名称 *", value=existing.get("company", ""), max_chars=150)
        position = right.text_input("投递岗位 *", value=existing.get("position", ""), max_chars=150)
        left, right = st.columns(2)
        applied_on = left.date_input("投递日期", value=date.fromisoformat(existing["applied_on"])
                                     if record else date.today())
        status = right.selectbox("申请状态", STATUSES,
                                 index=STATUSES.index(existing.get("status", "已投递")))
        notes = st.text_area("备注", value=existing.get("notes", ""),
                             placeholder="例如：面试安排、招聘联系人、下一步跟进事项", max_chars=5000)
        submitted = st.form_submit_button("保存修改" if record else "添加记录", type="primary")
        if submitted:
            try:
                save_record(company, position, applied_on, status, notes, record_id)
            except (ValueError, sqlite3.Error) as error:
                st.error(str(error))
            else:
                st.session_state["notice"] = "修改已保存。" if record else "投递记录已添加。"
                if not record:
                    st.session_state["new_version"] = st.session_state.get("new_version", 0) + 1
                st.rerun()


def main():
    st.set_page_config(page_title="求职进度管理", page_icon="💼", layout="wide")
    initialize()
    st.title("💼 求职进度管理")
    st.caption("记录每次投递，跟进每一步申请进展。")
    if "notice" in st.session_state:
        st.success(st.session_state.pop("notice"))

    records = get_records()
    counts = st.columns(4)
    counts[0].metric("全部投递", len(records))
    counts[1].metric("待跟进", sum(r["status"] in ("已投递", "筛选中", "笔试") for r in records))
    counts[2].metric("面试中", sum(r["status"] == "面试中" for r in records))
    counts[3].metric("已获 Offer", sum(r["status"] == "已获 Offer" for r in records))

    with st.sidebar:
        st.header("功能菜单")
        page = st.radio("选择操作", ["查看与编辑", "新增投递"])
        st.divider()
        st.caption("个人本地版 · 数据自动保存在项目的 data 文件夹中。")
        st.download_button("导出全部记录 CSV", csv_bytes(records),
                           "求职投递记录.csv", "text/csv", disabled=not records)

    if page == "新增投递":
        st.subheader("新增投递")
        record_form()
        return

    left, right = st.columns([3, 1])
    query = left.text_input("搜索公司或岗位", placeholder="输入关键词").strip().casefold()
    status_filter = right.selectbox("筛选申请状态", ["全部"] + STATUSES)
    visible = [r for r in records if
               (not query or query in r["company"].casefold() or query in r["position"].casefold())
               and (status_filter == "全部" or r["status"] == status_filter)]
    st.caption(f"显示 {len(visible)} 条，共 {len(records)} 条记录；按投递日期从新到旧排列。")
    if not visible:
        st.info("暂无匹配记录。可以调整筛选条件，或在左侧选择“新增投递”。")
        return

    st.dataframe([{"编号": r["id"], "公司": r["company"], "投递岗位": r["position"],
                   "投递日期": r["applied_on"], "申请状态": r["status"], "备注": r["notes"]}
                  for r in visible], hide_index=True, use_container_width=True)
    st.subheader("编辑记录")
    by_id = {r["id"]: r for r in visible}
    selected = st.selectbox("选择要编辑的记录", list(by_id),
                            format_func=lambda i: f"#{i} · {by_id[i]['company']} · {by_id[i]['position']} · {by_id[i]['applied_on']}")
    record_form(by_id[selected])
    with st.expander("删除这条记录"):
        st.write(f"即将删除：{by_id[selected]['company']} / {by_id[selected]['position']}")
        confirmed = st.checkbox("我确认删除这条记录（无法撤销）", key=f"confirm_{selected}")
        if st.button("确认删除", disabled=not confirmed, key=f"delete_{selected}"):
            delete_record(selected)
            st.session_state["notice"] = "记录已删除。"
            st.rerun()


if __name__ == "__main__":
    main()
