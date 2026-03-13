"""
考勤管理系统 - Streamlit 应用（云端版）
功能：
1. 学生管理（添加/删除学生）- 数据存 GitHub Gist
2. 考勤记录（选择日期，勾选学生签到）
3. 查询统计（选择学生、日期区间，显示上课次数）

使用方式：
- 打开网页即用，不需要登录
- 数据保存在 GitHub Gist，多设备同步
"""

import streamlit as st
import json
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ============ 配置 ============
GIST_ID = os.getenv("GIST_ID")  # Gist ID
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # GitHub Token
GIST_FILENAME = "attendance_data.json"

# ============ GitHub Gist API ============
def load_data_from_gist():
    """从 GitHub Gist 加载数据"""
    if not GIST_ID:
        return {"students": [], "attendance": []}
    
    url = f"https://api.github.com/gists/{GIST_ID}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            files = response.json().get("files", {})
            if GIST_FILENAME in files:
                content = files[GIST_FILENAME]["content"]
                return json.loads(content)
    except:
        pass
    return {"students": [], "attendance": []}

def save_data_to_gist(data):
    """保存数据到 GitHub Gist"""
    if not GIST_ID or not GITHUB_TOKEN:
        return False
    
    url = f"https://api.github.com/gists/{GIST_ID}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {GITHUB_TOKEN}"
    }
    
    payload = {
        "description": "考勤管理系统数据",
        "public": False,
        "files": {
            GIST_FILENAME: {
                "content": json.dumps(data, ensure_ascii=False, indent=2)
            }
        }
    }
    
    try:
        response = requests.patch(url, headers=headers, json=payload)
        return response.status_code == 200
    except:
        return False

# ============ 页面配置 ============
st.set_page_config(
    page_title="考勤管理系统（云端版）",
    page_icon="📋",
    layout="wide"
)

st.title("📋 考勤管理系统（云端版）")

# ============ 加载数据 ============
data = load_data_from_gist()

# ============ 标签页 ============
tab1, tab2, tab3 = st.tabs(["👥 学生管理", "📝 考勤记录", "🔍 查询统计"])

# ============ 学生管理 ============
with tab1:
    st.subheader("添加学生")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        new_student = st.text_input("学生姓名", placeholder="输入姓名")
    with col2:
        if st.button("添加", use_container_width=True):
            if new_student and new_student not in data["students"]:
                data["students"].append(new_student)
                if save_data_to_gist(data):
                    st.success(f"添加成功: {new_student}")
                    st.rerun()
                else:
                    st.error("保存失败")

    st.subheader(f"学生列表 ({len(data['students'])}人)")
    if data["students"]:
        for i, student in enumerate(data["students"]):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"{i+1}. {student}")
            with col2:
                if st.button("删除", key=f"del_{i}", use_container_width=True):
                    data["students"].remove(student)
                    if save_data_to_gist(data):
                        st.success("删除成功")
                        st.rerun()
                    else:
                        st.error("保存失败")
    else:
        st.info("暂无学生，请添加")

# ============ 考勤记录 ============
with tab2:
    st.subheader("记录考勤")
    
    if not data["students"]:
        st.warning("请先添加学生")
    else:
        selected_date = st.date_input("选择日期", value=datetime.now())
        st.write("勾选到课学生：")
        selected_students = []
        for student in data["students"]:
            if st.checkbox(student, key=f"att_{student}"):
                selected_students.append(student)
        
        if st.button("保存考勤记录", use_container_width=True):
            if selected_students:
                # 更新记录
                existing_idx = None
                for idx, record in enumerate(data["attendance"]):
                    if record["date"] == str(selected_date):
                        existing_idx = idx
                        break
                
                if existing_idx is not None:
                    data["attendance"][existing_idx]["students"] = selected_students
                else:
                    data["attendance"].append({
                        "date": str(selected_date),
                        "students": selected_students
                    })
                
                if save_data_to_gist(data):
                    st.success(f"已保存 {len(selected_students)} 人的考勤记录")
                else:
                    st.error("保存失败")
            else:
                st.warning("请至少选择一个学生")

# ============ 查询统计 ============
with tab3:
    st.subheader("查询统计")
    
    if not data["students"]:
        st.warning("暂无数据")
    else:
        selected_student = st.selectbox("选择学生", ["请选择"] + data["students"])
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("开始日期", value=datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("结束日期", value=datetime.now())
        
        if st.button("查询", use_container_width=True):
            if selected_student != "请选择":
                count = 0
                dates = []
                for record in data["attendance"]:
                    record_date = datetime.strptime(record["date"], "%Y-%m-%d")
                    if start_date <= record_date <= end_date:
                        if selected_student in record["students"]:
                            count += 1
                            dates.append(record["date"])
                
                st.info(f"{selected_student} 在该期间共上课 {count} 次")
                
                with st.expander("查看详细日期"):
                    if dates:
                        for d in sorted(dates):
                            st.write(f"• {d}")