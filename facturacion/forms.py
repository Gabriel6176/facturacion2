from django import forms
from .models import Presupuesto, MesAno

class BaseUploadFileForm(forms.Form):
    file = forms.FileField()
    mes = forms.ChoiceField(label='Mes', choices=MesAno.MESES)
    año = forms.IntegerField(label='Año')

class UploadFileForm1(BaseUploadFileForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].label = "Seleccione archivo Excel con Listado de TX de CSS"
        self.fields['tipo_proceso'] = forms.ChoiceField(
            label='Tipo de Proceso',
            choices=[
                ('raw_data', 'Ambulatorio'),  # Valores para 'raw_data'
                ('raw_data_internacion', 'Internación'),  # Valores para 'raw_data_internacion'
            ],
            required=True
        )

        if kwargs.get('initial'):
            initial = kwargs['initial']
            if 'mes' in initial:
                self.fields['mes'].initial = initial['mes']
            if 'año' in initial:
                self.fields['año'].initial = initial['año']

    def clean_año(self):
        año = self.cleaned_data['año']
        return año

    def clean_mes(self):
        mes = self.cleaned_data['mes']
        return mes


class UploadFileForm3(BaseUploadFileForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].label = "Seleccione archivo Excel con Listado de prestaciones UP"

class PresupuestoForm(forms.ModelForm):
    class Meta:
        model = Presupuesto
        fields = ['cliente', 'documento']
        widgets = {
            'cliente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del cliente'}),
            'documento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de documento'}),
        }