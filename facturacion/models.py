from django.db import models

from django.db import models

class MesAno(models.Model):
    MESES = [
        ('01', 'Enero'), ('02', 'Febrero'), ('03', 'Marzo'), ('04', 'Abril'),
        ('05', 'Mayo'), ('06', 'Junio'), ('07', 'Julio'), ('08', 'Agosto'),
        ('09', 'Septiembre'), ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre'),
    ]

    año = models.IntegerField()
    mes = models.CharField(max_length=2, choices=MESES)

    class Meta:
        unique_together = ('año', 'mes')  # No permite duplicados de año y mes
        ordering = ['año', 'mes']  # Ordenar por año y mes

    def __str__(self):
        return f"{self.get_mes_display()} {self.año}"


class Presupuesto(models.Model):
    numero = models.AutoField(primary_key=True)  # Número único de presupuesto
    cliente = models.CharField(max_length=255)  # Nombre del cliente
    documento = models.CharField(max_length=20)  # Documento del cliente
    fecha = models.DateField(auto_now_add=True)  # Fecha de creación del presupuesto

    def __str__(self):
        return f"Presupuesto #{self.numero} - {self.cliente}"


class Prestacion(models.Model):
    codigo = models.CharField(max_length=50)  # Código de la prestación
    descripcion = models.TextField(max_length=150)  # Descripción de la prestación
    honorarios = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Honorarios
    ayudante = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Ayudante
    gastos = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Gastos
    anestesia = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Anestesia
    total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Total
    servicio = models.CharField(max_length=50) #Servicio
    practica = models.CharField(max_length=150) #Practica
    
    def __str__(self):
        return f"{self.descripcion} (Código: {self.codigo})"
    
class Item(models.Model):
    presupuesto = models.ForeignKey(Presupuesto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=0)  # Nueva cantidad

    def __str__(self):
        return f"Presupuesto {self.presupuesto.numero} - Cantidad {self.cantidad}"
    
class DetallePrestacion(models.Model):
    presupuesto = models.ForeignKey(Presupuesto, on_delete=models.CASCADE, related_name='prestaciones')
    prestacion = models.ForeignKey(Prestacion, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    
    def calcular_total(self):
        if self.item and self.prestacion:
            return self.item.cantidad * self.prestacion.total
        return 0
    
    def __str__(self):
        return f"Presupuesto {self.presupuesto.numero} - Prestacion {self.prestacion.codigo}"