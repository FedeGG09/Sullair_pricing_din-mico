import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF


# Configuración de la app
st.set_page_config(page_title="Formulario de Cotización", layout="wide")

# Inicializar el estado de la aplicación
if "current_step" not in st.session_state:
    st.session_state.current_step = 1

if "productos" not in st.session_state:
    st.session_state.productos = []

if "datos_basicos" not in st.session_state:
    st.session_state.datos_basicos = {}

# Cargar clientes desde el CSV
try:
    clientes_csv_path = "C:\\Users\\Federico Gravina\\Downloads\\cuenta_razon_social.csv"
    df_clientes = pd.read_csv(clientes_csv_path, encoding="latin1", header=None, names=["SK_CUE_Cuenta", "VC_CUE_Razon_Social"])
    opciones_clientes = {row["SK_CUE_Cuenta"]: f'{row["SK_CUE_Cuenta"]} - {row["VC_CUE_Razon_Social"]}' for _, row in df_clientes.iterrows()}
except Exception as e:
    opciones_clientes = {}
    st.error(f"No se pudo cargar el archivo de clientes: {e}")

# Cargar lista de productos desde el CSV
try:
    productos_csv_path = "C:\\Users\\Federico Gravina\\Downloads\\lista_productos.csv"
    df_productos = pd.read_csv(productos_csv_path, encoding="utf-8-sig")
    df_productos.columns = df_productos.columns.str.strip()
    df_productos["items_SK_PRD_Producto"] = df_productos["items_SK_PRD_Producto"].astype(str)
    df_productos["producto_VC_PRD_Categoria2"] = df_productos["producto_VC_PRD_Categoria2"].astype(str)
    df_productos["producto_VC_PRD_Categoria3"] = df_productos["producto_VC_PRD_Categoria3"].astype(str)
    df_productos = df_productos[["items_SK_PRD_Producto", "producto_VC_PRD_Categoria2", "producto_VC_PRD_Categoria3"]]
    df_productos.columns = ["Código", "Categoría 2", "Categoría 3"]
    df_productos["Producto Completo"] = df_productos["Código"] + " - " + df_productos["Categoría 2"] + " - " + df_productos["Categoría 3"]
    lista_productos = df_productos["Producto Completo"].tolist()
except Exception as e:
    lista_productos = []
    st.error(f"No se pudo cargar el archivo de productos: {e}")

# Lista de sucursales
sucursales = [
    "Bahía Blanca", "Buenos Aires", "Neuquén", "Comodoro Rivadavia",
    "Córdoba", "Mendoza", "Tucumán", "Rosario", "Panamericana", "Salta", "Mar Del Plata"
]

# Cargar el DataFrame de entrenamiento
try:
    df_entrenamiento_path = "C:/Users/Federico Gravina/Desktop/modelo final/df_6_enero_entrenamiento_binario_2.csv"
    df_entrenamiento = pd.read_csv(df_entrenamiento_path)
    st.success("Datos de entrenamiento cargados correctamente.")
except Exception as e:
    st.error(f"Error al cargar el datos: {e}")
    df_entrenamiento = None

