"""
Utilidades para exportar reportes a archivos
"""
import csv
import io
from datetime import datetime
from django.http import HttpResponse


def exportar_reporte_csv(filename, headers, datos):
    """
    Genera un archivo CSV con los datos del reporte
    
    Args:
        filename: Nombre del archivo (sin extensión)
        headers: Lista de nombres de columnas
        datos: Lista de diccionarios con los datos
    
    Returns:
        HttpResponse con el archivo CSV
    """
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    
    # Agregar BOM para UTF-8 (para compatibilidad con Excel)
    response.write('\ufeff')
    
    writer = csv.DictWriter(response, fieldnames=headers, encoding='utf-8')
    writer.writeheader()
    
    for row in datos:
        writer.writerow({k: row.get(k, '') for k in headers})
    
    return response


def exportar_reporte_txt(filename, headers, datos, titulo=''):
    """
    Genera un archivo de texto formateado con los datos
    
    Args:
        filename: Nombre del archivo (sin extensión)
        headers: Lista de nombres de columnas
        datos: Lista de diccionarios con los datos
        titulo: Título del reporte
    
    Returns:
        HttpResponse con el archivo TXT
    """
    response = HttpResponse(content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}.txt"'
    
    lineas = []
    
    # Agregar título
    if titulo:
        lineas.append(f"\n{'=' * 80}")
        lineas.append(f"  {titulo}")
        lineas.append(f"{'=' * 80}\n")
    
    # Agregar fecha de exportación
    lineas.append(f"Fecha de Exportación: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    lineas.append(f"{'=' * 80}\n\n")
    
    # Calcular anchos de columna
    anchos = {h: len(str(h)) for h in headers}
    for row in datos:
        for h in headers:
            anchos[h] = max(anchos[h], len(str(row.get(h, ''))))
    
    # Agregar encabezados
    encabezado = " | ".join(str(h).ljust(anchos[h]) for h in headers)
    lineas.append(encabezado)
    lineas.append("-" * len(encabezado))
    
    # Agregar datos
    for row in datos:
        fila = " | ".join(str(row.get(h, '')).ljust(anchos[h]) for h in headers)
        lineas.append(fila)
    
    response.write('\n'.join(lineas))
    return response
