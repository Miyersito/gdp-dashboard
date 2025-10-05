import streamlit as st
import pandas as pd
import math
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(page_title="Dashboard",
                   layout="wide",
                   page_icon="📊")

google_drive_url = f'https://drive.google.com/uc?export=download&id={"1ovtCh5Q45nukxt9HILW3qzwTCmgSqNW2"}'
df_url = pd.read_csv(google_drive_url)
df = pd.DataFrame(df_url)
df['fecha'] = pd.to_datetime(df['fecha'])

ventas_año = df.groupby(pd.Grouper(key='fecha', freq='YE'))['pre_tot'].sum().reset_index()
ventas_año['fecha'] = ventas_año['fecha'].dt.strftime('%Y')
ventas_mes = df.groupby(pd.Grouper(key='fecha', freq='ME'))['pre_tot'].sum().reset_index()

# -----------------------------------------------------------------------------
# Declare some useful functions.

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
st.title('📊 Dashboard de Ventas y Análisis de Datos')
st.title('¿Cómo han evolucionado las ventas en el tiempo?')


# Add some spacing
''
''
# Configuración de la barra lateral
st.sidebar.title('Panel de control')

# Estado de sesión para los filtros
if 'filtros_inicializados' not in st.session_state:
    st.session_state.ciudad_key = 0
    st.session_state.subgrupo_key = 0
    st.session_state.agrupacion_key = 0
    st.session_state.fecha_inicio_key = 0
    st.session_state.fecha_fin_key = 0
    st.session_state.filtros_inicializados = True

# Función para reiniciar las claves
def reset_filters():
    st.session_state.ciudad_key += 1
    st.session_state.subgrupo_key += 1
    st.session_state.agrupacion_key += 1
    st.session_state.fecha_inicio_key += 1
    st.session_state.fecha_fin_key += 1

# Botón de reinicio filtros
st.sidebar.button(' Restablecer Filtros', on_click=reset_filters)

# 4. Selector de agrupación para gráfico ventas
st.sidebar.header('Configuración del gráfico')
agrupacion_tiempo = st.sidebar.radio(
    'Ventas agrupadas por:',
    ['Mensual', 'Trimestral', 'Anual'],
    key=f'agrupacion_{st.session_state.agrupacion_key}'
)

# 1. Selector de fechas
st.sidebar.header('Rango de fechas')
fecha_inicio = st.sidebar.date_input(
    'Fecha inicial',
    value=pd.to_datetime('2014-01-10'),
    min_value=pd.to_datetime('2014-01-10'),
    max_value=pd.to_datetime('2017-12-30'),
    key=f'fecha_inicio_{st.session_state.fecha_inicio_key}'
)
fecha_final = st.sidebar.date_input(
    'Fecha final',
    value=pd.to_datetime('2017-12-30'),
    min_value=pd.to_datetime('2014-01-10'),
    max_value=pd.to_datetime('2017-12-30'),
    key=f'fecha_fin_{st.session_state.fecha_fin_key}'
)

# 2. Filtro ciudad
st.sidebar.header('Filtro geográfico')
ciudades = df['ciudad'].unique().tolist()
ciudades_seleccionadas = st.sidebar.multiselect(
    'Selecciona ciudades:',
    options=ciudades,
    default=ciudades, # Todos por defecto
    key=f'ciudad_{st.session_state.ciudad_key}'
)

# 3. Filtro subgrupo
st.sidebar.header('Filtro de subgrupos')
subgrupos = df['nom_sub'].unique().tolist()
subgrupos_seleccionados = st.sidebar.multiselect(
    'Selecciona el subgrupo:',
    options=subgrupos,
    default=subgrupos,
    key=f'subgrupo_{st.session_state.subgrupo_key}'
)





# Mostrar advertencia si no hay ciudades seleccionadas
if not ciudades_seleccionadas:
    st.warning('Por favor, selecciona al menos una ciudad para visualizar los datos.')
    st.stop()

# Mostrar advertencia si no hay subgrupos seleccionados
if not subgrupos_seleccionados:
    st.warning('Por favor, selecciona al menos un subgrupo para visualizar los datos.')
    st.stop()

