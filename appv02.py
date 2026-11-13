import streamlit as st
import numpy as np
import random
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import os

# Configuración principal de la página web
st.set_page_config(page_title="Componentes Conexas", layout="wide")

# ==========================================
# CSS PERSONALIZADO PARA OPTIMIZAR ESPACIOS, BORDES Y COLORES
# ==========================================
st.markdown('''
<style>
    /* Reducir el tamaño de alerta/reporte */
    div[data-testid="stAlert"] {
        padding: 0.5rem 1rem !important;
    }
    div[data-testid="stAlert"] p {
        font-size: 15px !important;
        margin-bottom: 0.2rem !important;
    }
    
    /* CENTRAR TABLAS (st.table), reducir espacios y aumentar bordes */
    .stTable {
        margin: 0 auto !important;
        width: auto !important;
        border-collapse: collapse !important;
    }
    /* Estilo de bordes más gruesos para celdas de las tablas normales */
    .stTable th, .stTable td {
        text-align: center !important;
        padding: 0.4rem 0.8rem !important;
        border: 2px solid #888888 !important; 
    }
    
    /* COLORES CHEVERES PARA LOS ENCABEZADOS (LETRAS DE LOS NODOS) */
    .stTable th {
        color: #F59E0B !important; /* Color Ambar/Dorado brillante */
        background-color: rgba(128, 128, 128, 0.15) !important; /* Fondo sutil para separarlo de los números */
        font-size: 16px !important;
        font-weight: 900 !important;
    }
    
    /* Centrar contenedor de la tabla interactiva (checkboxes) y añadir borde a sus celdas */
    div[data-testid="stDataFrame"] {
        margin: 0 auto;
    }
    div[data-testid="stDataFrame"] div[data-testid="StyledFullScreenButton"] {
        display: none; 
    }
    div[data-testid="stDataFrame"] > div {
        border: 2px solid #888888 !important;
    }
    
    /* REDUCIR TAMAÑO Y CENTRAR LA IMAGEN DE WARSHALL */
    div[data-testid="stImage"] img {
        max-width: 250px !important; 
        margin: 0 auto !important;
        display: block !important;
    }

</style>
''', unsafe_allow_html=True)

# Título y descripción de la interfaz
st.title("🧩 Análisis de Componentes Conexas")
st.markdown("Cálculo de matriz de caminos mediante el **Algoritmo de Warshall** para grafos dirigidos.")

# --- SECCIÓN HISTÓRICA CON FOTO DE WARSHALL ---
with st.expander("ℹ️ ¿Quién fue Warshall y qué es la Cerradura Transitiva?"):
    col_txt, col_img = st.columns([3, 1])
    with col_txt:
        texto_historia = (
            "**Stephen Warshall (1935 – 2006)** fue un destacado investigador y científico de la computación "
            "estadounidense. En 1962, publicó este elegante algoritmo que revolucionó la forma de encontrar "
            "conectividad en grandes redes de datos.

"
            "**¿Qué es la Cerradura Transitiva?**
"
            "Es el principio matemático de deducir rutas indirectas. En términos sencillos: si puedes ir del nodo "
            "**A** al **B**, y del **B** al **C**, entonces existe un camino (indirecto) de **A** hacia **C**.

"
            "El algoritmo de Warshall evalúa estas combinaciones iterativamente para transformar nuestra "
            "*Matriz de Adyacencia* (conexiones directas) en una *Matriz de Caminos* (conectividad total o cerradura transitiva)."
        )
        st.markdown(texto_historia)
    with col_img:
        # Quitamos use_container_width=True para que aplique nuestro max-width de CSS
        st.image("https://commons.wikimedia.org/wiki/Special:FilePath/S_Warshall.jpg", caption="Stephen Warshall")

