# 使用方式：在 Terminal 中执行： streamlit run tax_calculator_app.py

import streamlit as st
import pandas as pd
from tax_calculator import monthly_net, annual_net, yearly_salary_details
import os

st.set_page_config(
    page_title="上海个税计算器",
    page_icon="💰",
    layout="wide"
)

st.title("上海个税计算器 💰")

# 创建侧边栏，用于选择计算模式
calculation_mode = st.sidebar.radio(
    "选择计算模式",
    ["月度工资计算", "年度工资计算", "12个月详细计算"]
)

# 是否四舍五入到整数
round_int = st.sidebar.checkbox("结果四舍五入到整数", value=False)

if calculation_mode == "月度工资计算":
    st.header("月度工资计算")
    
    # 输入月工资
    monthly_salary = st.number_input(
        "输入税前月工资（元）",
        min_value=0.0,
        value=12000.0,
        step=1000.0
    )
    
    if st.button("计算"):
        result = monthly_net(monthly_salary, round_int)
        
        # 转换为 DataFrame 并显示
        df = pd.DataFrame([result])
        
        # 显示主要结果
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("税前工资", f"¥{monthly_salary:,.2f}")
        with col2:
            st.metric("应纳税额", f"¥{result['tax']:,.2f}")
        with col3:
            st.metric("税后工资", f"¥{result['net']:,.2f}")
        
        # 显示详细分项
        st.subheader("详细分项")
        st.dataframe(df)

elif calculation_mode == "年度工资计算":
    st.header("年度工资计算")
    
    # 输入年工资
    annual_salary = st.number_input(
        "输入税前年工资（元）",
        min_value=0.0,
        value=144000.0,
        step=12000.0
    )
    
    if st.button("计算"):
        result = annual_net(annual_salary, round_int)
        
        # 转换为 DataFrame 并显示
        df = pd.DataFrame([result])
        
        # 显示主要结果
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("税前年薪", f"¥{annual_salary:,.2f}")
        with col2:
            st.metric("年度个税", f"¥{result['tax_annual']:,.2f}")
        with col3:
            st.metric("税后年薪", f"¥{result['net_annual']:,.2f}")
        
        # 显示月均值
        st.metric("月均税后工资", f"¥{result['net_monthly_equivalent']:,.2f}")
        
        # 显示详细分项
        st.subheader("详细分项")
        st.dataframe(df)

else:  # 12个月详细计算
    st.header("12个月详细计算")
    
    col1, col2 = st.columns(2)
    with col1:
        # 输入月工资
        monthly_salary = st.number_input(
            "输入基本月工资（元）",
            min_value=0.0,
            value=12000.0,
            step=1000.0
        )
    
    with col2:
        # 选择是否导出CSV
        export_csv = st.checkbox("导出为CSV文件", value=False)
        if export_csv:
            csv_filename = st.text_input("CSV文件名前缀", value="salary_details")
    
    if st.button("计算"):
        # 创建12个月的工资列表
        monthly_list = [monthly_salary] * 12
        result = yearly_salary_details(monthly_list, round_int)
        
        # 显示年度汇总
        st.subheader("年度汇总")
        totals_df = pd.DataFrame([result["totals"]])
        
        # 显示主要结果
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("年度总收入", f"¥{result['totals']['gross_annual']:,.2f}")
        with col2:
            st.metric("年度个税", f"¥{result['totals']['tax_annual']:,.2f}")
        with col3:
            st.metric("税后总收入", f"¥{result['totals']['net_annual']:,.2f}")
        
        # 显示月度明细
        st.subheader("月度明细")
        monthly_df = pd.DataFrame(result["monthly"])
        st.dataframe(monthly_df)
        
        # 导出CSV
        if export_csv:
            # 确保output_csv目录存在
            os.makedirs("output_csv", exist_ok=True)
            
            # 保存文件
            monthly_file = os.path.join("output_csv", f"{csv_filename}_monthly.csv")
            totals_file = os.path.join("output_csv", f"{csv_filename}_totals.csv")
            
            monthly_df.to_csv(monthly_file, index=False)
            totals_df.to_csv(totals_file, index=False)
            
            st.success(f"CSV文件已保存到:\n- {monthly_file}\n- {totals_file}")

# 添加页脚
st.markdown("---")
st.markdown("💡 本计算器基于上海市最新个人所得税政策计算。") 