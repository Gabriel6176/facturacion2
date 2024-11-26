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

