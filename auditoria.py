import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Monitor de Control - Negocio Oro", layout="wide", page_icon="⚖️")

# --- PALETA DE COLORES "CONTROL" ---
COLOR_PRIMARY = "#2C3E50"    # Azul Oscuro
COLOR_ACCENT = "#E67E22"     # Naranja
COLOR_SUCCESS = "#27AE60"    # Verde
COLOR_DANGER = "#C0392B"     # Rojo (Alertas)
COLOR_BG_CARD = "#FFFFFF"    # Fondo

# --- ESTILOS CSS ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    p, .stMarkdown, .stText, .stDataFrame {{
        font-size: 20px !important;
    }}
    
    .stCaption {{
        font-size: 18px !important;
        color: #555 !important;
    }}

    h1 {{ color: {COLOR_DANGER}; font-weight: 800; font-size: 3rem; }}
    h2, h3 {{ color: {COLOR_PRIMARY}; font-weight: 700; }}

    div[data-testid="metric-container"] {{
        background-color: {COLOR_BG_CARD};
        border: 1px solid #E0E0E0;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }}
    
    div[data-testid="metric-container"] > label {{
        color: {COLOR_PRIMARY};
        font-size: 1.6rem !important;
        font-weight: 700;
    }}
    
    div[data-testid="metric-container"] > div:nth-child(2) {{
        color: {COLOR_DANGER};
        font-size: 3.8rem !important;
        font-weight: 900;
        line-height: 1.1;
    }}

    .stTabs [data-baseweb="tab"] {{
        font-size: 22px !important;
        font-weight: 600;
        padding: 15px 30px;
    }}

    .capital-alert {{
        background-color: #FADBD8;
        border-left: 12px solid {COLOR_DANGER};
        color: #7B241C;
        padding: 25px;
        border-radius: 8px;
        margin-bottom: 25px;
        font-size: 22px;
        font-weight: bold;
    }}
    
    .method-box {{
        background-color: #D6EAF8;
        border-left: 10px solid {COLOR_PRIMARY};
        color: #1B4F72;
        padding: 20px;
        border-radius: 4px;
        margin-bottom: 25px;
        font-size: 18px;
    }}
    
    div.stDownloadButton > button {{
        width: 100%;
        background-color: {COLOR_PRIMARY};
        color: white;
        font-size: 18px;
        padding: 10px;
        border-radius: 8px;
    }}
    </style>
""", unsafe_allow_html=True)

# --- CARGA DE DATOS ---
def cargar_csv_super_flexible(filepath):
    encodings = ['utf-8', 'latin-1', 'cp1252', 'ISO-8859-1']
    separators = [',', ';']
    for encoding in encodings:
        for sep in separators:
            try:
                df = pd.read_csv(filepath, sep=sep, encoding=encoding)
                if df.shape[1] > 1: return df
            except Exception: continue
    return pd.DataFrame()

@st.cache_data
def load_data():
    files = {
        "leyes": "Auditoría Negocio ALA.xlsx - Leyes pesos y diferencias.csv",
        "orotec": "Auditoría Negocio ALA.xlsx - base orotec.csv",
        "gold": "Auditoría Negocio ALA.xlsx -  base gold price.csv",
        "bases": "Auditoría Negocio ALA.xlsx - comparacion de bases.csv"
    }
    loaded = {}
    for key, name in files.items():
        if os.path.exists(name):
            loaded[key] = cargar_csv_super_flexible(name)
        else:
            loaded[key] = None
    return loaded["leyes"], loaded["orotec"], loaded["gold"], loaded["bases"]

# --- PROCESAMIENTO ---
df_leyes, df_orotec, df_gold, df_bases = load_data()

if df_leyes is not None and not df_leyes.empty:
    
    # Normalización
    for df in [df_leyes, df_orotec, df_gold, df_bases]:
        if df is not None:
            df.columns = df.columns.str.lower().str.strip()

    # Limpieza
    def limpiar_nums(df, cols):
        if df is None: return df
        for col in cols:
            if col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '.').str.replace(' ', '')
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df

    if 'no' in df_leyes.columns:
        df_leyes['no'] = pd.to_numeric(df_leyes['no'], errors='coerce').fillna(0).astype(int)

    df_leyes = limpiar_nums(df_leyes, ['peso taller', 'peso factura', 'diferencia en valor', 'ley taller', 'ley jerusalen', 'diferencia peso oro puro', 'peso oro puro real', 'peso oro puro factura'])
    
    if df_bases is not None:
        cols_to_clean = [c for c in df_bases.columns if c != 'fecha']
        df_bases = limpiar_nums(df_bases, cols_to_clean)

    df_orotec = limpiar_nums(df_orotec, ['base orotec']) 
    df_gold = limpiar_nums(df_gold, ['base oro gold', 'base medellin']) 

    # Fechas
    for df in [df_leyes, df_orotec, df_gold, df_bases]:
        if df is not None and 'fecha' in df.columns:
            df['fecha_dt'] = pd.to_datetime(df['fecha'], errors='coerce')
            df['fecha_norm'] = df['fecha_dt'].dt.strftime('%Y-%m-%d')
            df.sort_values('fecha_dt', inplace=True)

    # --- INTERFAZ GRÁFICA ---
    st.markdown("### 🚨 Monitor de Control (Pérdidas y Diferencias)")
    st.markdown("---")
    
    # PESTAÑAS (AUDITORÍA PURA)
    tab1, tab_bases, tab3, tab4, tab5 = st.tabs([
        "💸 Fugas de Capital", 
        "📉 Análisis de Bases", 
        "⚖️ Auditoría de Gramajes",
        "🧪 Análisis de Leyes",
        "📅 Detalle Operativo Diario"
    ])

    # --- PESTAÑA 1: FUGAS ---
    with tab1:
        st.subheader("Resumen de Fugas Detectadas")
        
        IMPASSE_VALOR = 1531798.20
        IMPASSE_PESO = 3.69
        
        col_val = 'diferencia en valor'
        df_perdidas = df_leyes[df_leyes[col_val] < 0].copy()
        
        fuga_operativa = df_perdidas[col_val].sum()
        gramos_faltantes_op = df_leyes[df_leyes['diferencia peso oro puro'] > 0]['diferencia peso oro puro'].sum()
        
        total_dinero_perdido = fuga_operativa + (-IMPASSE_VALOR)
        total_gramos_perdidos = gramos_faltantes_op + IMPASSE_PESO
        dias_con_fugas = len(df_perdidas) + 1 

        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Dinero Faltante Total", f"${abs(total_dinero_perdido):,.0f}", delta="Diferencia Económica", delta_color="inverse")
        with c2: st.metric("Oro Puro Faltante", f"{total_gramos_perdidos:.2f} g", delta="Merma + Impasse", delta_color="inverse")
        with c3: st.metric("Días con Incidencias", f"{dias_con_fugas}", help="Días con diferencias + Impasse")

        # BOTÓN DESCARGA
        csv_fugas = df_perdidas.to_csv(index=False).encode('utf-8')
        st.download_button(label="💾 Descargar Reporte de Fugas (CSV)", data=csv_fugas, file_name='reporte_fugas.csv', mime='text/csv')

        # NOTA CLARA
        st.markdown(f"""
        <div class='method-box'>
        <b>ℹ️ Origen de las Diferencias:</b><br>
        1. <b>Fuga Operativa:</b> Es la diferencia matemática entre lo que dice la factura y el cálculo real (Peso × Ley).<br>
        2. <b>Impasse (19/05/2025):</b> Pérdida específica reportada por espectrometría de <b>{IMPASSE_PESO} g</b> (${IMPASSE_VALOR:,.0f}).
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        
        st.markdown("#### 📢 Hallazgos Administrativos (Observaciones)")
        hallazgos = []
        
        if 'observaciones' in df_gold.columns:
            for idx, row in df_gold.iterrows():
                obs = str(row['observaciones']).lower()
                fecha = row['fecha_norm']
                obs_real = row['observaciones']
                
                if fecha == '2025-11-27': obs_real = "⚠️ Yarden pone en la factura más de lo que debería pagar. " + str(obs_real)
                if fecha == '2025-05-19': continue 
                if len(obs) > 4 and "nan" not in obs and "ok" not in obs:
                    hallazgos.append({"Fecha": fecha, "Observación": obs_real})
                    
        if 'observaciones' in df_orotec.columns:
             for idx, row in df_orotec.iterrows():
                obs = str(row['observaciones']).lower()
                fecha = row['fecha_norm']
                obs_real = row['observaciones']
                if fecha == '2025-11-27': obs_real = "⚠️ Yarden pone en la factura más de lo que debería pagar. " + str(obs_real)
                if fecha == '2025-05-19': continue 
                if len(obs) > 4 and "nan" not in obs and "ok" not in obs and "referencia" not in obs:
                    hallazgos.append({"Fecha": fecha, "Observación": obs_real})

        if hallazgos:
            df_hallazgos = pd.DataFrame(hallazgos).drop_duplicates()
            def resaltar(row): return ['background-color: #F9E79F; color: #7D6608; font-weight: bold'] * len(row) if row['Fecha'] == '2025-11-27' else [''] * len(row)
            st.dataframe(df_hallazgos.style.apply(resaltar, axis=1), use_container_width=True, hide_index=True)
        else:
            st.info("Sin observaciones adicionales.")

        st.divider()
        st.markdown("#### 📉 Días con Mayor Impacto Económico")
        df_neg = df_perdidas.sort_values(col_val).head(10).copy()
        if not df_neg.empty:
            df_neg['Pérdida ($)'] = df_neg[col_val].abs()
            fig = px.bar(df_neg, x='fecha', y='Pérdida ($)', color_discrete_sequence=[COLOR_DANGER])
            fig.update_layout(template="plotly_white", font=dict(size=18))
            st.plotly_chart(fig, use_container_width=True)

    # --- PESTAÑA 2: BASES ---
    with tab_bases:
        st.subheader("📉 Auditoría de Bases de Liquidación")
        
        if df_bases is not None and not df_bases.empty:
            c_ala = next((c for c in df_bases.columns if 'ala' in c), None)
            c_cap = next((c for c in df_bases.columns if '4%' in c or 'compra' in c), None)
            c_acu = next((c for c in df_bases.columns if '93%' in c or 'acuerdo' in c), None)

            if c_ala and c_cap and c_acu:
                df_view = df_bases.copy()
                for col in [c_ala, c_cap, c_acu]:
                    if df_view[col].mean() < 10000: df_view[col] = df_view[col] * 1000
                
                df_view['Dif Capital'] = df_view[c_ala] - df_view[c_cap]
                dias_alerta = (df_view['Dif Capital'] < 0).sum()
                
                st.markdown("#### 📋 Control de Precios ($/g)")
                k1, k2, k3 = st.columns(3)
                with k1: st.metric("Costo Compra (Referencia)", f"${df_view[c_cap].mean():,.0f} /g", help="Precio mínimo de referencia (Suelo)")
                with k2: st.metric("Base Oficial (93% Acuerdo)", f"${df_view[c_acu].mean():,.0f} /g", help="Base objetiva para cálculo de utilidad")
                with k3: st.metric("Referencia ALA (Real)", f"${df_view[c_ala].mean():,.0f} /g", delta=f"${df_view[c_ala].mean() - df_view[c_cap].mean():,.0f} vs Costo")

                st.divider()

                # NOTA CLARA SOBRE EL 93%
                st.markdown(f"""
                <div class='method-box'>
                <b>ℹ️ Regla de Negocio (Bases):</b><br>
                • <b>Costo de Compra:</b> Es solo una referencia del "suelo" o costo del taller.<br>
                • <b>Base 93% (Oficial):</b> Es la <b>meta obligatoria</b>. La utilidad siempre debe calcularse o compararse contra este valor acordado. Si la referencia ALA está por debajo, se está perdiendo valor.
                </div>
                """, unsafe_allow_html=True)

                if dias_alerta > 0:
                    st.markdown(f"""<div class='capital-alert'>🚨 ALERTA CRÍTICA: En <b>{dias_alerta} días</b>, la referencia ALA fue INFERIOR incluso al costo de compra.</div>""", unsafe_allow_html=True)

                st.markdown("#### 📈 Comparativa de Bases ($/gramo)")
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_view['fecha'], y=df_view[c_cap], name="Costo Compra (Ref)", line=dict(color='black', width=3, dash='dot')))
                fig.add_trace(go.Scatter(x=df_view['fecha'], y=df_view[c_acu], name="Base Oficial (93%)", line=dict(color=COLOR_SUCCESS, width=3)))
                fig.add_trace(go.Scatter(x=df_view['fecha'], y=df_view[c_ala], name="Ref. ALA (Ejecución)", line=dict(color=COLOR_DANGER, width=4)))
                
                fig.add_trace(go.Scatter(x=df_view['fecha'], y=df_view[c_cap], mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip'))
                fig.add_trace(go.Scatter(x=df_view['fecha'], y=df_view[c_ala], mode='lines', line=dict(width=0), fill='tonexty', fillcolor='rgba(192, 57, 43, 0.2)', showlegend=False, hoverinfo='skip'))
                
                fig.update_layout(template="plotly_white", height=500, font=dict(size=16), legend=dict(orientation="h", y=1.1))
                st.plotly_chart(fig, use_container_width=True)

                st.markdown("#### 🗓️ Detalle Diario")
                df_table = df_view[['fecha', c_cap, c_acu, c_ala, 'Dif Capital']].copy()
                df_table.columns = ['Fecha', 'Costo Compra ($/g)', 'Base Oficial 93% ($/g)', 'Ref. ALA ($/g)', 'Dif vs Costo ($/g)']
                def color_red(val): return f'color: {"red" if val < 0 else "black"}; font-weight: bold;'
                st.dataframe(df_table.style.format({"Costo Compra ($/g)": "${:,.0f}", "Base Oficial 93% ($/g)": "${:,.0f}", "Ref. ALA ($/g)": "${:,.0f}", "Dif vs Costo ($/g)": "${:,.0f}"}).applymap(color_red, subset=['Dif vs Costo ($/g)']), use_container_width=True)
            else: st.error("Error en columnas de bases.")

    # --- PESTAÑA 3: PESOS ---
    with tab3:
        st.subheader(" Auditoría de Gramajes (Faltantes Físicos)")
        
        st.markdown("""
        <div class='method-box'>
        <b>⚖️ Control Físico:</b> Comparación estricta entre el <b>Peso Bruto</b> que salió del taller vs. el <b>Peso Bruto</b> recibido y facturado (antes de fundición/purificación).
        </div>
        """, unsafe_allow_html=True)
        
        df_view = df_leyes.copy()
        df_view['diff_peso'] = df_view['peso taller'] - df_view['peso factura']
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Peso Salida Taller", f"{df_view['peso taller'].sum():,.2f} g")
        with c2: st.metric("Peso Llegada Factura", f"{df_view['peso factura'].sum():,.2f} g")
        with c3: st.metric("Merma Física", f"{df_view['diff_peso'].sum():,.2f} g", delta_color="inverse")
        
        st.divider()
        
        # TABLA RECUPERADA (Detalle de Mermas)
        st.markdown("#### 📉 Detalle de Mermas de Peso (> 1g)")
        df_s = df_view[df_view['diff_peso'].abs() > 1.0].sort_values('fecha_dt', ascending=False)
        
        fig_p = go.Figure()
        fig_p.add_trace(go.Bar(x=df_s['fecha'], y=df_s['peso taller'], name='Taller', marker_color=COLOR_SUCCESS))
        fig_p.add_trace(go.Bar(x=df_s['fecha'], y=df_s['peso factura'], name='Factura', marker_color=COLOR_DANGER))
        fig_p.update_layout(template="plotly_white", legend=dict(orientation="h", y=1.1), font=dict(size=16))
        st.plotly_chart(fig_p, use_container_width=True)
        
        st.dataframe(df_s[['fecha', 'peso taller', 'peso factura', 'diff_peso']].style.format("{:.2f}", subset=['peso taller', 'peso factura', 'diff_peso']), use_container_width=True)

    # --- PESTAÑA 4: CALIDAD (Análisis de Leyes) ---
    with tab4:
        st.subheader("🧪 Análisis de Leyes (Pureza)")
        df_q = df_leyes.copy()
        df_q['diff'] = df_q['ley taller'] - df_q['ley jerusalen']
        
        # 1. MERMA DE LEY
        st.markdown("#### 🔻 Merma de Ley (Taller > Jerusalén)")
        st.caption("Casos donde la ley medida en el Taller fue SUPERIOR a la reconocida en Factura.")
        df_mermas = df_q[df_q['diff'] > 0.001].sort_values('fecha_dt', ascending=False)
        if not df_mermas.empty:
            fig1 = px.bar(df_mermas, x='diff', y='fecha', orientation='h', text='diff', title="Discrepancia Negativa (Merma)")
            fig1.update_traces(marker_color=COLOR_DANGER, texttemplate='%{text:.4f}')
            fig1.update_layout(template="plotly_white", font=dict(size=14))
            st.plotly_chart(fig1, use_container_width=True)
            st.dataframe(df_mermas[['fecha', 'ley taller', 'ley jerusalen', 'diff']].style.format("{:.4f}", subset=['ley taller', 'ley jerusalen', 'diff']), use_container_width=True)
        else: st.success("Sin mermas significativas de ley.")

        st.divider()
        
        # 2. ALZA DE LEY (RECUPERADO EL GRÁFICO)
        st.markdown("#### 🟢 Alza de Ley (Jerusalén > Taller)")
        st.caption("Casos donde la ley de Factura fue SUPERIOR a la del Taller.")
        
        df_ganancia = df_q[(df_q['diff'] < -0.001) & (df_q['ley taller'] > 0.01)].sort_values('fecha_dt', ascending=False)
        df_ganancia['diff_abs'] = df_ganancia['diff'].abs()
        
        if not df_ganancia.empty:
            # Gráfico de Alza de Ley
            fig2 = px.bar(df_ganancia, x='diff_abs', y='fecha', orientation='h', text='diff_abs', title="Diferencia Positiva (Alza)")
            fig2.update_traces(marker_color=COLOR_SUCCESS, texttemplate='%{text:.4f}')
            fig2.update_layout(template="plotly_white", font=dict(size=14))
            st.plotly_chart(fig2, use_container_width=True)
            
            st.dataframe(df_ganancia[['fecha', 'ley taller', 'ley jerusalen', 'diff_abs']].style.format("{:.4f}", subset=['ley taller', 'ley jerusalen', 'diff_abs']), use_container_width=True)
        else:
            st.info("No hay registros de alza de ley.")

    # --- PESTAÑA 5: DETALLE OPERATIVO ---
    with tab5:
        st.header("📅 Consulta Detallada (Operativa y Bases)")
        fechas = df_gold['fecha_norm'].dropna().unique()
        f_sel = st.selectbox("Fecha:", fechas)

        if f_sel:
            row_g = df_gold[df_gold['fecha_norm'] == f_sel].iloc[0]
            row_l = df_leyes[df_leyes['fecha_norm'] == f_sel]
            
            p_taller, p_factura, op_taller, op_factura = 0,0,0,0
            if not row_l.empty:
                p_taller = row_l['peso taller'].sum()
                p_factura = row_l['peso factura'].sum()
                if 'peso oro puro real' in row_l.columns:
                    op_taller = row_l['peso oro puro real'].sum()
                else: op_taller = (row_l['peso taller'] * row_l['ley taller']).sum()
                if 'peso oro puro factura' in row_l.columns:
                    op_factura = row_l['peso oro puro factura'].sum()
                else: op_factura = (row_l['peso factura'] * row_l['ley jerusalen']).sum()

            st.divider()
            
            st.markdown("### ⚖️ Balance de Masa y Pureza")
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Peso Bruto Taller", f"{p_taller:,.2f} g")
            with c2: st.metric("Peso Bruto Factura", f"{p_factura:,.2f} g")
            with c3: st.metric("Oro Puro Real", f"{op_taller:,.2f} g")
            with c4: st.metric("Oro Puro Factura", f"{op_factura:,.2f} g")
            
            st.markdown("---")
            st.markdown("### 💵 Auditoría de Bases Financieras")
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                st.metric("Gold Price (Internacional)", f"${row_g.get('base oro gold', 0):,.0f}")
            with c_f2:
                st.metric("Base Oficial (93%)", f"${row_g.get('base medellin', 0):,.0f}", delta_color="inverse")

else:
    st.warning("Esperando datos... Sube los 4 archivos CSV al repositorio.")
