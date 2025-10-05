import streamlit as st
import pandas as pd
import math
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

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

@st.cache_data
def get_gdp_data():
    """Grab GDP data from a CSV file.

    This uses caching to avoid having to read the file every time. If we were
    reading from an HTTP endpoint instead of a file, it's a good idea to set
    a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
    """

    # Instead of a CSV on disk, you could read from an HTTP endpoint here too.
    DATA_FILENAME = Path(__file__).parent/'data/gdp_data.csv'
    raw_gdp_df = pd.read_csv(DATA_FILENAME)

    MIN_YEAR = 1960
    MAX_YEAR = 2022

    # The data above has columns like:
    # - Country Name
    # - Country Code
    # - [Stuff I don't care about]
    # - GDP for 1960
    # - GDP for 1961
    # - GDP for 1962
    # - ...
    # - GDP for 2022
    #
    # ...but I want this instead:
    # - Country Name
    # - Country Code
    # - Year
    # - GDP
    #
    # So let's pivot all those year-columns into two: Year and GDP
    gdp_df = raw_gdp_df.melt(
        ['Country Code'],
        [str(x) for x in range(MIN_YEAR, MAX_YEAR + 1)],
        'Year',
        'GDP',
    )

    # Convert years from string to integers
    gdp_df['Year'] = pd.to_numeric(gdp_df['Year'])

    return gdp_df

gdp_df = get_gdp_data()

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
'''
# 📊 Dashboardd

Browse GDP data from the [World Bank Open Data](https://data.worldbank.org/) website. As you'll
notice, the data only goes to 2022 right now, and datapoints for certain years are often missing.
But it's otherwise a great (and did I mention _free_?) source of data.
'''

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

# 1. Selector de fechas
st.sidebar.header('Rango de fechas')
fecha_inicio = st.sidebar.date_input(
    'Fecha inicial', 
    value=pd.to_datetime('2014-01-10'),
    key=f'fecha_inicio_{st.session_state.fecha_inicio_key}'
)
fecha_final = st.sidebar.date_input(
    'Fecha final', 
    value=pd.to_datetime('2017-12-31'),
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

# 4. Selector de agrupación para gráfico ventas
st.sidebar.header('Configuración del gráfico')
agrupacion_tiempo = st.sidebar.radio(
    'Ventas agrupadas por:',
    ['Mensual', 'Trimestral', 'Anual'],
    key=f'agrupacion_{st.session_state.agrupacion_key}'
)

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







min_value = df['año'].min()
max_value = df['año'].max()

from_year, to_year = st.slider(
    'Which years are you interested in?',
    min_value=min_value,
    max_value=max_value,
    value=[min_value, max_value])

countries = gdp_df['Country Code'].unique()

if not len(countries):
    st.warning("Select at least one country")

selected_countries = st.multiselect(
    'Which countries would you like to view?',
    countries,
    ['DEU', 'FRA', 'GBR', 'BRA', 'MEX', 'JPN'])

''
''
''

# Filter the data
filtered_gdp_df = gdp_df[
    (gdp_df['Country Code'].isin(selected_countries))
    & (gdp_df['Year'] <= to_year)
    & (from_year <= gdp_df['Year'])
]

st.header('GDP over time', divider='gray')

''

st.line_chart(
    filtered_gdp_df,
    x='Year',
    y='GDP',
    color='Country Code',
)

''
''


first_year = gdp_df[gdp_df['Year'] == from_year]
last_year = gdp_df[gdp_df['Year'] == to_year]

st.header(f'GDP in {to_year}', divider='gray')

''

cols = st.columns(4)

for i, country in enumerate(selected_countries):
    col = cols[i % len(cols)]

    with col:
        first_gdp = first_year[first_year['Country Code'] == country]['GDP'].iat[0] / 1000000000
        last_gdp = last_year[last_year['Country Code'] == country]['GDP'].iat[0] / 1000000000

        if math.isnan(first_gdp):
            growth = 'n/a'
            delta_color = 'off'
        else:
            growth = f'{last_gdp / first_gdp:,.2f}x'
            delta_color = 'normal'

        st.metric(
            label=f'{country} GDP',
            value=f'{last_gdp:,.0f}B',
            delta=growth,
            delta_color=delta_color
        )
