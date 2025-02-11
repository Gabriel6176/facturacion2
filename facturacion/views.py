import os
import pandas as pd
import datetime
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .forms import UploadFileForm1, UploadFileForm3
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .models import MesAno
from .models import Item, Presupuesto, Prestacion, DetallePrestacion
from django.http import JsonResponse
from datetime import date
from django.db.models import F, Sum
from django.contrib import messages
from .forms import PresupuestoForm
from decimal import Decimal, InvalidOperation
import numpy as np  # Importa numpy para manejar NaN
from openpyxl.styles import NamedStyle
import openpyxl
from openpyxl.styles import Font

@login_required
def file_upload_view(request):
    form_classes = {
        'form1': UploadFileForm1,
        'form3': UploadFileForm3,
    }

    # Obtener el formulario seleccionado desde la URL
    selected_form_key = request.GET.get('form', 'form1')
    selected_form_class = form_classes.get(selected_form_key)

    if not selected_form_class:
        return HttpResponse("Formulario no válido", status=400)  # Manejar formulario inválido

    # Obtener opciones de Mes y Año desde la base de datos
    opciones_mes_ano = MesAno.objects.all()
    opciones_mes = []
    seen_mes = set()
    for opcion in opciones_mes_ano:
        if opcion.mes not in seen_mes:
            opciones_mes.append(opcion)
            seen_mes.add(opcion.mes)
    opciones_anos = sorted(set(opcion.año for opcion in opciones_mes_ano))

    # Si es una solicitud POST (cuando se envía el formulario)
    if request.method == 'POST':
        #print("Procesando solicitud POST...")  # Depuración
        form = selected_form_class(request.POST, request.FILES)
        if form.is_valid():
            mes = form.cleaned_data['mes']
            año = form.cleaned_data['año']
            tipo_proceso = form.cleaned_data['tipo_proceso']
            #print(f"Tipo de proceso seleccionado: {tipo_proceso}")  # Depuración
            uploaded_file = request.FILES['file']

            # Guardar el archivo subido
            uploaded_file_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.name)
            with open(uploaded_file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # Procesar los archivos
            base_file_path = os.path.join(settings.MEDIA_ROOT, 'base.xlsx')
            output_file_path = process_files(base_file_path, uploaded_file_path, mes, año, tipo_proceso)

            # Redirigir a la página de éxito
            return render(request, 'facturacion/success.html', {'output_file': os.path.basename(output_file_path)})

        else:
            print("Errores en el formulario:", form.errors)  # Depuración de errores
            return HttpResponse("Formulario inválido. Por favor revisa los datos enviados.", status=400)

    # Si es una solicitud GET (cuando se muestra el formulario)
    return render(request, 'facturacion/upload.html', {
        'form': selected_form_class(),
        'form_type': selected_form_key,
        'opciones_mes': opciones_mes,
        'opciones_anos': opciones_anos,
        'mostrar_volver': True,
    })



@login_required
def file_download_view(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, filename)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            response = HttpResponse(file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename={filename}'
            return response
    return HttpResponse("Archivo no encontrado", status=404)

def process_files(base_file_path, uploaded_file_path, mes, año, tipo_proceso):
    #print("Inicio de process_files")

    # Definir columnas de salida
    columnas_output = [
        'Nombre y apellido Afiliado', 'DNI', 'Nro Afiliado', 'Fecha', 
        'Cantidad', 'Codigo', 'Descripcion', 'Precio', 'Total', 'TX', 'Lote', 'Numerador'
    ]
    
    # 1. Cargar archivos
    #print("Cargando archivos...")
    df1 = pd.read_excel(uploaded_file_path, sheet_name='TX', usecols="A:B", header=None, skiprows=1, names=['TX', 'Lote'])
    df4 = pd.read_excel(base_file_path, sheet_name='Precios', usecols="A:C", header=None, names=['Codigo', 'Desc', 'Precio'])

    sheet_name = 'raw_data_internacion' if tipo_proceso == 'raw_data_internacion' else 'raw_data'
    df2 = pd.read_excel(base_file_path, sheet_name=sheet_name, usecols="A:Q", header=None)
    
    
    # Asignar nombres de columnas a df2
    df2.columns = ['Nombre y apellido Afiliado', 'Numerador', 'Nro Afiliado', 'DNI', 'Col5', 'TX', 'Fecha', 'Codigo', 'Descripcion',
                   'Cantidad', 'Col10', 'Col11', 'Col12', 'Col13', 'Col14', 'Col15', 'Col16']
    
    # Convertir TX a string y eliminar espacios en blanco
    df2['TX'] = df2['TX'].astype(str).str.strip()
    df1['TX'] = df1['TX'].astype(str).str.strip()

    # Crear columna 'DNI' extrayendo caracteres de 'Nro Afiliado'
    df2['DNI'] = df2['Nro Afiliado'].astype(str).str[3:11]

    # 2. Convertir fecha y filtrar por mes y año
    df2['Fecha'] = pd.to_datetime(df2['Fecha'], format='%d/%m/%Y', errors='coerce')
    df2_filtrado = df2.dropna(subset=['Fecha'])
    df2_filtrado = df2_filtrado[(df2_filtrado['Fecha'].dt.month == int(mes)) &
                                (df2_filtrado['Fecha'].dt.year == int(año))]

    # Limpieza de espacios en los códigos
    df4['Codigo'] = df4['Codigo'].astype(str).str.strip()
    df2['Codigo'] = df2['Codigo'].astype(str).str.strip()

    # 3. Convertir df4 en diccionario para búsqueda rápida
    precio_dict = df4.set_index('Codigo')['Precio'].to_dict()

    # 4. Inicializar listas para clasificar filas
    facturacion_ctx_rows = []
    facturacion_stx_rows = []
    tx_viejos_rows = []
    tx_noencontrados_rows = []

    df1['procesado'] = False

    # 5. Procesar df2 filtrado
    for _, row in df2_filtrado.iterrows():
        tx_value = row['TX']
        codigo = row['Codigo']
        cantidad = row['Cantidad']
        precio = precio_dict.get(codigo, np.nan)
        numerador=row['Numerador']

        # Calcular el total solo si el precio es numérico
        total = precio * cantidad if isinstance(precio, (int, float)) and pd.notna(precio) and pd.notna(cantidad) else np.nan

        lote = df1.loc[df1['TX'] == tx_value, 'Lote'].values[0] if tx_value in df1['TX'].values else None

        row_data = [
            row['Nombre y apellido Afiliado'], row['DNI'], row['Nro Afiliado'],
            row['Fecha'], cantidad, codigo, row['Descripcion'], precio, total, tx_value, lote,numerador,
        ]

        if tx_value in df1['TX'].values:
            facturacion_ctx_rows.append(row_data)
            df1.loc[df1['TX'] == tx_value, 'procesado'] = True
        else:
            facturacion_stx_rows.append(row_data)

    # 6. Procesar TXs no encontradas
    df1_no_procesados = df1[df1['procesado'] == False]

    for _, row_df1 in df1_no_procesados.iterrows():
        tx_value = row_df1['TX']
        lote = row_df1['Lote']
        matches = df2[df2['TX'] == tx_value]
        

        if not matches.empty:
            for _, match_row in matches.iterrows():
                codigo = match_row['Codigo']
                cantidad = match_row['Cantidad']
                precio = precio_dict.get(codigo, np.nan)
                numerador=row['Numerador']

                total = precio * cantidad if isinstance(precio, (int, float)) and pd.notna(precio) and pd.notna(cantidad) else np.nan

                tx_viejos_rows.append([
                    match_row['Nombre y apellido Afiliado'], match_row['DNI'], match_row['Nro Afiliado'],
                    match_row['Fecha'], cantidad, codigo, match_row['Descripcion'], precio, total, tx_value, lote,numerador,
                ])
                df1.loc[df1['TX'] == tx_value, 'procesado'] = True
        else:
            tx_noencontrados_rows.append(["NO ENCONTRADO", None, None, None, None, None, None, None, None, tx_value, lote,None])

    # 7. Convertir listas a DataFrames
    df_facturacion_ctx = pd.DataFrame(facturacion_ctx_rows, columns=columnas_output)
    df_facturacion_stx = pd.DataFrame(facturacion_stx_rows, columns=columnas_output)
    df_tx_viejos = pd.DataFrame(tx_viejos_rows, columns=columnas_output)
    df_tx_noencontrados = pd.DataFrame(tx_noencontrados_rows, columns=columnas_output)

    # 8. Guardar los DataFrames en Excel
    output_filename = f"facturacion_{datetime.datetime.now().strftime('%d%b%y')}.xlsx"
    output_file_path = os.path.join(settings.MEDIA_ROOT, output_filename)

    date_style = NamedStyle(name="date_style", number_format="DD/MM/YYYY")

    with pd.ExcelWriter(output_file_path, engine='openpyxl') as writer:
        df_facturacion_ctx.to_excel(writer, sheet_name='Facturación Con TX', index=False)
        df_facturacion_stx.to_excel(writer, sheet_name='Facturación Sin TX', index=False)
        df_tx_viejos.to_excel(writer, sheet_name='TX Viejos', index=False)
        df_tx_noencontrados.to_excel(writer, sheet_name='TX No Encontrados', index=False)

        # Aplicar estilos al archivo Excel
        workbook = writer.book
        for sheet_name in writer.sheets:
            worksheet = workbook[sheet_name]
            for col in worksheet.iter_cols(min_col=4, max_col=4):  # Formatear la columna Fecha
                for cell in col:
                    cell.style = date_style
            for cell in worksheet[1]:  # Negrita en títulos
                cell.font = Font(bold=True)

    return output_file_path



@login_required
def dashboard_view(request):
    return render(request, 'facturacion/dashboard.html')  # Renderiza la plantilla del dashboard


def dashboard_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')  # Redirige al dashboard
    return redirect('login')  # Redirige al login



@login_required
def presupuesto_nuevo(request):
    if request.method == 'POST':
        # Obtiene los datos del formulario
        cliente = request.POST.get('cliente')
        documento = request.POST.get('documento')

        if cliente and documento:
            # Crea un nuevo presupuesto
            presupuesto = Presupuesto(
                cliente=cliente,
                documento=documento,
                fecha=date.today()  # Fecha actual como predeterminada
            )
            presupuesto.save()
            # Redirige a la vista de lista de presupuestos
            return redirect('detalle_presupuestador')

    # Renderiza la plantilla con datos adicionales (si es necesario)
    return render(request, 'facturacion/presupuesto_nuevo.html', {
        'fecha_hoy': date.today().strftime('%Y-%m-%d')  # Enviar fecha actual como string
    })

@login_required
def detalle_presupuestador(request):
    presupuestos = Presupuesto.objects.all()  # Obtén todos los presupuestos
    return render(request, 'facturacion/detalle_presupuestador.html', {
        'presupuestos': presupuestos,
        'mostrar_volver': True  # Agrega una bandera para mostrar el botón
    })


@login_required
def agregar_item(request, presupuesto_id):
    presupuesto = get_object_or_404(Presupuesto, pk=presupuesto_id)

    if request.method == 'POST':
        cantidad = request.POST.get('cantidad')
        prestacion_id = request.POST.get('prestacion')

        if cantidad and prestacion_id:
            prestacion = get_object_or_404(Prestacion, pk=prestacion_id)

            # Crear un nuevo Item
            item = Item.objects.create(
                presupuesto=presupuesto,
                cantidad=cantidad
            )

            # Asociar el item con DetallePrestacion
            DetallePrestacion.objects.create(
                presupuesto=presupuesto,
                prestacion=prestacion,
                item=item
            )

        # Aquí usamos presupuesto.numero en lugar de presupuesto.id
        return redirect('detalle_presupuesto', presupuesto_id=presupuesto.numero)

    servicios = Prestacion.objects.values('servicio').distinct()

    return render(request, 'facturacion/agregar_item.html', {
        'presupuesto': presupuesto,
        'servicios': servicios,
    })

@login_required
def eliminar_item(request, presupuesto_id):
    if request.method == "POST":
        item_id = request.POST.get("item_id")  # Obtén el ID del ítem desde el formulario
        detalle = get_object_or_404(DetallePrestacion, pk=item_id, presupuesto_id=presupuesto_id)

        # Elimina el ítem
        detalle.delete()

        # Muestra un mensaje de éxito
        messages.success(request, "El ítem se eliminó correctamente.")

    # Redirige al detalle del presupuesto
    return redirect("detalle_presupuesto", presupuesto_id=presupuesto_id)

@login_required
def detalle_presupuesto(request, presupuesto_id):
    # Obtiene el presupuesto o lanza un error 404 si no existe
    presupuesto = get_object_or_404(Presupuesto, pk=presupuesto_id)
    
    # Obtiene los detalles del presupuesto, optimizando con select_related
    detalles = DetallePrestacion.objects.filter(presupuesto=presupuesto).select_related('prestacion', 'item')

    # Añadir el total de cada línea al queryset
    for detalle in detalles:
        detalle.total_linea = detalle.item.cantidad * detalle.prestacion.total
        
    # Calcula el total general usando anotaciones
    total_general = detalles.aggregate(
        total=Sum(F('item__cantidad') * F('prestacion__total'))
    )['total'] or 0

    # Bandera para saber si estamos en modo edición (se puede activar desde la URL)
    modo_edicion = request.GET.get('modo_edicion') == 'true'

    # Renderiza la plantilla con los datos necesarios
    return render(request, 'facturacion/detalle_presupuesto.html', {
        'presupuesto': presupuesto,
        'detalles': detalles,
        'total_general': total_general,
        'modo_edicion': modo_edicion  # Determina si se muestran acciones de edición
    })

@login_required
def obtener_prestaciones(request):
    servicio = request.GET.get('servicio')
    #print(f"Servicio solicitado: {servicio}")  # Log temporal
    if servicio:
        prestaciones = Prestacion.objects.filter(servicio=servicio).values('id', 'codigo', 'descripcion')
        return JsonResponse(list(prestaciones), safe=False)
    return JsonResponse([], safe=False)

@login_required
def buscar_descripcion(request):
    query = request.GET.get('q', '')
    resultados = Prestacion.objects.filter(descripcion__icontains=query).values('id', 'descripcion')[:10]
    return JsonResponse(list(resultados), safe=False)

@login_required
def nueva_prestacion(request, presupuesto_id):
    presupuesto = get_object_or_404(Presupuesto, id=presupuesto_id)

    # Obtener todas las prestaciones disponibles
    prestaciones = Prestacion.objects.all()

    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad'))
        prestacion_id = request.POST.get('prestacion')  # ID de la prestación seleccionada
        prestacion = get_object_or_404(Prestacion, id=prestacion_id)

        # Crear un nuevo detalle de prestación
        nuevo_detalle = DetallePrestacion(
            cantidad=cantidad,
            presupuesto=presupuesto,
            prestacion=prestacion
        )
        nuevo_detalle.save()
        return redirect('detalle_presupuestador')

    return render(request, 'facturacion/nueva_prestacion.html', {
        'presupuesto': presupuesto,
        'prestaciones': prestaciones  # Pasar todas las prestaciones a la plantilla
    })



@login_required
def editar_presupuesto(request, numero):
    # Obtiene el presupuesto o lanza un error 404 si no existe
    presupuesto = get_object_or_404(Presupuesto, numero=numero)

    if request.method == 'POST':
        # Procesa el formulario enviado
        form = PresupuestoForm(request.POST, instance=presupuesto)
        if form.is_valid():
            form.save()  # Guarda los cambios realizados en cliente y documento
            return redirect('detalle_presupuesto', presupuesto_id=presupuesto.numero)  # Redirige a los detalles
    else:
        # Muestra el formulario con los datos actuales
        form = PresupuestoForm(instance=presupuesto)

    return render(request, 'facturacion/editar_presupuesto.html', {
        'presupuesto': presupuesto,
        'form': form  # Formulario para editar el presupuesto
    })