# Aplicar filtros al DataFrame
df_filtrado = df[
    (df['ciudad'].isin(ciudades_seleccionadas)) &
    (df['nom_sub'].isin(subgrupos_seleccionados)) &
    (df['fecha'] >= pd.to_datetime(fecha_inicio)) &
    (df['fecha'] <= pd.to_datetime(fecha_final))
]

# Metricas claves
col1, col2 = st.columns(2)
with col1:
    st.metric('Ventas Totales en Pesos', f'${df_filtrado["pre_tot"].sum():,.0f}')
with col2:
    st.metric('Ventas Totales en Dolares', f'${df_filtrado["pre_tot_US"].sum():,.0f}')

col1, col2 = st.columns(2)
with col1:
    st.metric('Clientes Únicos', df_filtrado['cliente'].nunique())
with col2:
    st.metric('Productos Vendidos', df_filtrado['item'].nunique())

# Logica agrupar segun eleccion
if agrupacion_tiempo == 'Mensual':
    df_agrupado = df_filtrado.groupby(pd.Grouper(key='fecha', freq='M'))['pre_tot'].sum().reset_index()
    titulo_grafico = 'Evolución de Ventas Mensuales'
elif agrupacion_tiempo == 'Trimestral':
    df_agrupado = df_filtrado.groupby(pd.Grouper(key='fecha', freq='Q'))['pre_tot'].sum().reset_index()
    titulo_grafico = 'Evolución de Ventas Trimestrales'
else: # Anual
    df_agrupado = df_filtrado.groupby(pd.Grouper(key='fecha', freq='Y'))['pre_tot'].sum().reset_index()
    titulo_grafico = 'Evolución de Ventas Anuales'

st.dataframe(df)


# # Gráfico de líneas con Plotly

# fig = px.line(
#     df_agrupado, 
#     x='fecha', 
#     y='pre_tot', 
#     title=titulo_grafico)

# etiquetas = [f"{meses_español[fecha.month-1]} {fecha.year}" for fecha in fechas]
# fig.update_layout(
#     xaxis = dict(
#         tickmode='array',
#         tickvals=fechas,
#         ticktext=etiquetas
#     ),
#     xaxis_title='Fecha', 
#     yaxis_title='Ventas Totales (Pesos)')
# fig.update_xaxes(
#     dtick="M1", # Muestra un tick cada mes
#     tickformat="%b\n%Y", # Formato de fecha: Mes y Año
#     ticklabelmode="period", # Etiquetas en el inicio del periodo
#     tickangle=-45 # Rotar etiquetas para mejor legibilidad
# )
# st.plotly_chart(fig, use_container_width=True)

def formato_miles_millones(value, tick_number):
    new_value = value / 1000000
    return f'{new_value:,.0f} M'.replace(',', 'X').replace('.', ',').replace('X', '.')

fig = go.Figure()

if agrupacion_tiempo == 'Mensual':
    fechas = pd.date_range(start=df_agrupado['fecha'].min(), end=df_agrupado['fecha'].max(), freq='M')
    fig.update_layout(
    xaxis_title='Fecha', 
    yaxis_title='Ventas Totales (Pesos)',
    title=titulo_grafico
    )
    meses_español = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
    fechas = df_agrupado['fecha']
    etiquetas_personalizadas = []
    mostrar_año = []
    for fecha in df_agrupado['fecha']:
        nombre_mes = meses_español[fecha.month - 1]
        etiquetas_personalizadas.append(nombre_mes)
        if fecha.month == 1:  # Si es enero, mostrar el año
            mostrar_año.append(str(fecha.year))
        else:
            mostrar_año.append('')
    # fig.update_xaxes(title_text='Mes (Los años se indican sobre el punto de Enero)')
    for i, fecha in enumerate(fechas):
        if fecha.month == 1:  # Si es enero, añadir anotación del año
            fig.add_annotation(
                x=fecha,
                y=0,
                yref="paper",
                text=str(fecha.year),
                showarrow=False,
                yshift=-50,
                font=dict(size=13)
            )
    fig.update_xaxes(
        tickvals=fechas,
        ticktext=etiquetas_personalizadas
    )