# Paso 1: Carga de datos
if st.session_state.current_step == 1:
    st.title("Formulario de Cotización - Paso 1: Carga de Datos")

    with st.container():
        st.markdown("### Datos Básicos y Productos")
        with st.form("datos_basicos_form"):
            # Datos básicos
            with st.expander("Datos Básicos"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    fecha = st.date_input("Fecha", value=pd.Timestamp.now())
                with col2:
                    cliente = st.selectbox(
                        "Cliente",
                        options=list(opciones_clientes.keys()),
                        format_func=lambda x: opciones_clientes.get(x, "Selecciona un cliente")
                    )
                with col3:
                    sucursal = st.selectbox("Sucursal", options=sucursales, help="Selecciona la sucursal")
                col4, col5 = st.columns(2)
                with col4:
                    plazo = st.text_input("Plazo", placeholder="Plazo del contrato")
                with col5:
                    volumen = st.number_input("Volumen Total del Contrato", min_value=0.0, step=1000.0)

            # Productos
            st.markdown("#### Productos")
            col1, col2 = st.columns(2)
            with col1:
                producto_seleccionado = st.selectbox("Producto", options=lista_productos, placeholder="Selecciona un producto")
            with col2:
                precio_lista = st.number_input("Precio de lista (USD)", min_value=0.0, step=100.0)

            col_izq, col_der = st.columns([3, 1])
            with col_der:
                agregar_producto = st.form_submit_button("Agregar Producto")
                eliminar_producto = st.form_submit_button("Eliminar Producto")

                if agregar_producto and producto_seleccionado and precio_lista > 0:
                    codigo_producto = producto_seleccionado.split(" - ")[0]
                    st.session_state.productos.append({
                        "Producto": codigo_producto,
                        "Precio lista (USD)": precio_lista
                    })
                    st.success(f"Producto {producto_seleccionado} agregado.")
                elif eliminar_producto and st.session_state.productos:
                    st.session_state.productos.pop()
                    st.success("Último producto eliminado.")

            st.markdown("#### Productos Agregados")
            if st.session_state.productos:
                df_productos = pd.DataFrame(st.session_state.productos)
                st.table(df_productos)
            else:
                st.info("No hay productos agregados aún.")

            continuar = st.form_submit_button("GENERAR COTIZACIÓN")
            if continuar and cliente and sucursal:
                st.session_state.datos_basicos = {
                    "Fecha": fecha,
                    "Cliente": cliente,
                    "Sucursal": sucursal,
                    "Plazo": plazo,
                    "Volumen Total": volumen
                }
                st.session_state.current_step = 2
            elif continuar:
                st.error("Por favor, complete todos los campos obligatorios.")
                
# Paso 2: Cotización
elif st.session_state.current_step == 2:
    st.title("Formulario de Cotización - Paso 2: Cotización")

    # Mostrar resumen de datos básicos
    st.subheader("Datos Básicos")
    for key, value in st.session_state.datos_basicos.items():
        st.write(f"**{key}:** {value}")

    # Generar predicciones con el modelo
    st.subheader("Cotización con Predicciones de Rangos")
    if st.session_state.productos:
        cotizacion_data = []
        for producto in st.session_state.productos:
            precio_lista = producto["Precio lista (USD)"]

            # Crear un DataFrame con las características del producto (simulación de rangos)
            caracteristicas = pd.DataFrame([{
                "precio_entrenamiento_final": precio_lista,
                "Fidelizacion": st.session_state.datos_basicos.get("Volumen Total", 0)
            }])

            # Simulación simple de rangos (ajustar según tu lógica de negocio)
            rango_min = precio_lista * 0.8  # Ejemplo: 80% del precio lista
            rango_max = precio_lista * 1.2  # Ejemplo: 120% del precio lista

            cotizacion_data.append({
                "Producto": producto["Producto"],
                "Precio lista (USD)": precio_lista,
                "Rango Máximo (USD)": round(rango_max, 2),
                "Rango Mínimo (USD)": round(rango_min, 2)
            })

        df_cotizacion = pd.DataFrame(cotizacion_data)
        st.table(df_cotizacion)

        fig, ax = plt.subplots(figsize=(6, 4))  # Cambia el tamaño aquí (ancho, alto)

        st.subheader("Gráfico de Optimización de Precios")
        for producto in st.session_state.productos:
            precio_lista = producto["Precio lista (USD)"]

            # Crear datos de ejemplo para simulación
            precios_simulados = np.linspace(precio_lista * 0.8, precio_lista * 1.2, 50)
            probabilidades_simuladas = []

            # Simulación de probabilidades (ajustar según tus necesidades)
            for precio in precios_simulados:
                # Este es un ejemplo de cómo podrías simular probabilidades
                probabilidad = np.clip(1 - abs((precio - precio_lista) / precio_lista), 0, 1)
                probabilidades_simuladas.append(probabilidad)

            # Crear el gráfico con ejes invertidos
            fig, ax = plt.subplots()
            ax.plot(precios_simulados, probabilidades_simuladas, label=producto["Producto"])
            ax.set_ylabel("Probabilidad de Éxito (%)")
            ax.set_xlabel("Precio USD")
            ax.set_title(f"Optimización de Precio para {producto['Producto']}")
            ax.grid(True)
            ax.legend()

            # Mostrar el gráfico en Streamlit
            st.pyplot(fig)
    else:
        st.error("No se pudo generar la cotización. Verifique que los productos estén registrados.")

    # Opción para guardar como PDF
    if st.button("Guardar Cotización como PDF"):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Título
        pdf.set_font("Arial", style="B", size=16)
        pdf.cell(200, 10, txt="Cotización Generada", ln=True, align="C")
        pdf.ln(10)

        # Datos básicos
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Datos Básicos:", ln=True)
        for key, value in st.session_state.datos_basicos.items():
            pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)

        pdf.ln(10)

        # Detalles de productos cotizados
        pdf.cell(200, 10, txt="Productos Cotizados:", ln=True)
        for index, row in df_cotizacion.iterrows():
            pdf.cell(200, 10, txt=f"Producto: {row['Producto']}", ln=True)
            pdf.cell(200, 10, txt=f"Precio Lista: USD {row['Precio lista (USD)']}", ln=True)
            pdf.cell(200, 10, txt=f"Rango Mínimo: USD {row['Rango Mínimo (USD)']}", ln=True)
            pdf.cell(200, 10, txt=f"Rango Máximo: USD {row['Rango Máximo (USD)']}", ln=True)
            pdf.ln(5)

        # Guardar el archivo PDF
        pdf_output_path = "Cotizacion.pdf"
        pdf.output(pdf_output_path)
        st.success(f"Cotización guardada como {pdf_output_path}.")
        with open(pdf_output_path, "rb") as pdf_file:
            st.download_button(
                label="Descargar PDF",
                data=pdf_file,
                file_name="Cotizacion.pdf",
                mime="application/pdf"
            )

# Crear columnas para alinear los botones a la derecha
col1, col2, col3 = st.columns([1, 1, 1])  # Ajusta las proporciones según sea necesario

with col3:  # Los botones estarán en la tercera columna (alineados a la derecha)
    # Botón para finalizar
    if st.button("Finalizar"):
        st.success("¡Cotización generada exitosamente!")

    # Botón "Volver Atrás"
    volver_atras = st.button("Nueva Cotización")
    if volver_atras:
        st.session_state.current_step = 1
        st.rerun()  # Esto recarga la app desde el paso anterior