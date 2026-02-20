"""
Componente de tarjeta de habitación para el dashboard
"""
import flet as ft
from models.habitacion import Habitacion, EstadoHabitacion
from models.registro import Registro
from utils.helpers import format_money

class RoomCard(ft.Card):
    """Tarjeta visual de una habitación para el grid principal"""
    
    def __init__(self, habitacion: Habitacion, on_click=None):
        super().__init__()
        self.habitacion = habitacion
        self.on_card_click = on_click
        self._build()
    
    def _build(self):
        # Determinar información a mostrar según estado
        estado_texto = self.habitacion.estado.value
        info_adicional = ""
        
        if self.habitacion.estado == EstadoHabitacion.OCUPADA:
            # Buscar información del huésped
            registro = Registro.buscar_activo_por_habitacion(self.habitacion.numero)
            if registro:
                info_adicional = registro.huesped_nombre
                if registro.saldo_actual_usd > 0:
                    info_adicional += f"\n⚠️ Debe: ${registro.saldo_actual_usd:.2f}"
        
        # Color de fondo según estado
        bg_color = self.habitacion.color_estado
        
        # Contenido de la tarjeta
        self.content = ft.Container(
            content=ft.Column(
                [
                    # Número de habitación
                    ft.Text(
                        f"{self.habitacion.numero:03d}",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                        text_align=ft.TextAlign.CENTER
                    ),
                    # Tipo de habitación
                    ft.Text(
                        self.habitacion.tipo,
                        size=12,
                        color=ft.Colors.WHITE70,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Divider(height=1, color=ft.Colors.WHITE24),
                    # Estado
                    ft.Text(
                        estado_texto,
                        size=11,
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.W_500,
                        text_align=ft.TextAlign.CENTER
                    ),
                    # Info adicional (huésped o precio)
                    ft.Text(
                        info_adicional if info_adicional else f"${self.habitacion.precio_usd:.0f}",
                        size=10,
                        color=ft.Colors.WHITE70,
                        text_align=ft.TextAlign.CENTER,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2
            ),
            width=100,
            height=120,
            padding=5,
            bgcolor=bg_color,
            border_radius=8,
            on_click=self._on_click,
            animate=ft.animation.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
        )
    
    def _on_click(self, e):
        if self.on_card_click:
            self.on_card_click(self.habitacion)
    
    def update_habitacion(self, habitacion: Habitacion):
        """Actualiza la información de la habitación"""
        self.habitacion = habitacion
        self._build()
        self.update()