# Panel lateral
st.sidebar.header("⚙️ Configuración del Grafo")
num_nodos = st.sidebar.slider("Selecciona la cantidad de nodos", min_value=4, max_value=12, value=5)
tipo_generacion = st.sidebar.radio("Tipo de generación", options=["Generación Aleatoria", "Generación Manual"])
st.sidebar.markdown("---")
st.sidebar.info(f"**Nota:** Los nodos se nombran en orden alfabético. Para {num_nodos} nodos van de la 'A' a la '{chr(65 + num_nodos - 1)}'.")

def nombre_nodo(i):
    return chr(65 + i)

def warshall_con_historial(matriz):
    n = len(matriz)
    caminos = matriz.copy().astype(int)
    historial = []
    for i in range(n):
        caminos[i][i] = 1
    historial.append(caminos.copy())
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if caminos[i][j] == 0 and caminos[i][k] == 1 and caminos[k][j] == 1:
                    caminos[i][j] = 1
        historial.append(caminos.copy())
    return historial

def generar_texto_reporte(componentes):
    texto = "**REPORTE FINAL DE COMPONENTES CONEXAS**

"
    texto += f"Número total de componentes conexas: {len(componentes)}

"
    for i, componente in enumerate(componentes, start=1):
        nombres = [nombre_nodo(nodo) for nodo in sorted(componente)]
        texto += f"Componente {i}: {{ " + ", ".join(nombres) + " }
"
    return texto

def ordenar_matriz(caminos):
    n = len(caminos)
    cantidades = np.sum(caminos, axis=1)
    primera_posicion = []
    for i in range(n):
        posiciones = np.where(caminos[i] == 1)[0]
        if len(posiciones) > 0:
            primera_posicion.append(posiciones[0])
        else:
            primera_posicion.append(n)
    orden = sorted(range(n), key=lambda i: (-cantidades[i], primera_posicion[i]))
    matriz_ordenada = caminos[np.ix_(orden, orden)]
    return matriz_ordenada, orden, cantidades

def encontrar_componentes(caminos):
    n = len(caminos)
    fuerte = ((caminos == 1) & (caminos.T == 1))
    visitados = [False] * n
    componentes = []
    for i in range(n):
        if not visitados[i]:
            comp = [j for j in range(n) if fuerte[i][j]]
            for nodo in comp:
                visitados[nodo] = True
            componentes.append(comp)
    return componentes