elif agrupacion_tiempo == 'Trimestral':
    trimestres = ['Tri 1', 'Tri 2', 'Tri 3', 'Tri 4']
    fechas = df_agrupado['fecha']
    etiquetas_personalizadas = []
    mostrar_año = []
    for fecha in df_agrupado['fecha']:
        nombre_tri = trimestres[fecha.quarter-1]
        etiquetas_personalizadas.append(nombre_tri)
    if fecha.quarter == 1:  # Si es el primer mes del trimestre, mostrar el año 
        mostrar_año.append(str(fecha.year))
    else:
        mostrar_año.append('')
    
    for i, fecha in enumerate(fechas):
        if fecha.quarter == 1:  # Si es el primer mes del trimestre, añadir anotación del año
            fig.add_annotation(
                x=fecha,
                y=0,
                yref="paper",
                text=str(fecha.year),
                showarrow=False,
                yshift=-50,
                font=dict(size=13)
            )
    fig.update_layout(
        yaxis=dict(
            tickformat=',.0f',
            tickmode='array'
        ),
        xaxis = dict(
            tickmode='array',
            tickvals=fechas,
            ticktext=etiquetas_personalizadas
        ),
        xaxis_title='Fecha', 
        yaxis_title='Ventas Totales (Pesos)',
        title=titulo_grafico
    )
    fig.update_xaxes(
        tickvals=fechas,
        ticktext=etiquetas_personalizadas
    )
else:  # Anual
    fechas = df_agrupado['fecha']
    etiquetas_personalizadas = [f'{fecha.year}' for fecha in fechas]
    for i, fecha in enumerate(fechas):
        fig.add_annotation(
                x=fecha,
                y=0,
                yref="paper",
                text=str(fecha.year),
                showarrow=False,
                yshift=-50,
                font=dict(size=13)
            )
    fig.update_layout(
        xaxis = dict(
            tickmode='array',
            tickvals=fechas,
            ticktext=etiquetas_personalizadas
        ),
        xaxis_title='Fecha', 
        yaxis_title='Ventas Totales (Pesos)',
        title=titulo_grafico
    )
    fig.update_xaxes(
        tickvals=[],
        ticktext=etiquetas_personalizadas
    )

fig.add_trace(go.Scatter(
    x=fechas,
    y=df_agrupado['pre_tot'],
    mode='lines')
)


st.plotly_chart(fig, use_container_width=True)


# st.line_chart(df_agrupado, 
#               x='fecha', 
#               y='pre_tot', 
#               use_container_width=True)





# -------------------------------------------------------------------

st.title('¿Cuáles son los productos y subgrupos más rentables?')

st.subheader('Productos y subgrupos que más venden')

df_agrupado = df_filtrado.groupby(['nom_sub', 'des_item'])['pre_tot'].sum().reset_index()
df_agrupado = df_agrupado.sort_values(by='pre_tot', ascending=True).head(10)

df_agrupado['Porcentaje_Acumulado'] = df_agrupado['pre_tot'].cumsum() / df_agrupado['pre_tot'].sum() * 100
df_agrupado['Porcentaje_Del_Total'] = df_agrupado['pre_tot'] / df_agrupado['pre_tot'].sum() * 100

df_subgrupo = df_filtrado.groupby(['nom_sub'])['pre_tot'].sum().reset_index()
df_subgrupo = df_subgrupo.sort_values(by='pre_tot', ascending=True)
df_subgrupo['Porcentaje_Acumulado'] = df_subgrupo['pre_tot'].cumsum() / df_subgrupo['pre_tot'].sum() * 100

df_top_subgrupo = df_subgrupo.tail(10)

fig_subgrupo = make_subplots(specs=[[{"secondary_y": True}]])
fig_subgrupo.add_trace(
    go.Bar(
        y=df_top_subgrupo['nom_sub'],
        x=df_top_subgrupo['pre_tot'],
        name='Ventas Totales (Pesos)',
        marker_color='indianred',
        orientation='h',
    ),
    secondary_y=False,
)

fig_subgrupo.update_layout(
    title_text='Top 10 Subgrupos por Ventas Totales',
    height=600,
)
fig_subgrupo.update_xaxes(title_text='Ventas Totales (Pesos)', tickangle=0)
fig_subgrupo.update_yaxes(
    title_text='Subgrupo', 
    secondary_y=False,
    tickformat=',.0f'
)
fig_subgrupo.update_yaxes(
    title_text='Porcentaje Acumulado (%)',
    secondary_y=True,
    # tickformat='%',
    range=[0, 110]
)




df_productos = df.groupby(['nom_sub','des_item'])['pre_tot'].sum().reset_index()
df_productos = df_productos.sort_values(by='pre_tot', ascending=True)

