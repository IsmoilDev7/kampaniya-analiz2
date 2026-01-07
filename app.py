import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from prophet import Prophet

st.set_page_config(page_title="Savdo va Kampaniya Analizi", layout="wide")

st.title("📊 Sotuv Analizi va Prognoz Dashboard")
st.markdown("""
Bu dashboard kengaytirilgan sotuv ma'lumotlariga asoslangan:
- Savdo trendlari va KPI
- Foyda va zarar (tannarx, себестоимость)
- Narx o‘zgarishining ta’siri (What-if)
- Subkonto / Valyuta bo‘yicha analiz
- Tovar / Ombor / Subkonto filtrlar
- Kelajak prognozi (6 oy)
""")

# Fayl yuklash
file = st.file_uploader("📂 Excel faylni yuklang", type=["xlsx"])
if file:
    df = pd.read_excel(file)
    
    # Sanalarni va raqamlarni formatlash
    df['Период'] = pd.to_datetime(df['Период'], errors='coerce')
    df['Summa'] = pd.to_numeric(df['Summa'], errors='coerce')
    df['СуммаВал'] = pd.to_numeric(df['СуммаВал'], errors='coerce')
    df['Miqdor'] = pd.to_numeric(df['Miqdor'], errors='coerce')
    df['Tannarx summasi'] = pd.to_numeric(df['Tannarx summasi'], errors='coerce')
    df['СебестоимостьВал'] = pd.to_numeric(df['СебестоимостьВал'], errors='coerce')
    
    df = df.dropna(subset=['Период','Summa','Miqdor'])
    
    # Narx va foyda
    df['Narx'] = df['Summa'] / df['Miqdor']
    df['Foyda'] = df['Summa'] - df['Tannarx summasi']
    df['ROI'] = df['Foyda'] / df['Tannarx summasi']
    
    # Filtrlar
    st.subheader("🔍 Filtrlar")
    col1, col2, col3 = st.columns(3)
    with col1:
        tovar = st.multiselect("Tovar", df['Tovar'].unique(), default=df['Tovar'].unique())
    with col2:
        ombor = st.multiselect("Ombor", df['Ombor'].unique(), default=df['Ombor'].unique())
    with col3:
        subkonto = st.multiselect("Subkonto", df['Subkonto'].unique(), default=df['Subkonto'].unique())
    
    df_filtered = df[df['Tovar'].isin(tovar) & df['Ombor'].isin(ombor) & df['Subkonto'].isin(subkonto)]
    
    # KPI
    st.subheader("📌 Asosiy ko‘rsatkichlar")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("💰 Umumiy Savdo", f"{df_filtered['Summa'].sum():,.0f}")
    k2.metric("📦 Sotilgan miqdor", f"{df_filtered['Miqdor'].sum():,.0f}")
    k3.metric("💲 O‘rtacha Narx", f"{df_filtered['Narx'].mean():,.2f}")
    k4.metric("💹 Umumiy Foyda", f"{df_filtered['Foyda'].sum():,.0f}")
    
    # Savdo trendlari
    st.subheader("📈 Savdo va Foyda Trendlari")
    trend = df_filtered.groupby('Период').agg({'Summa':'sum','Foyda':'sum'}).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trend['Период'], y=trend['Summa'], mode='lines+markers', name='Savdo'))
    fig.add_trace(go.Scatter(x=trend['Период'], y=trend['Foyda'], mode='lines+markers', name='Foyda'))
    fig.update_layout(title="Vaqt bo‘yicha Savdo va Foyda", xaxis_title="Период", yaxis_title="Summa")
    st.plotly_chart(fig, use_container_width=True)
    
    # Valyuta bo'yicha analiz
    st.subheader("💱 Valyuta bo‘yicha Savdo")
    valyuta_df = df_filtered.groupby('Valyuta')['СуммаВал'].sum().reset_index()
    st.plotly_chart(px.pie(valyuta_df, names='Valyuta', values='СуммаВал', title="Valyuta bo‘yicha Savdo"), use_container_width=True)
    
    # Tovar bo'yicha foyda / zarar
    st.subheader("📊 Tovar bo‘yicha foyda / zarar")
    profit_tovar = df_filtered.groupby('Tovar')['Foyda'].sum().reset_index()
    st.plotly_chart(px.bar(profit_tovar, x='Tovar', y='Foyda', color='Foyda', color_continuous_scale='Viridis',
                           title="Tovarlar bo‘yicha foyda / zarar"), use_container_width=True)
    
    # Ombor bo'yicha savdo
    st.subheader("🏬 Ombor bo‘yicha savdo taqsimoti")
    ombor_summa = df_filtered.groupby('Ombor')['Summa'].sum().reset_index()
    st.plotly_chart(px.pie(ombor_summa, names='Ombor', values='Summa', title="Ombor bo‘yicha savdo taqsimoti"),
                    use_container_width=True)
    
    # Subkonto heatmap
    st.subheader("🌡️ Subkonto bo‘yicha savdo heatmap")
    heatmap_data = df_filtered.pivot_table(index='Subkonto', columns='Tovar', values='Summa', aggfunc='sum').fillna(0)
    st.plotly_chart(px.imshow(heatmap_data, text_auto=True, aspect="auto", color_continuous_scale='YlOrRd',
                              title="Subkonto bo‘yicha savdo heatmap"), use_container_width=True)
    
    # ROI diagram
    st.subheader("💹 ROI (Foyda / Tannarx)")
    roi_df = df_filtered.groupby('Tovar')['ROI'].mean().reset_index()
    st.plotly_chart(px.bar(roi_df, x='Tovar', y='ROI', color='ROI', color_continuous_scale='Blues',
                           title="Tovar bo‘yicha ROI"), use_container_width=True)
    
    # Scatter narx vs foyda
    st.subheader("💲 Narx vs Foyda scatter plot")
    st.plotly_chart(px.scatter(df_filtered, x='Narx', y='Foyda', color='Tovar', size='Miqdor',
                               hover_data=['Ombor','Subkonto'], title="Narx vs Foyda"), use_container_width=True)
    
    # Cumulative sum (oylik)
    st.subheader("📈 Cumulative Savdo va Foyda")
    trend_cum = trend.copy()
    trend_cum['Summa_cum'] = trend_cum['Summa'].cumsum()
    trend_cum['Foyda_cum'] = trend_cum['Foyda'].cumsum()
    fig_cum = go.Figure()
    fig_cum.add_trace(go.Scatter(x=trend_cum['Период'], y=trend_cum['Summa_cum'], name='Cumulative Savdo'))
    fig_cum.add_trace(go.Scatter(x=trend_cum['Период'], y=trend_cum['Foyda_cum'], name='Cumulative Foyda'))
    fig_cum.update_layout(title="Cumulative Savdo va Foyda", xaxis_title="Период", yaxis_title="Summa")
    st.plotly_chart(fig_cum, use_container_width=True)
    
    # What-if narx simulyatsiyasi
    st.subheader("🎚️ Narx What-if Simulyatsiyasi")
    change = st.slider("Narxni o‘zgartirish (%)", -30, 30, 0)
    trend['Simulyatsiya'] = trend['Summa'] * (1 + change/100)
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=trend['Период'], y=trend['Summa'], name="Asl Savdo"))
    fig2.add_trace(go.Scatter(x=trend['Период'], y=trend['Simulyatsiya'], name="Simulyatsiya"))
    fig2.update_layout(title="Narx o‘zgarishi savdoga ta’siri")
    st.plotly_chart(fig2, use_container_width=True)
    
    # Prognoz
    st.subheader("🔮 Savdo Prognozi (6 oy)")
    ts = trend.rename(columns={'Период':'ds','Summa':'y'})
    model = Prophet()
    model.fit(ts)
    future = model.make_future_dataframe(periods=6, freq='M')
    forecast = model.predict(future)
    st.plotly_chart(px.line(forecast, x='ds', y='yhat', title="Kelgusi 6 oylik Savdo Prognozi"), use_container_width=True)
    
else:
    st.info("Excel faylni yuklang va barcha analizlar avtomatik hosil bo‘lsin.")
