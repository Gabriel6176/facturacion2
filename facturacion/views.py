import os
import pandas as pd
import datetime
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from .forms import UploadFileForm1, UploadFileForm2, UploadFileForm3
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

@login_required
def file_upload_view(request):
    form_classes = {
        'form1': UploadFileForm1,
        'form2': UploadFileForm2,
        'form3': UploadFileForm3,
    }

    # Obtener el parámetro `form` de la URL
    selected_form_key = request.GET.get('form', 'form1')  # Por defecto, 'form1'
    selected_form_class = form_classes.get(selected_form_key)  # Obtener la clase del formulario

    if not selected_form_class:
        # Si el parámetro `form` no es válido, muestra un error o redirige a una página válida
        return HttpResponse("Formulario no válido", status=400)

    # Instanciar el formulario seleccionado
    selected_form = selected_form_class()

    if request.method == 'POST':
        # Procesar el formulario enviado
        form = selected_form_class(request.POST, request.FILES)
        if form.is_valid():
            # Manejo del archivo subido
            uploaded_file = request.FILES['file']
            uploaded_file_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.name)
            with open(uploaded_file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # Procesar el archivo base con el subido
            base_file_path = os.path.join(settings.MEDIA_ROOT, 'base.xlsx')
            output_file_path = process_files(base_file_path, uploaded_file_path)

            # Retornar la vista de éxito
            output_filename = os.path.basename(output_file_path)
            return render(request, 'facturacion/success.html', {'output_file': output_filename})

    # Renderizar solo el formulario seleccionado
    return render(request, 'facturacion/upload.html', {
        'form': selected_form,
        'form_type': selected_form_key,  # Agregamos el tipo de formulario al contexto si es necesario
    })

def file_download_view(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, filename)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            response = HttpResponse(file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename={filename}'
            return response
    return HttpResponse("Archivo no encontrado", status=404)

def process_files(base_file_path, uploaded_file_path):


    # Cargar `df1` desde el archivo subido por el usuario, usando la hoja `TX`
    df1 = pd.read_excel(uploaded_file_path, sheet_name='TX', usecols="A:B", header=None)

    # Cargar `df2` y `df4` desde el archivo base `base.xlsx`
    df2 = pd.read_excel(base_file_path, sheet_name='raw_data', usecols="A:Q", header=None)
    df4 = pd.read_excel(base_file_path, sheet_name='Precios', usecols="A:C", header=None)

    # Crear DataFrames vacíos para "Facturación" y "No Encontrados"
    df_facturacion = pd.DataFrame(columns=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
    df_no_encontrados = pd.DataFrame(columns=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])

    # Procesar registros de `df1`
    for index, (value, value2) in df1.iloc[1:, [0, 1]].iterrows():
        matches = df2[df2.iloc[:, 5] == value]
        if matches.empty:
            # Si no se encuentra en `df2`, agregar al DataFrame "No Encontrados"
            row_to_add = pd.DataFrame({
                1: ["NO ENCONTRADO"], 2: [None], 3: [None], 4: [None], 5: [None],
                6: [None], 7: [None], 8: [None], 9: [None], 10: [value], 11: [value2]
            })
            df_no_encontrados = pd.concat([df_no_encontrados, row_to_add], ignore_index=True)
        else:
            # Si se encuentra, procesar normalmente y agregar al DataFrame "Facturación"
            for _, row in matches.iterrows():
                modified_value = str(row[2])[3:-2] if isinstance(row[2], str) else row[2]
                
                # Quitar espacios en ambos valores, convertir a string y hacer una sola comparación
                df4_filtered = df4[df4.iloc[:, 0].astype(str).str.replace(" ", "", regex=False) == str(row[7]).replace(" ", "")]
            
                if not df4_filtered.empty:
                    precio = df4_filtered.iloc[0, 2]  # Precio tomado de df4
                else:
                    precio = "NO ENCONTRADO"

                row_to_add = pd.DataFrame({
                    1: [row[0]], 
                    2: [modified_value], 
                    3: [row[2]], 
                    4: [row[6]], 
                    5: [row[9]], 
                    6: [row[7]], 
                    7: [row[8]], 
                    8: [precio], 
                    9: [float(precio) * float(row[9]) if isinstance(precio, (int, float)) and pd.notna(row[9]) else None],
                    10: [value], 
                    11: [value2]
                })
                df_facturacion = pd.concat([df_facturacion, row_to_add], ignore_index=True)
    
    # Asignar nombres de columnas
    column_names = [
        df2.iloc[0, 0], "DNI", df2.iloc[0, 2], df2.iloc[0, 6], df2.iloc[0, 9], 
        df2.iloc[0, 7], df2.iloc[0, 8], "Precio", "Total", "TX", "LOTE"
    ]
    df_facturacion.columns = column_names
    df_no_encontrados.columns = column_names

    # Generar nombre de archivo de salida
    output_filename = f"facturacion_{datetime.datetime.now().strftime('%d%b%y')}.xlsx"
    output_file_path = os.path.join(settings.MEDIA_ROOT, output_filename)

    # Guardar ambos DataFrames en diferentes hojas del archivo Excel
    with pd.ExcelWriter(output_file_path, engine='openpyxl') as writer:
        df_facturacion.to_excel(writer, sheet_name='Facturación', index=False)
        df_no_encontrados.to_excel(writer, sheet_name='No Encontrados', index=False)

    return output_file_path

@login_required
def dashboard_view(request):
    return render(request, 'facturacion/dashboard.html')  # Renderiza la plantilla del dashboard


def dashboard_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')  # Redirige al dashboard
    return redirect('login')  # Redirige al login