df_productos = df_filtrado.groupby(['nom_sub','des_item'])['pre_tot'].sum().reset_index()
df_productos = df_productos.sort_values(by='pre_tot', ascending=True)

df_top_productos = df_productos.tail(10)

fig_productos = make_subplots(specs=[[{"secondary_y": True}]])
fig_productos.add_trace(
    go.Bar(
        y=df_top_productos['des_item'],
        x=df_top_productos['pre_tot'],
        name='Ventas Totales (Pesos)',
        marker_color='lightsalmon',
        orientation='h',
    ),
    secondary_y=False,
)
fig_productos.update_layout(
    title_text='Top 10 Productos por Ventas Totales',
    height=600,
)
fig_productos.update_yaxes(title_text='Producto', secondary_y=False)
fig_productos.update_xaxes(title_text='Ventas Totales (Pesos)')

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(fig_subgrupo, use_container_width=True)
with col2:
    st.plotly_chart(fig_productos, use_container_width=True)


st.subheader('Análisis de Pareto')

df_subgrupo = df_subgrupo.sort_values(by='pre_tot', ascending=False)
total_ventas = df_subgrupo['pre_tot'].sum()
ventas_acumuladas = 0
subgrupos_80 = 0

for i, row in df_subgrupo.iterrows():
    ventas_acumuladas += row['pre_tot']
    if ventas_acumuladas / total_ventas <= 0.8:
        subgrupos_80 += 1
    else:
        break

st.info(f"""
        **Principio de Pareto (Regla 80/20):**
        - {subgrupos_80} de los {len(df_subgrupo)} subgrupos de productos ({(subgrupos_80/len(df_subgrupo))*100:.1f}%)
          generan aproximadamente el 80% de las ventas totales.
        - El resto de subgrupos ({len(df_subgrupo)-subgrupos_80} productos) generan solo el 20% de las ventas.
        """)

df_productos = df_productos.sort_values(by='pre_tot', ascending=False)
ventas_totales = df_productos['pre_tot'].sum()
ventas_acumuladas = 0
productos_80 = 0

for i, row in df_productos.iterrows():
    ventas_acumuladas += row['pre_tot']
    if ventas_acumuladas / ventas_totales <= 0.8:
        productos_80 += 1
    else:
        break

st.info(f"""
        **Principio de Pareto (Regla 80/20):**
        - {productos_80} de los {len(df_productos)} productos ({(productos_80/len(df_productos))*100:.1f}%)
          generan aproximadamente el 80% de las ventas totales.
        - El resto de productos ({len(df_productos)-productos_80} productos) generan solo el 20% de las ventas.
        """)

st.subheader('Tabla de Productos que generan el 80% de las ventas')


ventas_acumuladas = 0
productos_top = []
for i, row in df_productos.iterrows():
    ventas_acumuladas += row['pre_tot']
    porcentaje_acumulado = (ventas_acumuladas / ventas_totales) * 100
    productos_top.append({
        'Producto': row['des_item'],
        'Subgrupo': row['nom_sub'],
        'Ventas Totales (Pesos)': row['pre_tot'],
        'Porcentaje del Total (%)': (row['pre_tot'] / ventas_totales) * 100,
        'Porcentaje Acumulado (%)': porcentaje_acumulado
    })

    if porcentaje_acumulado >= 80:
        break

df_top_resumen = pd.DataFrame(productos_top)
st.dataframe(df_top_resumen.style.format({
    'Ventas Totales (Pesos)': '${:,.0f}',
    'Porcentaje del Total (%)': '{:.1f}%',
    'Porcentaje Acumulado (%)': '{:.1f}%'
}))

'''
## **Conclusiones del análisis de productos y subgrupos:**
Este análisis permite identificar el 20% de productos y subgrupos que generan aproximadamente el 80% de las ventas.
Con esta información, se pueden tomar decisiones estratégicas como:
 - *Para los productos "top":* Centrar esfuerzos de marketing, asegurar si disponibilida en inventario y considerar precios premium.
 - *Para la larga cola de productos:* Evaluar su rentabilidad real; algunos podrían ser eliminados para simplificar el catálogo y reducir costos.
'''

# ------------------------------------------------------------------

st.title('¿Quiénes son nuestros mejores clientes?')

