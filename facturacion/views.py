import os
import pandas as pd
import datetime
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .forms import UploadFileForm1, UploadFileForm2, UploadFileForm3
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .models import MesAno
from .models import Item, Presupuesto, Prestacion, DetallePrestacion
from django.http import JsonResponse
from datetime import date
from django.db.models import F, Sum
from django.contrib import messages
from .forms import PresupuestoForm

@login_required
def file_upload_view(request):
    form_classes = {
        'form1': UploadFileForm1,
        'form2': UploadFileForm2,
        'form3': UploadFileForm3,
    }

    # Obtener el formulario seleccionado desde la URL
    selected_form_key = request.GET.get('form', 'form1')
    selected_form_class = form_classes.get(selected_form_key)

    if not selected_form_class:
        return HttpResponse("Formulario no válido", status=400)

    # Obtener todas las opciones de Mes y Año desde la base de datos
    opciones_mes_ano = MesAno.objects.all()

    # Extraer meses únicos
    opciones_mes = []
    seen_mes = set()
    for opcion in opciones_mes_ano:
        if opcion.mes not in seen_mes:
            opciones_mes.append(opcion)
            seen_mes.add(opcion.mes)

    # Extraer años únicos
    opciones_anos = sorted(set(opcion.año for opcion in opciones_mes_ano))

    if request.method == 'POST':
        # Procesar datos enviados
        form = selected_form_class(request.POST, request.FILES)
        if form.is_valid():
            mes = request.POST.get('mes')
            año = request.POST.get('año')
            tipo_proceso = request.POST.get('tipo_proceso')

            # Procesar archivo subido
            uploaded_file = request.FILES['file']
            uploaded_file_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.name)
            with open(uploaded_file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # Realizar el procesamiento
            base_file_path = os.path.join(settings.MEDIA_ROOT, 'base.xlsx')
            output_file_path = process_files(base_file_path, uploaded_file_path, mes, año, tipo_proceso)

            # Retornar vista de éxito
            output_filename = os.path.basename(output_file_path)
            return render(request, 'facturacion/success.html', {'output_file': output_filename})

    # Renderizar formulario
    return render(request, 'facturacion/upload.html', {
        'form': selected_form_class(),
        'form_type': selected_form_key,
        'opciones_mes': opciones_mes,
        'opciones_anos': opciones_anos,
    })

def file_download_view(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, filename)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            response = HttpResponse(file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename={filename}'
            return response
    return HttpResponse("Archivo no encontrado", status=404)

def process_files(base_file_path, uploaded_file_path, mes, año, tipo_proceso):
    # Cargar `df1` desde el archivo subido por el usuario, usando la hoja `TX`
    df1 = pd.read_excel(uploaded_file_path, sheet_name='TX', usecols="A:B", header=None)

    # Selección condicional del DataFrame `df2`
    if tipo_proceso == 'internacion':
        df2 = pd.read_excel(base_file_path, sheet_name='raw_data_internacion', usecols="A:Q", header=None)
    else:
        df2 = pd.read_excel(base_file_path, sheet_name='raw_data', usecols="A:Q", header=None)

    # Cargar `df4` desde el archivo base
    df4 = pd.read_excel(base_file_path, sheet_name='Precios', usecols="A:C", header=None)

    # Crear DataFrames vacíos para clasificar los registros
    df_facturacion_ctx = pd.DataFrame(columns=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
    df_facturacion_stx = pd.DataFrame(columns=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
    df_tx_viejos = pd.DataFrame(columns=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
    df_tx_noencontrados = pd.DataFrame(columns=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])

    # Agregar una columna "procesado" a df1 con valores iniciales en False
    df1['procesado'] = False

    # Filtrar `df2` por mes y año (columna 6 -> Fecha en formato DD/MM/YYYY)
    df2['Fecha'] = pd.to_datetime(df2.iloc[:, 6], format='%d/%m/%Y', errors='coerce')
    df2_filtrado = df2[(df2['Fecha'].dt.month == int(mes)) & (df2['Fecha'].dt.year == int(año))]

    # Iterar sobre el DataFrame filtrado `df2_filtrado`
    for _, row in df2_filtrado.iterrows():
        valor_buscar = row[5]  # Valor en la columna 5
        modified_value = str(row[2])[3:-2] if isinstance(row[2], str) else row[2]  # Modificar columna 2

        # Nueva lógica para buscar el precio en `df4` usando la columna 7 del registro actual
        df4_filtered = df4[df4.iloc[:, 0].astype(str).str.replace(" ", "", regex=False) == str(row[7]).replace(" ", "")]
        if not df4_filtered.empty:
            precio = df4_filtered.iloc[0, 2]  # Extraer el precio
        else:
            precio = "NO ENCONTRADO"

        # Cálculo del total (cantidad * precio)
        cantidad = row[9]
        total = float(precio) * float(cantidad) if isinstance(precio, (int, float)) and pd.notna(cantidad) else None

        # Obtener el valor del lote desde la columna B de df1 basado en la coincidencia
        valor_lote = df1.loc[df1.iloc[:, 0] == valor_buscar, 1].values[0] if valor_buscar in df1.iloc[:, 0].values else None

        # Crear el registro procesado como DataFrame
        row_to_add = pd.DataFrame({
            1: [row[0]], 
            2: [modified_value], 
            3: [row[2]], 
            4: [row[6]],  # Fecha
            5: [cantidad], 
            6: [row[7]], 
            7: [row[8]], 
            8: [precio],  # Precio obtenido de df4
            9: [total],   # Total calculado
            10: [valor_buscar],
            11: [valor_lote]  # Valor del lote obtenido de la columna B de df1
        })

        # Verificar si el valor está en df1
        if valor_buscar in df1.iloc[:, 0].values:
            # Si está en df1, guardar en df_facturacion_ctx y marcar como procesado
            df_facturacion_ctx = pd.concat([df_facturacion_ctx, row_to_add], ignore_index=True)
            df1.loc[df1.iloc[:, 0] == valor_buscar, 'procesado'] = True
        else:
            # Si no está en df1, guardar en df_facturacion_stx
            df_facturacion_stx = pd.concat([df_facturacion_stx, row_to_add], ignore_index=True)

    # Iterar sobre los registros de df1 donde 'procesado' es False, empezando desde la segunda fila
    for _, row_df1 in df1.iloc[1:][df1['procesado'] == False].iterrows():
        valor_buscar = row_df1[0]  # Valor en la columna 0 de `df1`
        valor_lote = row_df1[1]  # Valor del lote desde la columna 1 de `df1`

        # Buscar en df2 el valor en la columna 5
        matches = df2[df2.iloc[:, 5] == valor_buscar]

        if not matches.empty:
            # Si se encuentra en df2, iterar sobre las coincidencias
            for _, row in matches.iterrows():
                modified_value = str(row[2])[3:-2] if isinstance(row[2], str) else row[2]  # Modificar columna 2

                # Nueva lógica para buscar el precio en df4
                df4_filtered = df4[df4.iloc[:, 0].astype(str).str.replace(" ", "", regex=False) == str(row[7]).replace(" ", "")]
                if not df4_filtered.empty:
                    precio = df4_filtered.iloc[0, 2]  # Precio tomado de df4
                else:
                    precio = "NO ENCONTRADO"

                # Cálculo del total (cantidad * precio)
                cantidad = row[9]
                total = float(precio) * float(cantidad) if isinstance(precio, (int, float)) and pd.notna(cantidad) else None

                # Crear registro para TX encontrada
                row_to_add = pd.DataFrame({
                    1: [row[0]], 
                    2: [modified_value], 
                    3: [row[2]], 
                    4: [row[6]],  # Fecha
                    5: [cantidad], 
                    6: [row[7]], 
                    7: [row[8]], 
                    8: [precio],  # Precio obtenido de df4
                    9: [total],   # Total calculado
                    10: [valor_buscar],
                    11: [valor_lote]  # Valor del lote obtenido de la columna B de df1
                })

                # Agregar a df_tx_viejos
                df_tx_viejos = pd.concat([df_tx_viejos, row_to_add], ignore_index=True)

                # Marcar como procesado en df1
                df1.loc[df1.iloc[:, 0] == valor_buscar, 'procesado'] = True
        else:
            # Si no se encuentra en df2, agregar a df_tx_noencontrados
            row_to_add = pd.DataFrame({
                1: ["NO ENCONTRADO"], 
                2: [None], 
                3: [None], 
                4: [None], 
                5: [None], 
                6: [None], 
                7: [None], 
                8: [None], 
                9: [None], 
                10: [valor_buscar],
                11: [valor_lote]
            })
            df_tx_noencontrados = pd.concat([df_tx_noencontrados, row_to_add], ignore_index=True)
    

    # Asignar nombres de columnas
    column_names = [
        df2.iloc[0, 0], "DNI", df2.iloc[0, 2], df2.iloc[0, 6], df2.iloc[0, 9], 
        df2.iloc[0, 7], df2.iloc[0, 8], "Precio", "Total", "TX", "LOTE"
    ]

    df_facturacion_ctx.columns = column_names
    df_facturacion_stx.columns = column_names
    df_tx_viejos.columns = column_names
    df_tx_noencontrados.columns = column_names

    # Generar nombre de archivo de salida
    output_filename = f"facturacion_{datetime.datetime.now().strftime('%d%b%y')}.xlsx"
    output_file_path = os.path.join(settings.MEDIA_ROOT, output_filename)

    # Guardar ambos DataFrames en diferentes hojas del archivo Excel
    with pd.ExcelWriter(output_file_path, engine='openpyxl') as writer:
        df_facturacion_ctx.to_excel(writer, sheet_name='Facturación Con TX', index=False)
        df_facturacion_stx.to_excel(writer, sheet_name='Facturacion Sin TX', index=False)
        df_tx_viejos.to_excel(writer, sheet_name='TX_Viejos', index=False),
        df_tx_noencontrados.to_excel(writer, sheet_name='TX_NoEncontrados', index=False)


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
    return render(request, 'facturacion/detalle_presupuestador.html', {'presupuestos': presupuestos})


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


def detalle_presupuesto(request, presupuesto_id):
    presupuesto = get_object_or_404(Presupuesto, pk=presupuesto_id)
    detalles = DetallePrestacion.objects.filter(presupuesto=presupuesto).select_related('prestacion', 'item')

    # Calcular el total general
    total_general = detalles.aggregate(total=Sum(F('item__cantidad') * F('prestacion__total')))['total'] or 0

    return render(request, 'facturacion/detalle_presupuesto.html', {
        'presupuesto': presupuesto,
        'detalles': detalles,
        'total_general': total_general,
    })

def obtener_prestaciones(request):
    servicio = request.GET.get('servicio')
    print(f"Servicio solicitado: {servicio}")  # Log temporal
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


def editar_presupuesto(request, numero):
    # Obtiene el presupuesto o lanza un error 404 si no existe
    presupuesto = get_object_or_404(Presupuesto, numero=numero)

    if request.method == 'POST':
        # Procesa el formulario con los datos enviados
        form = PresupuestoForm(request.POST, instance=presupuesto)
        if form.is_valid():
            # Actualiza solo los campos especificados
            presupuesto.cliente = form.cleaned_data['cliente']
            presupuesto.documento = form.cleaned_data['documento']
            presupuesto.save()  # Guarda la instancia actualizada
            return redirect('detalle_presupuesto', presupuesto_id=presupuesto.numero)  # Redirige a la vista de detalle
    else:
        # Muestra el formulario con los datos actuales
        form = PresupuestoForm(instance=presupuesto)

    return render(request, 'facturacion/editar_presupuesto.html', {'form': form, 'presupuesto': presupuesto})