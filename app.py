import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --- CONFIGURACIÓN INICIAL Y TEMA ---
st.set_page_config(page_title="Tablero de Control - Negocio Oro", layout="wide", page_icon="💎")

# --- PALETA DE COLORES "FINANCIAL PRO" ---
COLOR_PRIMARY = "#2C3E50"    # Azul Oscuro
COLOR_ACCENT = "#E67E22"     # Naranja/Dorado
COLOR_SUCCESS = "#27AE60"    # Verde Esmeralda
COLOR_DANGER = "#C0392B"     # Rojo Coral
COLOR_NEUTRAL = "#95A5A6"    # Gris
COLOR_BG_CARD = "#FFFFFF"    # Fondo

# --- ESTILOS CSS (LEGIBILIDAD MÁXIMA) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    /* FUENTE GENERAL GRANDE */
    p, .stMarkdown, .stText, .stDataFrame {{
        font-size: 20px !important;
    }}
    
    /* ETIQUETAS */
    .stCaption {{
        font-size: 18px !important;
        color: #555 !important;
    }}

    /* TÍTULOS */
    h1 {{ color: {COLOR_PRIMARY}; font-weight: 800; font-size: 3rem; }}
    h2, h3 {{ color: {COLOR_PRIMARY}; font-weight: 700; }}

    /* TARJETAS KPI */
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
        color: {COLOR_PRIMARY};
        font-size: 3.8rem !important;
        font-weight: 900;
        line-height: 1.1;
    }}

    /* PESTAÑAS */
    .stTabs [data-baseweb="tab"] {{
        font-size: 22px !important;
        font-weight: 600;
        padding: 15px 30px;
    }}

    /* ALERTAS */
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
    
    /* BOTÓN DE DESCARGA */
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

