import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import os
import calendar
from datetime import datetime

# --- CONFIGURACIÓN INICIAL Y TEMA ---
st.set_page_config(page_title="Tablero de Control - Negocio Oro", layout="wide", page_icon="💎")

# --- PALETA DE COLORES "FINANCIAL PRO" ---
COLOR_PRIMARY = "#2C3E50"    # Azul Oscuro
COLOR_ACCENT = "#E67E22"     # Naranja/Dorado
COLOR_SUCCESS = "#27AE60"    # Verde Esmeralda
COLOR_DANGER = "#C0392B"     # Rojo Coral
COLOR_NEUTRAL = "#95A5A6"    # Gris
COLOR_BG_CARD = "#FFFFFF"    # Fondo

# --- ESTILOS CSS (MODO LEGIBILIDAD ALTA) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    /* AUMENTO DE FUENTE GENERAL (Párrafos, Tablas, Textos) */
    p, .stMarkdown, .stText, .stDataFrame {{
        font-size: 18px !important; /* Antes era estándar, ahora es grande */
    }}

    /* TEXTOS "PEQUEÑOS" (Captions, Notas) - AHORA MÁS GRANDES */
    .stCaption {{
        font-size: 16px !important; /* Subido para que se lea fácil */
        color: #555 !important;
    }}

    /* TÍTULOS */
    h1 {{ color: {COLOR_PRIMARY}; font-weight: 800; }}
    h2, h3 {{ color: {COLOR_PRIMARY}; font-weight: 700; }}

    /* TARJETAS DE MÉTRICAS (KPIs) */
    div[data-testid="metric-container"] {{
        background-color: {COLOR_BG_CARD};
        border: 1px solid #E0E0E0;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }}
    /* Etiqueta de la métrica (ej: "Total Peso") - MÁS GRANDE */
    div[data-testid="metric-container"] > label {{
        color: {COLOR_PRIMARY}; /* Más oscuro para contraste */
        font-size: 1.1rem !important; /* Aumentado */
        font-weight: 600;
    }}
    /* Valor de la métrica - GIGANTE */
    div[data-testid="metric-container"] > div:nth-child(2) {{
        color: {COLOR_PRIMARY};
        font-size: 2.2rem !important; /* Aumentado */
        font-weight: 800;
    }}

    /* PESTAÑAS MÁS LEGIBLES */
    .stTabs [data-baseweb="tab"] {{
        font-size: 18px !important;
        font-weight: 600;
        padding: 10px 20px;
    }}

    /* ALERTAS */
    .suplente-box {{
        background-color: #FFF3CD;
        border-left: 8px solid {COLOR_ACCENT};
        color: #856404;
        padding: 20px;
        border-radius: 4px;
        margin-bottom: 20px;
        font-size: 18px; /* Texto de alerta grande */
        font-weight: bold;
    }}
    
    /* BOTONES */
    .stButton > button {{
        font-size: 18px !important;
        font-weight: bold;
        padding: 12px 24px;
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
        "gold": "Auditoría Negocio ALA.xlsx -  base gold price.csv" 
    }
    for name in files.values():
        if not os.path.exists(name): return None, None, None

    df_l = cargar_csv_super_flexible(files["leyes"])
    df_o = cargar_csv_super_flexible(files["orotec"])
    df_g = cargar_csv_super_flexible(files["gold"])
    
    return df_l, df_o, df_g

# --- PROCESAMIENTO ---
df_leyes, df_orotec, df_gold = load_data()

if df_leyes is not None and not df_leyes.empty:
    
    # 1. Normalización
    for df in [df_leyes, df_orotec, df_gold]:
        df.columns = df.columns.str.lower().str.strip()

    def limpiar_nums(df, cols):
        for col in cols:
            if col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df

    if 'no' in df_leyes.columns:
        df_leyes['no'] = pd.to_numeric(df_leyes['no'], errors='coerce').fillna(0).astype(int)

    df_leyes = limpiar_nums(df_leyes, ['peso taller', 'peso factura', 'diferencia en valor', 'ley taller', 'ley jerusalen', 'diferencia peso oro puro'])
    cols_util = ['utilidad sociedad total', 'utilidad taller', 'utilidad ala']
    cols_extra_gold = ['total peso taller', 'total peso factura', 'total pagado en factura', 'compra medellin', 'base oro gold', 'base medellin', 'base venta']
    cols_extra_orotec = ['base orotec']
    
    df_orotec = limpiar_nums(df_orotec, cols_util + cols_extra_orotec)
    df_gold = limpiar_nums(df_gold, cols_util + cols_extra_gold)

    # 3. Fechas
    for df in [df_leyes, df_orotec, df_gold]:
        df['fecha_dt'] = pd.to_datetime(df['fecha'], errors='coerce')
        df['fecha_norm'] = df['fecha_dt'].dt.strftime('%Y-%m-%d')
        df.sort_values('fecha_dt', inplace=True)

    # --- INTERFAZ GRÁFICA ---
    st.markdown("### 💎 Dashboard de Auditoría Financiera")
    st.markdown("---")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🚨 Fugas de Capital", 
        "📊 Escenarios & Modelos", 
        "⚖️ Auditoría de Pesos",
        "🧪 Calidad (Leyes)",
        "📅 Consulta Diaria"
    ])

    # --- PESTAÑA 1: INCONSISTENCIAS ---
    with tab1:
        st.subheader("Resumen Ejecutivo de Diferencias")
        
        col_val = 'diferencia en valor'
        df_perdidas = df_leyes[df_leyes[col_val] < 0].copy()
        
        total_dinero_perdido = df_perdidas[col_val].sum()
        total_gramos_perdidos = df_leyes[df_leyes['diferencia peso oro puro'] > 0]['diferencia peso oro puro'].sum()
        dias_con_fugas = len(df_perdidas)

        # TARJETAS DE IMPACTO
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Dinero Faltante Acumulado", f"${total_dinero_perdido:,.0f}", delta="Impacto Financiero", delta_color="inverse")
        with c2:
            st.metric("Oro Puro Faltante", f"{total_gramos_perdidos:.2f} g", delta="Merma Material", delta_color="inverse")
        with c3:
            st.metric("Días con Inconsistencias", f"{dias_con_fugas} días", help="Días con balance negativo")

        st.markdown("### 📋 Bitácora de Observaciones")
        if 'observaciones' in df_gold.columns:
            df_obs = df_gold[df_gold['observaciones'].notna() & (df_gold['observaciones'].astype(str).str.strip() != '')].copy()
            df_obs = df_obs[df_obs['fecha_norm'] != '2025-05-19']

            def aplicar_estilos(row):
                if '2025-11-27' in str(row['Fecha']):
                    return ['background-color: #D6EAF8; color: #1B4F72; font-weight: bold; font-size: 16px'] * len(row)
                return ['font-size: 16px'] * len(row)

            mask_27 = df_obs['fecha_norm'] == '2025-11-27'
            if mask_27.any():
                df_obs.loc[mask_27, 'observaciones'] = df_obs.loc[mask_27, 'observaciones'] + " (⚠️ Inconsistencia: Pagaron más de lo debido)"

            if not df_obs.empty:
                st.dataframe(
                    df_obs[['fecha_norm', 'observaciones', 'utilidad sociedad total']]
                    .rename(columns={'fecha_norm': 'Fecha', 'observaciones': 'Detalle Observación', 'utilidad sociedad total': 'Utilidad Total'})
                    .style.apply(aplicar_estilos, axis=1)
                    .format({'Utilidad Total': '${:,.0f}'}), 
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.success("No hay observaciones relevantes.")
        
        col_graf, col_tabla = st.columns([2, 1])
        with col_graf:
            st.markdown("##### 📉 Top 10 Días Críticos")
            df_neg = df_perdidas.sort_values(col_val).head(10).copy()
            df_neg['Pérdida ($)'] = df_neg[col_val].abs()
            
            if not df_neg.empty:
                fig = px.bar(df_neg, x='fecha', y='Pérdida ($)', 
                             color_discrete_sequence=[COLOR_DANGER])
                # AUMENTAMOS TAMAÑO FUENTE GRÁFICO
                fig.update_layout(
                    template="plotly_white", 
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(size=14) # Letra más grande en gráfico
                )
                st.plotly_chart(fig, use_container_width=True)

        with col_tabla:
            st.markdown("##### 📥 Exportar Datos")
            st.info("Descarga la evidencia completa.")
            df_download = df_perdidas[['fecha', 'peso taller', 'peso factura', 'diferencia en valor']]
            csv = df_download.to_csv(index=False).encode('utf-8')
            st.download_button("Descargar Reporte Fugas (.csv)", data=csv, file_name="reporte_fugas_oro.csv", mime="text/csv", use_container_width=True)

    # --- PESTAÑA 2: ESCENARIOS ---
    with tab2:
        st.subheader("Comparativa de Modelos de Negocio")
        
        st.markdown(f"""
        <div style="background-color: #E8F6F3; border-left: 5px solid {COLOR_PRIMARY}; padding: 15px; border-radius: 5px; color: {COLOR_PRIMARY};">
        <b>📢 Nota Metodológica:</b><br>
        1. El escenario <b>'Gold Price'</b> se calcula sobre el <b>93%</b> del valor internacional.<br>
        2. En las fechas sin referencia Orotec, se utilizó el dato de <b>Medellín</b> como suplente.
        </div>
        """, unsafe_allow_html=True)
        st.write("")

        u_g_taller = df_gold['utilidad taller'].sum()
        u_g_ala = df_gold['utilidad ala'].sum()
        u_o_taller = df_orotec['utilidad taller'].sum()
        u_o_ala = df_orotec['utilidad ala'].sum()

        data_comp = [
            {'Escenario': 'Esc. Medellín (Gold 93%)', 'Entidad': 'Taller (60%)', 'Monto': u_g_taller},
            {'Escenario': 'Esc. Medellín (Gold 93%)', 'Entidad': 'ALA (40%)', 'Monto': u_g_ala},
            {'Escenario': 'Esc. Orotec', 'Entidad': 'Taller (60%)', 'Monto': u_o_taller},
            {'Escenario': 'Esc. Orotec', 'Entidad': 'ALA (40%)', 'Monto': u_o_ala},
        ]
        
        fig_comp = px.bar(pd.DataFrame(data_comp), x="Escenario", y="Monto", color="Entidad", barmode="group",
                          color_discrete_map={'Taller (60%)': COLOR_PRIMARY, 'ALA (40%)': COLOR_ACCENT})
        
        fig_comp.update_traces(
            texttemplate='<b>%{y:$,.0f}</b>', 
            textposition='outside',
            textfont_size=15, # Letra más grande en las barras
            cliponaxis=False
        )
        
        fig_comp.update_layout(
            template="plotly_white", 
            font=dict(family="Inter", size=15), # Letra base grande
            legend=dict(orientation="h", y=1.1, title=""),
            yaxis_tickformat="$,.0f",
            yaxis_title="Utilidad Neta ($)",
            xaxis_title="",
            margin=dict(t=50)
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        st.divider()

        st.subheader("📅 Días sin Referencia Orotec")
        if 'observaciones' in df_orotec.columns:
            mask_suplentes = df_orotec['observaciones'].astype(str).str.contains("no se tiene referencia", case=False, na=False)
            df_suplentes = df_orotec[mask_suplentes].copy()
            
            if not df_suplentes.empty:
                df_suplentes['mensaje_estandar'] = "No se tiene referencia Orotec"
                st.dataframe(
                    df_suplentes[['fecha', 'mensaje_estandar']]
                    .rename(columns={'fecha': 'Fecha', 'mensaje_estandar': 'Estado del Dato'}),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("✅ Integridad de datos al 100%.")

    # --- PESTAÑA 3: PESOS ---
    with tab3:
        st.subheader("Auditoría de Gramajes")
        fechas_omitir = ['2025-05-15', '2025-05-24']
        df_pesos_view = df_leyes[~df_leyes['fecha_norm'].isin(fechas_omitir)].copy()

        total_peso_taller = df_pesos_view['peso taller'].sum()
        total_peso_factura = df_pesos_view['peso factura'].sum()
        diff_total_peso = total_peso_taller - total_peso_factura

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Peso Taller (Entregado)", f"{total_peso_taller:,.2f} g")
        with c2:
            st.metric("Peso Factura (Reportado)", f"{total_peso_factura:,.2f} g")
        with c3:
            st.metric("Merma Total", f"{diff_total_peso:,.2f} g", delta=-diff_total_peso, delta_color="inverse")
        
        st.divider()

        diff_g = st.slider("Filtrar diferencias > (g):", 0.0, 20.0, 1.0)
        
        df_pesos_view['diff_peso'] = (df_pesos_view['peso taller'] - df_pesos_view['peso factura'])
        df_show = df_pesos_view[df_pesos_view['diff_peso'].abs() > diff_g]
        
        fig_p = go.Figure()
        fig_p.add_trace(go.Bar(x=df_show['fecha'], y=df_show['peso taller'], name='Taller (Real)', marker_color=COLOR_SUCCESS))
        fig_p.add_trace(go.Bar(x=df_show['fecha'], y=df_show['peso factura'], name='Factura (Reportado)', marker_color=COLOR_DANGER))
        fig_p.update_layout(
            template="plotly_white", 
            legend=dict(orientation="h", y=1.1),
            font=dict(size=14) # Letra más grande
        )
        st.plotly_chart(fig_p, use_container_width=True)
        
        st.dataframe(df_show[['fecha', 'peso taller', 'peso factura', 'diff_peso']].style.format({
            "peso taller": "{:.2f} g", 
            "peso factura": "{:.2f} g", 
            "diff_peso": "{:.2f} g"
        }), use_container_width=True)

    # --- PESTAÑA 4: CALIDAD (LEYES) ---
    with tab4:
        st.subheader("🧪 Análisis de Calidad (Desviaciones)")
        
        df_q = df_leyes[(df_leyes['ley taller'] > 0) & (df_leyes['ley jerusalen'] > 0)].copy()
        
        umbral_ley = st.slider("Filtrar diferencias mayores o iguales a:", 
                               min_value=0.00, max_value=0.50, value=0.09, step=0.01)
        
        df_q['diff_real'] = df_q['ley taller'] - df_q['ley jerusalen']
        df_q_filtered = df_q[df_q['diff_real'] >= umbral_ley].sort_values('fecha_dt', ascending=False)
        
        col_main, col_detail = st.columns([2, 1])

        with col_main:
            if not df_q_filtered.empty:
                st.markdown(f"#### 📉 Lista de Desviaciones (>= {umbral_ley})")
                
                df_q_filtered['label'] = df_q_filtered['fecha'] + " (Item " + df_q_filtered['no'].astype(str) + ")"
                
                fig_list = go.Figure()
                fig_list.add_trace(go.Bar(
                    y=df_q_filtered['label'],
                    x=df_q_filtered['diff_real'],
                    orientation='h',
                    marker_color=COLOR_ACCENT,
                    text=df_q_filtered['diff_real'],
                    texttemplate='%{text:.4f}',
                    textposition='outside'
                ))
                
                fig_list.update_layout(
                    template="plotly_white",
                    xaxis_title="Diferencia de Ley",
                    height=max(400, len(df_q_filtered) * 40), # Más espacio entre barras
                    margin=dict(l=10),
                    font=dict(family="Inter", size=14) # Letra más grande
                )
                st.plotly_chart(fig_list, use_container_width=True)

            else:
                st.success(f"✅ No hay desviaciones de calidad significativas.")

        with col_detail:
            st.markdown("#### 📋 Detalle Numérico")
            if not df_q_filtered.empty:
                st.dataframe(
                    df_q_filtered[['no', 'fecha', 'ley taller', 'ley jerusalen', 'diff_real']]
                    .rename(columns={'no': 'Item', 'fecha': 'Fecha', 'ley taller': 'Taller', 'ley jerusalen': 'Factura', 'diff_real': 'Dif.'})
                    .style.format({'Taller': '{:.3f}', 'Factura': '{:.3f}', 'Dif.': '{:.3f}'}),
                    use_container_width=True,
                    hide_index=True
                )

    # --- PESTAÑA 5: CONSULTA DIARIA ---
    with tab5:
        st.header("📅 Consulta Detallada por Día")
        
        fechas_disponibles = df_gold['fecha_norm'].dropna().unique()
        
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            fecha_sel_str = st.selectbox("Selecciona fecha:", fechas_disponibles)
        with col_sel2:
            escenario_dia = st.radio("Escenario de cálculo:", ["Escenario Medellín (Gold Price 93%)", "Escenario Orotec"], horizontal=True)

        if fecha_sel_str:
            dato_dia_gold = df_gold[df_gold['fecha_norm'] == fecha_sel_str]
            
            if not dato_dia_gold.empty:
                dato_dia_gold = dato_dia_gold.iloc[0]
                dato_dia_orotec = None
                temp_o = df_orotec[df_orotec['fecha_norm'] == fecha_sel_str]
                if not temp_o.empty: dato_dia_orotec = temp_o.iloc[0]
                
                ley_taller_val = 0
                ley_factura_val = 0
                temp_l = df_leyes[df_leyes['fecha_norm'] == fecha_sel_str]
                if not temp_l.empty:
                    ley_taller_val = temp_l.iloc[0].get('ley taller', 0)
                    ley_factura_val = temp_l.iloc[0].get('ley jerusalen', 0)

                obs_orotec = ""
                if dato_dia_orotec is not None: obs_orotec = str(dato_dia_orotec.get('observaciones', '')).lower()
                
                es_suplente = "no se tiene referencia" in obs_orotec
                alerta_suplencia = False
                
                if escenario_dia == "Escenario Orotec":
                    if dato_dia_orotec is not None:
                         utilidad_taller_dia = dato_dia_orotec.get('utilidad taller', 0)
                         utilidad_ala_dia = dato_dia_orotec.get('utilidad ala', 0)
                         base_calculo = dato_dia_orotec.get('base orotec', 0)
                         nombre_base = "Base Orotec"
                         if es_suplente:
                             nombre_base = "Base Medellín (SUPLENTE)"
                             alerta_suplencia = True
                    else:
                        utilidad_taller_dia = dato_dia_gold.get('utilidad taller', 0)
                        utilidad_ala_dia = dato_dia_gold.get('utilidad ala', 0)
                        base_calculo = dato_dia_gold.get('base medellin', 0)
                        nombre_base = "Base Medellín (Suplente)"
                        alerta_suplencia = True
                else:
                    utilidad_taller_dia = dato_dia_gold.get('utilidad taller', 0)
                    utilidad_ala_dia = dato_dia_gold.get('utilidad ala', 0)
                    base_calculo = dato_dia_gold.get('base medellin', 0)
                    nombre_base = "Base Medellín (93%)"

                base_gold_internacional = dato_dia_gold.get('base oro gold', 0)

                st.divider()
                
                if alerta_suplencia:
                    st.markdown(f"""
                    <div class='suplente-box'>
                    ⚠️ ATENCIÓN: Para este día NO existe referencia Orotec.<br>
                    El sistema está usando la base de Medellín como suplente.
                    </div>
                    """, unsafe_allow_html=True)

                obs = dato_dia_gold.get('observaciones', '')
                if pd.notna(obs) and str(obs).strip() != '':
                     st.info(f"📝 Observación: {obs}")

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown("### ⚖️ Pesos y Leyes")
                    st.metric("Peso Taller", f"{dato_dia_gold.get('total peso taller', 0):.2f} g")
                    st.metric("Peso Factura", f"{dato_dia_gold.get('total peso factura', 0):.2f} g")
                    col_l1, col_l2 = st.columns(2)
                    col_l1.metric("Ley Taller", f"{ley_taller_val:.3f}")
                    col_l2.metric("Ley Jerusalén", f"{ley_factura_val:.3f}")
                
                with c2:
                    st.markdown("### 💵 Bases y Referencias")
                    st.metric("Gold Price (Intl)", f"${base_gold_internacional:,.0f}")
                    st.metric(f"{nombre_base}", f"${base_calculo:,.0f}", delta="⚠️" if alerta_suplencia else None, delta_color="inverse")
                    st.metric("Precio Venta Real", f"${dato_dia_gold.get('base venta', 0):,.0f}")

                with c3:
                    st.markdown(f"### 💰 Reparto ({escenario_dia})")
                    st.metric("Taller (60%)", f"${utilidad_taller_dia:,.0f}", delta="Tu Ganancia")
                    st.metric("ALA (40%)", f"${utilidad_ala_dia:,.0f}")
                    cobrado = dato_dia_gold.get('total pagado en factura', 0)
                    costo_medellin = dato_dia_gold.get('compra medellin', 0)
                    st.caption(f"Margen Op. Bruto: ${cobrado - costo_medellin:,.0f}")
            else:
                st.error("Error cargando datos para la fecha seleccionada.")

else:
    st.warning("Esperando datos... Asegúrate de que los archivos estén en la carpeta correcta.")