"""
Funciones auxiliares y utilidades
"""
from datetime import datetime, date
from typing import Optional
import re

def format_money(amount: float, currency: str = 'USD') -> str:
    """Formatea un monto como dinero"""
    if currency == 'USD':
        return f"${amount:,.2f}"
    else:
        return f"Bs {amount:,.2f}"

def format_date(fecha: Optional[datetime]) -> str:
    """Formatea una fecha para mostrar"""
    if not fecha:
        return "N/A"
    return fecha.strftime("%d/%m/%Y")

def format_datetime(fecha: Optional[datetime]) -> str:
    """Formatea una fecha y hora para mostrar"""
    if not fecha:
        return "N/A"
    return fecha.strftime("%d/%m/%Y %H:%M")

def format_time(fecha: Optional[datetime]) -> str:
    """Formatea solo la hora"""
    if not fecha:
        return "N/A"
    return fecha.strftime("%H:%M")

def parse_date(fecha_str: str) -> Optional[date]:
    """Parsea una fecha desde string"""
    if not fecha_str:
        return None
    try:
        return datetime.strptime(fecha_str, "%d/%m/%Y").date()
    except ValueError:
        try:
            return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            return None

def calcular_noches(fecha_entrada: datetime, fecha_salida: datetime) -> int:
    """Calcula el número de noches entre dos fechas"""
    delta = fecha_salida - fecha_entrada
    return max(1, delta.days)

def validar_cedula(documento: str) -> bool:
    """Valida formato básico de cédula/pasaporte venezolano"""
    if not documento:
        return False
    # Permitir V12345678, E12345678, P12345678 o solo números
    pattern = r'^[VEP]?-?\d{6,9}$'
    return bool(re.match(pattern, documento.upper()))

def validar_telefono(telefono: str) -> bool:
    """Valida formato básico de teléfono venezolano"""
    if not telefono:
        return True  # Teléfono es opcional
    # Permitir +58, 04XX, etc.
    pattern = r'^[\+\d\s\-\(\)]{10,20}$'
    return bool(re.match(pattern, telefono))

def validar_email(email: str) -> bool:
    """Valida formato de email"""
    if not email:
        return True  # Email es opcional
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def truncate_text(text: str, max_length: int = 50) -> str:
    """Trunca un texto a una longitud máxima"""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def get_initials(name: str) -> str:
    """Obtiene las iniciales de un nombre"""
    if not name:
        return "??"
    parts = name.strip().split()
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()

def generate_room_number(tipo: str, numero: int) -> str:
    """Genera un número de habitación formateado"""
    return f"{numero:03d}"

def estado_to_color(estado: str) -> str:
    """Convierte un estado a su color correspondiente"""
    colores = {
        'Libre': '#4CAF50',
        'Ocupada': '#F44336',
        'Reservada': '#FFC107',
        'Aseo': '#9E9E9E',
        'Mantenimiento': '#FF9800',
        'Activo': '#4CAF50',
        'Cerrado': '#9E9E9E',
        'Cancelado': '#F44336'
    }
    return colores.get(estado, '#9E9E9E')