# --- FUNCIÓN DE CARGA ---
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
    
    # 1. Normalización
    for df in [df_leyes, df_orotec, df_gold, df_bases]:
        if df is not None:
            df.columns = df.columns.str.lower().str.strip()

    # 2. Limpieza
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

    # LIMPIEZA DE LEYES
    df_leyes = limpiar_nums(df_leyes, ['peso taller', 'peso factura', 'diferencia en valor', 'ley taller', 'ley jerusalen', 'diferencia peso oro puro', 'peso oro puro real', 'peso oro puro factura'])
    
    # LIMPIEZA DE BASES
    if df_bases is not None:
        cols_to_clean = [c for c in df_bases.columns if c != 'fecha']
        df_bases = limpiar_nums(df_bases, cols_to_clean)

    # LIMPIEZA DE REPARTO
    df_orotec = limpiar_nums(df_orotec, ['utilidad sociedad total', 'utilidad taller', 'utilidad ala', 'base orotec'])
    df_gold = limpiar_nums(df_gold, ['utilidad sociedad total', 'utilidad taller', 'utilidad ala', 'total peso taller', 'total peso factura', 'total pagado en factura', 'compra medellin', 'base oro gold', 'base medellin', 'base venta'])

    # 3. Fechas
    for df in [df_leyes, df_orotec, df_gold, df_bases]:
        if df is not None and 'fecha' in df.columns:
            df['fecha_dt'] = pd.to_datetime(df['fecha'], errors='coerce')
            df['fecha_norm'] = df['fecha_dt'].dt.strftime('%Y-%m-%d')
            df.sort_values('fecha_dt', inplace=True)

    # --- INTERFAZ GRÁFICA ---
    st.markdown("### 💎 Dashboard de Auditoría Financiera")
    st.markdown("---")
    
    tab1, tab_bases, tab2, tab3, tab4, tab5 = st.tabs([
        "🚨 Fugas de Capital", 
        "📉 Análisis de Bases", 
        "📊 Escenarios (Utilidad)", 
        "⚖️ Auditoría de Pesos",
        "🧪 Calidad (Leyes)",
        "📅 Consulta Diaria"
    ])

    # --- PESTAÑA 1: FUGAS DE CAPITAL ---
    with tab1:
        st.subheader("Resumen Ejecutivo de Diferencias")
        
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
        with c1: st.metric("Dinero Faltante Total", f"${abs(total_dinero_perdido):,.0f}", delta="Pérdida Total", delta_color="inverse")
        with c2: st.metric("Oro Puro Faltante", f"{total_gramos_perdidos:.2f} g", delta="Merma + Impasse", delta_color="inverse")
        with c3: st.metric("Días de Inconsistencia", f"{dias_con_fugas}", help="Días con diferencias + Impasse")

        # BOTÓN DE DESCARGA (SOLICITADO)
        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=False).encode('utf-8')
        
        csv_fugas = convert_df(df_perdidas)
        st.download_button(
            label="💾 Descargar Reporte de Fugas (Excel/CSV)",
            data=csv_fugas,
            file_name='reporte_fugas_capital.csv',
            mime='text/csv',
        )

        st.markdown(f"""
        <div class='method-box'>
        <b>ℹ️ Aclaración sobre el Cálculo:</b><br>
        1. <b>Fuga Operativa:</b> Diferencia matemática estricta en la factura (Oro Puro Reportado vs. Oro Puro Real calculado como <i>Peso Factura × Ley Factura</i>).<br>
        2. <b>IMPASSE 19/05/2025:</b> Se incluye la pérdida por espectrometría de <b>{IMPASSE_PESO} g</b> (${IMPASSE_VALOR:,.0f}), según información compartida por ALA.
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        
        st.markdown("#### 📢 Hallazgos Administrativos (Facturas y Pagos)")
        
        hallazgos = []
        
        # Revisión archivos
        for df_source, name in [(df_gold, 'Gold Price'), (df_orotec, 'Orotec')]:
            if 'observaciones' in df_source.columns:
                for idx, row in df_source.iterrows():
                    obs = str(row['observaciones']).lower()
                    fecha = row['fecha_norm']
                    obs_real = row['observaciones']
                    
                    if fecha == '2025-11-27': obs_real = "⚠️ Yarden pone en la factura más de lo que debería pagar. " + str(obs_real)
                    if fecha == '2025-05-19': continue
                    
                    if len(obs) > 4 and "nan" not in obs and "ok" not in obs:
                        # Filtro extra para orotec
                        if name == 'Orotec' and "referencia" in obs: continue
                        hallazgos.append({"Fecha": fecha, "Observación": obs_real})

        if hallazgos:
            df_hallazgos = pd.DataFrame(hallazgos).drop_duplicates()
            def resaltar_fila_especifica(row):
                return ['background-color: #F9E79F; color: #7D6608; font-weight: bold'] * len(row) if row['Fecha'] == '2025-11-27' else [''] * len(row)
            st.dataframe(df_hallazgos.style.apply(resaltar_fila_especifica, axis=1), use_container_width=True, hide_index=True)
        else:
            st.info("No se encontraron observaciones administrativas adicionales.")

        st.divider()
        
        st.markdown("#### 📉 Desglose Diario (Operativo)")
        df_neg = df_perdidas.sort_values(col_val).head(10).copy()
        if not df_neg.empty:
            df_neg['Pérdida ($)'] = df_neg[col_val].abs()
            fig = px.bar(df_neg, x='fecha', y='Pérdida ($)', color_discrete_sequence=[COLOR_DANGER])
            fig.update_layout(template="plotly_white", font=dict(size=18))
            st.plotly_chart(fig, use_container_width=True)

    # --- PESTAÑA 2: ANÁLISIS DE BASES ---
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
                df_view['Alerta'] = df_view['Dif Capital'] < 0
                dias_alerta = df_view['Alerta'].sum()
                
                st.markdown("#### 📋 Resumen de Promedios (Precio por Gramo)")
                k1, k2, k3 = st.columns(3)
                with k1: st.metric("Promedio Base Capital (Suelo)", f"${df_view[c_cap].mean():,.0f} /g")
                with k2: st.metric("Promedio Base Acuerdo (Meta)", f"${df_view[c_acu].mean():,.0f} /g")
                with k3: st.metric("Promedio Referencia ALA (Real)", f"${df_view[c_ala].mean():,.0f} /g", delta=f"${df_view[c_ala].mean() - df_view[c_cap].mean():,.0f} vs Capital")

                st.divider()

                if dias_alerta > 0:
                    st.markdown(f"""
                    <div class='capital-alert'>
                    🚨 ALERTA DE EROSIÓN DE CAPITAL: En <b>{dias_alerta} días</b>, la referencia tomada por ALA fue INFERIOR al costo de compra del taller.<br>
                    Esto indica que se repartieron utilidades inexistentes, afectando el capital de trabajo.
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("#### 📈 Evolución Comparativa de Bases ($/gramo)")
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df_view['fecha'], y=df_view[c_cap], name="Capital (Compra Taller)", line=dict(color='black', width=3, dash='dot')))
                fig.add_trace(go.Scatter(x=df_view['fecha'], y=df_view[c_acu], name="Acuerdo (93%)", line=dict(color=COLOR_SUCCESS, width=3)))
                fig.add_trace(go.Scatter(x=df_view['fecha'], y=df_view[c_ala], name="Referencia ALA", line=dict(color=COLOR_PRIMARY, width=4)))
                fig.add_trace(go.Scatter(x=df_view['fecha'], y=df_view[c_cap], mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip'))
                fig.add_trace(go.Scatter(x=df_view['fecha'], y=df_view[c_ala], mode='lines', line=dict(width=0), fill='tonexty', fillcolor='rgba(192, 57, 43, 0.15)', showlegend=False, hoverinfo='skip'))
                fig.update_layout(template="plotly_white", height=500, font=dict(size=16), legend=dict(orientation="h", y=1.1), yaxis_title="Precio por Gramo ($)")
                st.plotly_chart(fig, use_container_width=True)

                st.markdown("#### 🗓️ Detalle Diario y Afectación")
                df_table = df_view[['fecha', c_cap, c_acu, c_ala, 'Dif Capital']].copy()
                df_table.columns = ['Fecha', 'Base Capital ($/g)', 'Base Acuerdo 93% ($/g)', 'Referencia ALA ($/g)', 'Diferencia ($/g)']
                def color_red(val): return f'color: {"red" if val < 0 else "black"}; font-weight: bold;'
                st.dataframe(df_table.style.format({"Base Capital ($/g)": "${:,.0f}", "Base Acuerdo 93% ($/g)": "${:,.0f}", "Referencia ALA ($/g)": "${:,.0f}", "Diferencia ($/g)": "${:,.0f}"}).applymap(color_red, subset=['Diferencia ($/g)']), use_container_width=True, height=400)
            else:
                st.error("No se encontraron las columnas necesarias en el archivo 'comparacion de bases.csv'.")
        else:
            st.info("Cargando datos de bases...")

    # --- PESTAÑA 3: ESCENARIOS ---
    with tab2:
        st.subheader("Comparativa de Modelos")
        # NOTA AJUSTADA (BASE OFICIAL vs REFERENCIA)
        st.markdown(f"""
        <div class='method-box'>
        <b>ℹ️ Regla de Negocio (Escenarios):</b><br>
        • <b>Escenario Medellín (93%):</b> Esta es la <b>BASE OFICIAL</b> según el Acuerdo Inicial (93% del Gold Price).<br>
        • <b>Escenario Orotec:</b> Esta base se usa solo como <b>REFERENCIA</b> para calcular la utilidad si se vendiera en Orotec. <span style='color:#C0392B'><b>¡Importante!</b></span> Si NO hay referencia Orotec, se usa automáticamente Medellín.
        </div>
        """, unsafe_allow_html=True)
        
        u_g_taller = df_gold['utilidad taller'].sum()
        u_g_ala = df_gold['utilidad ala'].sum()
        u_o_taller = df_orotec['utilidad taller'].sum()
        u_o_ala = df_orotec['utilidad ala'].sum()
        data_comp = [{'Escenario': 'Esc. Medellín (93%)', 'Entidad': 'Taller (60%)', 'Monto': u_g_taller}, {'Escenario': 'Esc. Medellín (93%)', 'Entidad': 'ALA (40%)', 'Monto': u_g_ala}, {'Escenario': 'Esc. Orotec', 'Entidad': 'Taller (60%)', 'Monto': u_o_taller}, {'Escenario': 'Esc. Orotec', 'Entidad': 'ALA (40%)', 'Monto': u_o_ala}]
        fig_comp = px.bar(pd.DataFrame(data_comp), x="Escenario", y="Monto", color="Entidad", barmode="group", color_discrete_map={'Taller (60%)': COLOR_PRIMARY, 'ALA (40%)': COLOR_ACCENT})
        fig_comp.update_traces(texttemplate='<b>%{y:$,.0f}</b>', textposition='outside', textfont_size=18, cliponaxis=False)
        fig_comp.update_layout(template="plotly_white", font=dict(size=16), legend=dict(orientation="h", y=1.1), margin=dict(t=50))
        st.plotly_chart(fig_comp, use_container_width=True)

        st.subheader("📅 Días sin Referencia Orotec")
        if 'observaciones' in df_orotec.columns:
            mask = df_orotec['observaciones'].astype(str).str.contains("no se tiene referencia", case=False, na=False)
            if mask.any(): st.dataframe(df_orotec[mask][['fecha']].assign(Mensaje="No se tiene referencia Orotec"), use_container_width=True, hide_index=True)

    # --- PESTAÑA 4: PESOS ---
    with tab3:
        st.subheader("Auditoría de Gramajes")
        st.markdown("""<div class='method-box'><b>⚖️ Nota sobre los Pesos:</b> Esta auditoría compara el <b>Peso Bruto</b> que sale del taller vs. el <b>Peso Bruto</b> registrado en la factura (antes de purificación).</div>""", unsafe_allow_html=True)
        df_view = df_leyes.copy()
        df_view['diff_peso'] = df_view['peso taller'] - df_view['peso factura']
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Peso Taller", f"{df_view['peso taller'].sum():,.2f} g")
        with c2: st.metric("Peso Factura", f"{df_view['peso factura'].sum():,.2f} g")
        with c3: st.metric("Merma Total", f"{df_view['diff_peso'].sum():,.2f} g", delta_color="inverse")
        st.divider()
        diff_g = st.slider("Filtrar > (g):", 0.0, 20.0, 1.0)
        fig_p = go.Figure()
        df_s = df_view[df_view['diff_peso'].abs() > diff_g]
        fig_p.add_trace(go.Bar(x=df_s['fecha'], y=df_s['peso taller'], name='Taller', marker_color=COLOR_SUCCESS))
        fig_p.add_trace(go.Bar(x=df_s['fecha'], y=df_s['peso factura'], name='Factura', marker_color=COLOR_DANGER))
        fig_p.update_layout(template="plotly_white", legend=dict(orientation="h", y=1.1), font=dict(size=16))
        st.plotly_chart(fig_p, use_container_width=True)
        st.dataframe(df_s[['fecha', 'peso taller', 'peso factura', 'diff_peso']], use_container_width=True)

    # --- PESTAÑA 5: CALIDAD (TERMINOLOGÍA AJUSTADA) ---
    with tab4:
        st.subheader("🧪 Análisis de Calidad (Leyes)")
        
        df_q = df_leyes.copy()
        df_q['diff'] = df_q['ley taller'] - df_q['ley jerusalen']
        
        # 1. MERMA DE LEY (Taller > Jerusalén)
        st.markdown("#### 🔻 Merma de Ley (Taller > Jerusalén)")
        st.caption("Casos donde la ley del Taller fue SUPERIOR a la de Jerusalén.")
        
        df_mermas = df_q[df_q['diff'] > 0.001].sort_values('fecha_dt', ascending=False)
        
        if not df_mermas.empty:
            fig1 = px.bar(df_mermas, x='diff', y='fecha', orientation='h', text='diff', title="Merma de Ley")
            fig1.update_traces(marker_color=COLOR_DANGER, texttemplate='%{text:.4f}')
            fig1.update_layout(template="plotly_white", font=dict(size=14))
            st.plotly_chart(fig1, use_container_width=True)
            st.dataframe(df_mermas[['fecha', 'ley taller', 'ley jerusalen', 'diff']].style.format("{:.4f}", subset=['ley taller', 'ley jerusalen', 'diff']), use_container_width=True)
        else:
            st.success("No hay mermas de ley significativas.")

        st.divider()

        # 2. ALZA DE LEY (Jerusalén > Taller)
        st.markdown("#### 🟢 Alza de Ley (Jerusalén > Taller)")
        st.caption("Casos donde la ley del Taller fue INFERIOR a la de Jerusalén.")
        
        df_ganancia = df_q[(df_q['diff'] < -0.001) & (df_q['ley taller'] > 0.01)].sort_values('fecha_dt', ascending=False)
        df_ganancia['diff_abs'] = df_ganancia['diff'].abs()

        if not df_ganancia.empty:
            fig2 = px.bar(df_ganancia, x='diff_abs', y='fecha', orientation='h', text='diff_abs', title="Alza de Ley")
            fig2.update_traces(marker_color=COLOR_SUCCESS, texttemplate='%{text:.4f}')
            fig2.update_layout(template="plotly_white", font=dict(size=14))
            st.plotly_chart(fig2, use_container_width=True)
            st.dataframe(df_ganancia[['fecha', 'ley taller', 'ley jerusalen', 'diff_abs']].style.format("{:.4f}", subset=['ley taller', 'ley jerusalen', 'diff_abs']), use_container_width=True)
        else:
            st.info("No hay casos de Alza de Ley (con datos válidos).")

    # --- PESTAÑA 6: CONSULTA DIARIA ---
    with tab5:
        st.header("📅 Consulta Detallada por Día")
        fechas = df_gold['fecha_norm'].dropna().unique()
        c_s1, c_s2 = st.columns(2)
        with c_s1: f_sel = st.selectbox("Fecha:", fechas)
        with c_s2: esc = st.radio("Escenario:", ["Escenario Medellín (93%)", "Escenario Orotec"], horizontal=True)

        if f_sel:
            row_g = df_gold[df_gold['fecha_norm'] == f_sel].iloc[0]
            row_o = df_orotec[df_orotec['fecha_norm'] == f_sel]
            row_o = row_o.iloc[0] if not row_o.empty else None
            
            row_l = df_leyes[df_leyes['fecha_norm'] == f_sel]
            
            p_taller, p_factura, op_taller, op_factura = 0,0,0,0
            if not row_l.empty:
                p_taller = row_l['peso taller'].sum()
                p_factura = row_l['peso factura'].sum()
                # Prioridad columna archivo
                if 'peso oro puro real' in row_l.columns:
                    op_taller = row_l['peso oro puro real'].sum()
                else:
                    op_taller = (row_l['peso taller'] * row_l['ley taller']).sum()
                
                if 'peso oro puro factura' in row_l.columns:
                    op_factura = row_l['peso oro puro factura'].sum()
                else:
                    op_factura = (row_l['peso factura'] * row_l['ley jerusalen']).sum()

            obs = str(row_o.get('observaciones', '')) if row_o is not None else ""
            es_sup = "no se tiene referencia" in obs.lower()
            
            if esc == "Escenario Orotec":
                if row_o is not None:
                     ut_t, ut_a, b_c, n_b = row_o.get('utilidad taller',0), row_o.get('utilidad ala',0), row_o.get('base orotec',0), "Base Orotec"
                     if es_sup: n_b = "Base Medellín (SUPLENTE)"
                else: ut_t, ut_a, b_c, n_b = 0,0,0,"Sin Datos"
            else:
                ut_t, ut_a, b_c, n_b = row_g.get('utilidad taller',0), row_g.get('utilidad ala',0), row_g.get('base medellin',0), "Base Medellín (93%)"

            st.divider()
            if es_sup and esc == "Escenario Orotec": st.warning("⚠️ Usando base suplente.")
            
            st.markdown("### ⚖️ Balance de Masa y Pureza")
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Peso Bruto Taller", f"{p_taller:,.2f} g")
            with c2: st.metric("Peso Bruto Factura", f"{p_factura:,.2f} g")
            with c3: st.metric("Oro Puro Real", f"{op_taller:,.2f} g")
            with c4: st.metric("Oro Puro Factura", f"{op_factura:,.2f} g")
            
            st.markdown("---")
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                st.markdown("### 💵 Bases Financieras")
                st.metric("Gold Price", f"${row_g.get('base oro gold', 0):,.0f}")
                st.metric(f"{n_b}", f"${b_c:,.0f}", delta_color="inverse")
            with c_f2:
                st.markdown("### 💰 Reparto")
                st.metric("Taller (60%)", f"${ut_t:,.0f}")
                st.metric("ALA (40%)", f"${ut_a:,.0f}")

            # MARGEN BRUTO
            st.markdown("---")
            st.markdown("### 📊 Resultados Consolidados")
            utilidad_total_sociedad = ut_t + ut_a
            valor_venta_estimado = op_taller * b_c if (op_taller > 0 and b_c > 0) else 1
            margen_bruto_pct = (utilidad_total_sociedad / valor_venta_estimado) * 100 if valor_venta_estimado > 1 else 0

            cm1, cm2 = st.columns(2)
            with cm1: st.metric("Utilidad Total Sociedad", f"${utilidad_total_sociedad:,.0f}")
            with cm2: st.metric("Margen Bruto Operación", f"{margen_bruto_pct:.2f}%")

else:
    st.warning("Esperando datos... Sube los 4 archivos CSV al repositorio.")
