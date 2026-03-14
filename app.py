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
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ============ GitHub Gist 配置 ============
GIST_ID = os.getenv("GIST_ID", "your_gist_id_here")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "your_github_token_here")
GIST_FILENAME = "attendance_data.json"

# ============ 数据加载/保存 ============
def load_data():
    """从 GitHub Gist 加载数据"""
    if GIST_ID == "your_gist_id_here":
        return {"students": [], "attendance": []}
    
    url = f"https://api.github.com/gists/{GIST_ID}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN and GITHUB_TOKEN != "your_github_token_here":
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            files = response.json().get("files", {})
            if GIST_FILENAME in files:
                return json.loads(files[GIST_FILENAME]["content"])
    except:
        pass
    return {"students": [], "attendance": []}

def save_data(data):
    """保存数据到 GitHub Gist"""
    st.write(f"调试 - GIST_ID: {GIST_ID}")
    st.write(f"调试 - GITHUB_TOKEN: {GITHUB_TOKEN[:10] if GITHUB_TOKEN else 'None'}...")
    
    if GIST_ID == "your_gist_id_here" or not GITHUB_TOKEN or GITHUB_TOKEN == "your_github_token_here":
        st.error("Gist配置未设置")
        return False
    
    url = f"https://api.github.com/gists/{GIST_ID}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {GITHUB_TOKEN}"
    }
    
    payload = {
        "description": "考勤管理系统数据",
        "public": True,
        "files": {
            GIST_FILENAME: {
                "content": json.dumps(data, ensure_ascii=False, indent=2)
            }
        }
    }
    
    try:
        response = requests.patch(url, headers=headers, json=payload)
        st.write(f"保存响应: {response.status_code}")
        if response.status_code == 200:
            return True
        else:
            st.error(f"保存失败: {response.status_code}")
            st.write(f"错误详情: {response.text[:200]}")
            return False
    except Exception as e:
        st.error(f"保存异常: {e}")
        return False

# ============ 页面配置 ============
st.set_page_config(
    page_title="考勤管理系统",
    page_icon="📋",
    layout="wide"
)

st.title("📋 考勤管理系统")

# ============ 加载数据 ============
data = load_data()

# ============ 创建标签页 ============
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
                if save_data(data):
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
                    if save_data(data):
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
                # 检查是否已存在该日期
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
                
                if save_data(data):
                    st.success(f"已保存 {len(selected_students)} 人的考勤记录")
                    st.rerun()
                else:
                    st.error("保存失败")
            else:
                st.warning("请至少选择一个学生")
        
        # 显示该日期已有的考勤记录并提供删除功能
        st.divider()
        st.subheader("管理已有考勤记录")
        
        # 查找该日期的已有记录
        existing_record = None
        for record in data["attendance"]:
            if record["date"] == str(selected_date):
                existing_record = record
                break
        
        if existing_record and existing_record["students"]:
            st.write(f"📅 {selected_date} 已考勤的学生：")
            for student in existing_record["students"]:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"✓ {student}")
                with col2:
                    # 使用 session_state 来处理确认对话框
                    if f"confirm_delete_{student}" not in st.session_state:
                        st.session_state[f"confirm_delete_{student}"] = False
                    
                    if st.session_state[f"confirm_delete_{student}"]:
                        # 显示确认对话框
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button(f"✅ 确认", key=f"yes_{student}", use_container_width=True):
                                # 删除该学生
                                existing_record["students"].remove(student)
                                if save_data(data):
                                    st.success(f"已删除 {student}")
                                    st.session_state[f"confirm_delete_{student}"] = False
                                    st.rerun()
                                else:
                                    st.error("删除失败")
                        with col_b:
                            if st.button(f"❌ 取消", key=f"no_{student}", use_container_width=True):
                                st.session_state[f"confirm_delete_{student}"] = False
                                st.rerun()
                    else:
                        if st.button(f"🗑️ 删除", key=f"del_{student}_{selected_date}", use_container_width=True):
                            st.session_state[f"confirm_delete_{student}"] = True
                            st.rerun()
        else:
            st.info("该日期暂无考勤记录")

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
                    record_date = datetime.strptime(record["date"], "%Y-%m-%d").date()
                    if start_date <= record_date <= end_date:
                        if selected_student in record["students"]:
                            count += 1
                            dates.append(record["date"])
                
                st.info(f"{selected_student} 在该期间共上课 {count} 次")
                
                with st.expander("查看详细日期"):
                    if dates:
                        for d in sorted(dates):
                            st.write(f"• {d}")