# ==========================================
# GRAFOS INTERACTIVOS FLEXIBLES CORREGIDOS (Letras dentro, sin reacomodo elástico)
# ==========================================
def mostrar_grafo_interactivo(matriz, componentes=None, tipo="inicial", height="350px"):
    n = len(matriz)
    net = Network(directed=True, height=height, width="100%", bgcolor="transparent")
    
    # 1. DESACTIVAR FÍSICA para que el grafo no se rompa ni rebote al arrastrar un nodo
    net.toggle_physics(False)
    
    # 2. CONFIGURAR 'shape': 'circle' para que las letras vayan DENTRO del círculo
    net.set_options('''
    var options = {
      "nodes": {
        "shape": "circle",
        "borderWidth": 2.5,
        "size": 25,
        "color": {
          "background": "white"
        },
        "font": {
          "color": "black",
          "size": 18,
          "face": "sans-serif",
          "bold": true
        }
      },
      "edges": {
        "color": {
          "inherit": false
        },
        "smooth": {
          "type": "curvedCW",
          "roundness": 0.2
        }
      }
    }
    ''')

    mapa_comp = {}
    if componentes:
        for c_idx, comp in enumerate(componentes):
            for nodo in comp:
                mapa_comp[nodo] = c_idx

    # Añadir Nodos (Generamos las posiciones x, y estáticas para que formen un círculo)
    angulos_totales = np.linspace(0, 2 * np.pi, n, endpoint=False)
    for i in range(n):
        if tipo == "componentes" and componentes:
            color_border = "#1B5E20" 
            color_hover = "#2E7D32"  
            c_idx = mapa_comp[i]
            comp = componentes[c_idx]
            idx_in_comp = comp.index(i)
            angulos_comp = np.linspace(0, 2 * np.pi, len(comp), endpoint=False)
            radio = 80 if len(comp) > 1 else 0
            cx = c_idx * 200 - ((len(componentes)-1)*100) 
            x = int(cx + np.cos(angulos_comp[idx_in_comp]) * radio)
            y = int(np.sin(angulos_comp[idx_in_comp]) * radio)
        else:
            color_border = "#0D47A1" 
            color_hover = "#1976D2"  
            radio = 130
            x = int(np.cos(angulos_totales[i]) * radio)
            y = int(np.sin(angulos_totales[i]) * radio)
            
        # Al desactivar física, pasar x e y coloca el nodo exactamente donde queremos.
        # Desde ahí el usuario puede arrastrarlo sin estropear nada más.
        net.add_node(i, label=nombre_nodo(i), x=x, y=y,
                     color={"border": color_border, "background": "white",
                            "highlight": {"border": "#F59E0B", "background": "white"},
                            "hover": {"border": color_hover, "background": "white"}})

    # Añadir Aristas (Flechas)
    for i in range(n):
        for j in range(n):
            if i != j and matriz[i][j] == 1:
                es_misma_comp = mapa_comp.get(i) == mapa_comp.get(j) if componentes else False
                
                if tipo == "componentes":
                    if es_misma_comp:
                        net.add_edge(i, j, color="#2E7D32", width=2, arrows="to")
                else:
                    net.add_edge(i, j, color="#1976D2", width=2, arrows="to")
                    
    tmp_dir = tempfile.gettempdir()
    tmp_path = os.path.join(tmp_dir, f"grafo_{random.randint(1000, 99999)}.html")
    net.save_graph(tmp_path)
    
    with open(tmp_path, "r", encoding="utf-8") as f:
        html_data = f.read()
    
    components.html(html_data, height=int(height.replace("px", "")) + 15)

