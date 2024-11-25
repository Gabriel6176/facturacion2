from django import forms

class BaseUploadFileForm(forms.Form):
    file = forms.FileField()

class UploadFileForm1(BaseUploadFileForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].label = "Seleccione archivo Excel con Listado de TX de CSS"

class UploadFileForm2(BaseUploadFileForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].label = "Seleccione archivo Excel con Listado de Prestaciones OSDE"

class UploadFileForm3(BaseUploadFileForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].label = "Seleccione archivo Excel con Listado de prestaciones UP"
