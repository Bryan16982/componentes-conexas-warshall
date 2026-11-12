import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import random
import pandas as pd

# Configuración principal de la página web
st.set_page_config(page_title="Componentes Conexas", layout="wide")

# ==========================================
# CSS PERSONALIZADO PARA OPTIMIZAR ESPACIOS Y CENTRAR
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
    
    /* CENTRAR TABLAS (st.table) y reducir espacios de celdas */
    .stTable {
        margin: 0 auto !important; /* Centra la tabla en su contenedor */
        width: auto !important;
    }
    .stTable th, .stTable td {
        text-align: center !important; /* Centra los números */
        padding: 0.4rem 0.8rem !important; /* Disminuye el espacio de las celdas sin que sea diminuta */
    }
    
    /* Centrar contenedor de la tabla interactiva (checkboxes) */
    div[data-testid="stDataFrame"] {
        margin: 0 auto;
    }
</style>
''', unsafe_allow_html=True)

# Título y descripción de la interfaz
st.title("🧩 Análisis de Componentes Conexas")
st.markdown("Cálculo de matriz de caminos mediante el **Algoritmo de Warshall** para grafos dirigidos.")

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
    texto = "**REPORTE FINAL DE COMPONENTES CONEXAS**\n\n"
    texto += f"Número total de componentes conexas: {len(componentes)}\n\n"
    for i, componente in enumerate(componentes, start=1):
        nombres = [nombre_nodo(nodo) for nodo in sorted(componente)]
        texto += f"Componente {i}: {{ " + ", ".join(nombres) + " }\n"
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

def mostrar_grafos_comparativos(matriz, componentes):
    n = len(matriz)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))
    pos = {}
    mapa_comp = {}
    for c_idx, comp in enumerate(componentes):
        cx = c_idx * 3.5  
        cy = 0
        angulos = np.linspace(0, 2 * np.pi, len(comp), endpoint=False)
        for i, nodo in enumerate(comp):
            radio = 1.0 if len(comp) > 1 else 0
            pos[nodo] = (cx + np.cos(angulos[i]) * radio, cy + np.sin(angulos[i]) * radio)
            mapa_comp[nodo] = c_idx

    for i in range(n):
        for j in range(n):
            if i != j and matriz[i][j] == 1:
                curva = 0.15 if matriz[j][i] == 1 and i < j else (-0.15 if matriz[j][i] == 1 else 0)
                ax1.annotate("", xy=pos[j], xytext=pos[i],
                             arrowprops=dict(arrowstyle="->", connectionstyle=f"arc3,rad={curva}", linewidth=1.5, shrinkA=18, shrinkB=18, color="#1976D2"))
    for i in range(n):
        ax1.scatter(pos[i][0], pos[i][1], s=600, edgecolors="#0D47A1", facecolor="white", linewidths=2, zorder=2)
        ax1.text(pos[i][0], pos[i][1], nombre_nodo(i), ha="center", va="center", fontsize=10, fontweight="bold", zorder=3)
    ax1.set_title("Grafo Dirigido Original (G)", fontweight="bold", fontsize=11)
    ax1.axis("off")

    for i in range(n):
        for j in range(n):
            if i != j and matriz[i][j] == 1 and mapa_comp.get(i) == mapa_comp.get(j):
                curva = 0.15 if matriz[j][i] == 1 and i < j else (-0.15 if matriz[j][i] == 1 else 0)
                ax2.annotate("", xy=pos[j], xytext=pos[i],
                             arrowprops=dict(arrowstyle="->", connectionstyle=f"arc3,rad={curva}", linewidth=1.5, shrinkA=18, shrinkB=18, color="#2E7D32"))
    for i in range(n):
        ax2.scatter(pos[i][0], pos[i][1], s=600, edgecolors="#1B5E20", facecolor="white", linewidths=2, zorder=2)
        ax2.text(pos[i][0], pos[i][1], nombre_nodo(i), ha="center", va="center", fontsize=10, fontweight="bold", zorder=3)
    ax2.set_title("Componentes Fuertemente Conexas", fontweight="bold", fontsize=11)
    ax2.axis("off")
    plt.tight_layout()
    return fig

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
    st.markdown("**Matriz de Adyacencia Inicial:**")
    col1, col_t, col2 = st.columns([1, 4, 1])
    with col_t:
        st.table(df_matriz.style.set_properties(**{'text-align': 'center'}))

elif tipo_generacion == "Generación Manual":
    st.subheader("✍️ Generación Manual Interactiva")
    if st.button("🧹 Limpiar Matriz"):
        st.session_state['matriz'] = np.zeros((num_nodos, num_nodos), dtype=int)
        st.session_state['calculado'] = False
        st.session_state['paso'] = 0
        st.session_state['reset_count'] += 1
        st.rerun()

    st.markdown("Marca las casillas donde exista una conexión directa (**Fila** $\to$ **Columna**).")
    df_base = pd.DataFrame(st.session_state['matriz'].astype(bool), index=etiquetas, columns=etiquetas)
    config_columnas = {nodo: st.column_config.CheckboxColumn(nodo, required=True) for nodo in etiquetas}
    llave_dinamica = f"editor_manual_{num_nodos}_{st.session_state['reset_count']}"
    
    col_espacio1, col_tabla, col_espacio2 = st.columns([1, 4, 1])
    with col_tabla:
        df_editado = st.data_editor(
            df_base, 
            key=llave_dinamica,
            column_config=config_columnas,
            use_container_width=True
        )
    matriz_manual = df_editado.astype(int).to_numpy().copy()
    np.fill_diagonal(matriz_manual, 0)      
    st.session_state['matriz'] = matriz_manual

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
        st.table(df_paso.style.set_properties(**{'text-align': 'center'}))

    if paso_actual == max_pasos:
        st.success(f"¡Análisis completado! Se detectaron {len(st.session_state['componentes'])} componentes fuertemente conexas.")
        
        st.markdown("---")
        st.markdown("### 🔄 Reordenamiento de Filas y Columnas")
        orden = st.session_state['orden']
        cantidades = st.session_state['cantidades']
        
        detalles_orden = pd.DataFrame({
            "Nuevo Orden": [i + 1 for i in range(num_nodos)],
            "Nodo": [nombre_nodo(i) for i in orden],
            "Cantidad de 1s": [cantidades[i] for i in orden]
        })
        col_d1, col_d2, col_d3 = st.columns([1, 4, 1])
        with col_d2:
            st.table(detalles_orden.style.hide(axis="index").set_properties(**{'text-align': 'center'}))
        
        st.markdown("**Matriz de Caminos Reordenada (Bloques Diagonales):**")
        etiquetas_ordenadas = [nombre_nodo(i) for i in orden]
        df_reordenada = pd.DataFrame(st.session_state['matriz_ordenada'], index=etiquetas_ordenadas, columns=etiquetas_ordenadas)
        
        def resaltar_bloques_diagonales(df):
            estilos = pd.DataFrame('', index=df.index, columns=df.columns)
            for fila in df.index:
                for col in df.columns:
                    if df.loc[fila, col] == 1 and df.loc[col, fila] == 1:
                        estilos.loc[fila, col] = 'background-color: #2e7d32; color: white;'
            return estilos
            
        col_f1, col_f2, col_f3 = st.columns([1, 4, 1])
        with col_f2:
            st.table(df_reordenada.style.apply(resaltar_bloques_diagonales, axis=None).set_properties(**{'text-align': 'center'}))
        
        st.markdown("---")
        st.markdown("### 📋 Reporte en Pantalla")
        texto_reporte = generar_texto_reporte(st.session_state['componentes'])
        st.info(texto_reporte.replace('\n', '  \n')) 
        
        st.download_button(
            label="📄 Descargar Reporte (.txt)",
            data=texto_reporte,
            file_name="reporte_grafos.txt",
            mime="text/plain"
        )
        
        st.markdown("**Representación Gráfica:**")
        fig = mostrar_grafos_comparativos(st.session_state['matriz'], st.session_state['componentes'])
        col_g1, col_g2, col_g3 = st.columns([1, 6, 1])
        with col_g2:
            st.pyplot(fig)