def generar_aleatorio(n):
    matriz = np.zeros((n, n), dtype=int)
    nodos = list(range(n))
    random.shuffle(nodos)
    num_grupos = random.randint(2, min(3, max(2, n//2)))
    grupos = np.array_split(nodos, num_grupos)
    for grupo in grupos:
        if len(grupo) > 1:
            for i in range(len(grupo)):
                origen = grupo[i]
                destino = grupo[(i + 1) % len(grupo)]
                matriz[origen][destino] = 1
                for otro in grupo:
                    if origen != otro and random.random() < 0.5:
                        matriz[origen][otro] = 1
    for _ in range(random.randint(1, 2)):
        origen = random.choice(nodos)
        destino = random.choice(nodos)
        if origen != destino:
            matriz[origen][destino] = 1
    return matriz

# ==========================================
# FUNCIONES DE COLOR PARA PANDAS STYLER
# ==========================================
def aplicar_colores_basicos(df):
    estilos = pd.DataFrame('', index=df.index, columns=df.columns)
    for fila in df.index:
        for col in df.columns:
            if df.loc[fila, col] == 1:
                estilos.loc[fila, col] = 'color: #38BDF8; font-weight: bold;'
            else:
                estilos.loc[fila, col] = 'color: #64748B;'
    return estilos

def aplicar_colores_detalles(df):
    estilos = pd.DataFrame('', index=df.index, columns=df.columns)
    for fila in df.index:
        estilos.loc[fila, 'Nuevo Orden'] = 'color: #F59E0B; font-weight: bold;' 
        estilos.loc[fila, 'Cantidad de 1s'] = 'color: #38BDF8; font-weight: bold;' 
    return estilos

# GESTIÓN DE ESTADO
if 'reset_count' not in st.session_state:
    st.session_state['reset_count'] = 0
if 'ultimo_n' not in st.session_state or st.session_state['ultimo_n'] != num_nodos:
    st.session_state['ultimo_n'] = num_nodos
    st.session_state['matriz'] = np.zeros((num_nodos, num_nodos), dtype=int)
    st.session_state['calculado'] = False
    st.session_state['paso'] = 0
    st.session_state['reset_count'] = 0

etiquetas = [nombre_nodo(i) for i in range(num_nodos)]

if tipo_generacion == "Generación Aleatoria":
    st.subheader("🎲 Generación Aleatoria de Grafo")
    if st.button("🎲 Generar nuevo grafo aleatorio"):
        st.session_state['matriz'] = generar_aleatorio(num_nodos)
        st.session_state['calculado'] = False
        st.session_state['paso'] = 0
        
    df_matriz = pd.DataFrame(st.session_state['matriz'], index=etiquetas, columns=etiquetas)
    
    col_mat_izq, col_graf_der = st.columns([1.2, 1.8])
    with col_mat_izq:
        st.markdown("**Matriz de Adyacencia Inicial:**")
        st.table(df_matriz.style.apply(aplicar_colores_basicos, axis=None))
    with col_graf_der:
        st.markdown("**Visualización del Grafo Dirigido Inicial:**")
        mostrar_grafo_interactivo(st.session_state['matriz'], tipo="inicial", height="350px")

elif tipo_generacion == "Generación Manual":
    st.subheader("✍️ Generación Manual Interactiva")
    if st.button("🧹 Limpiar Matriz"):
        st.session_state['matriz'] = np.zeros((num_nodos, num_nodos), dtype=int)
        st.session_state['calculado'] = False
        st.session_state['paso'] = 0
        st.session_state['reset_count'] += 1
        st.rerun()

    col_mat_izq, col_graf_der = st.columns([1.2, 1.8])
    
    with col_mat_izq:
        st.markdown("Marca las casillas donde exista conexión directa (**Fila** ➡️ **Columna**).")
        df_base = pd.DataFrame(st.session_state['matriz'].astype(bool), index=etiquetas, columns=etiquetas)
        config_columnas = {nodo: st.column_config.CheckboxColumn(nodo, required=True) for nodo in etiquetas}
        llave_dinamica = f"editor_manual_{num_nodos}_{st.session_state['reset_count']}"
        
        df_editado = st.data_editor(
            df_base, 
            key=llave_dinamica,
            column_config=config_columnas,
            use_container_width=True
        )
        matriz_manual = df_editado.astype(int).to_numpy().copy()
        np.fill_diagonal(matriz_manual, 0)      
        st.session_state['matriz'] = matriz_manual
        
    with col_graf_der:
        st.markdown("**Visualización del Grafo Dirigido Inicial:**")
        mostrar_grafo_interactivo(st.session_state['matriz'], tipo="inicial", height="350px")

st.markdown("---")
st.subheader("🧠 Procesamiento Matemático y Paso a Paso")

if 'paso' not in st.session_state:
    st.session_state['paso'] = 0
    st.session_state['historial'] = []
    st.session_state['componentes'] = []
    st.session_state['calculado'] = False

if st.button("🚀 Iniciar Cálculo de Warshall"):
    matriz_actual = st.session_state['matriz'].copy()
    st.session_state['historial'] = warshall_con_historial(matriz_actual)
    matriz_final = st.session_state['historial'][-1]
    matriz_ordenada, orden, cantidades = ordenar_matriz(matriz_final)
    st.session_state['orden'] = orden
    st.session_state['cantidades'] = cantidades
    st.session_state['matriz_ordenada'] = matriz_ordenada
    st.session_state['componentes'] = encontrar_componentes(matriz_final)
    st.session_state['paso'] = 0
    st.session_state['calculado'] = True

if st.session_state['calculado']:
    historial = st.session_state['historial']
    paso_actual = st.session_state['paso']
    max_pasos = len(historial) - 1
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Anterior") and paso_actual > 0:
            st.session_state['paso'] -= 1
            st.rerun()
    with col2:
        if paso_actual == 0:
            st.markdown("<h4 style='text-align: center;'>Paso 0: Matriz Inicial (Reflexiva)</h4>", unsafe_allow_html=True)
        else:
            st.markdown(f"<h4 style='text-align: center;'>Paso {paso_actual}: Evaluando Nodo {nombre_nodo(paso_actual-1)}</h4>", unsafe_allow_html=True)
    with col3:
        if st.button("Siguiente ➡️") and paso_actual < max_pasos:
            st.session_state['paso'] += 1
            st.rerun()

    df_paso = pd.DataFrame(historial[paso_actual], index=etiquetas, columns=etiquetas)
    col_p1, col_p2, col_p3 = st.columns([1, 4, 1])
    with col_p2:
        st.table(df_paso.style.apply(aplicar_colores_basicos, axis=None))

    if paso_actual == max_pasos:
        st.success(f"¡Listo! Se ha hallado la **Cerradura Transitiva**. A partir de esta, se detectaron {len(st.session_state['componentes'])} componentes fuertemente conexas.")
        
        st.markdown("---")
        st.markdown("### 🔄 Reordenamiento de Filas y Columnas")
        
        col_reorden_izq, col_reorden_der = st.columns([1.5, 2.5])
        
        orden = st.session_state['orden']
        cantidades = st.session_state['cantidades']
        
        with col_reorden_izq:
            st.markdown("<p style='text-align: center;'><strong>1. Criterio de Ordenamiento (Nodos)</strong></p>", unsafe_allow_html=True)
            detalles_orden = pd.DataFrame({
                "Nuevo Orden": [nombre_nodo(i) for i in orden],
                "Cantidad de 1s": [cantidades[i] for i in orden]
            })
            st.table(detalles_orden.style.hide(axis="index").apply(aplicar_colores_detalles, axis=None))
        
        with col_reorden_der:
            st.markdown("<p style='text-align: center;'><strong>2. Matriz de Caminos Reordenada (Bloques)</strong></p>", unsafe_allow_html=True)
            etiquetas_ordenadas = [nombre_nodo(i) for i in orden]
            df_reordenada = pd.DataFrame(st.session_state['matriz_ordenada'], index=etiquetas_ordenadas, columns=etiquetas_ordenadas)
            
            def resaltar_bloques_diagonales(df):
                estilos = pd.DataFrame('', index=df.index, columns=df.columns)
                for fila in df.index:
                    for col in df.columns:
                        val = df.loc[fila, col]
                        if val == 1 and df.loc[col, fila] == 1:
                            estilos.loc[fila, col] = 'background-color: #2e7d32; color: white; font-weight: bold;'
                        elif val == 1:
                            estilos.loc[fila, col] = 'color: #38BDF8; font-weight: bold;'
                        else:
                            estilos.loc[fila, col] = 'color: #64748B;'
                return estilos
                
            st.table(df_reordenada.style.apply(resaltar_bloques_diagonales, axis=None))
        
        st.markdown("---")
        
        col_izq, col_der = st.columns([1.2, 2.8])
        
        with col_izq:
            st.markdown("### 📋 Reporte en Pantalla")
            texto_reporte = generar_texto_reporte(st.session_state['componentes'])
            st.info(texto_reporte.replace('\n', '  \n')) 
            
            st.download_button(
                label="📄 Descargar Reporte (.txt)",
                data=texto_reporte,
                file_name="reporte_grafos.txt",
                mime="text/plain"
            )
            
        with col_der:
            st.markdown("### 📊 Representación Gráfica")
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                st.markdown("<p style='text-align: center;'><strong>Grafo Dirigido Original (G)</strong></p>", unsafe_allow_html=True)
                mostrar_grafo_interactivo(st.session_state['matriz'], tipo="original", height="400px")
                
            with col_g2:
                st.markdown("<p style='text-align: center;'><strong>Componentes Fuertemente Conexas</strong></p>", unsafe_allow_html=True)
                mostrar_grafo_interactivo(st.session_state['matriz'], componentes=st.session_state['componentes'], tipo="componentes", height="400px")
