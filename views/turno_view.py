"""
Vista de Gestión de Turnos (Apertura/Cierre)
"""
import flet as ft
from datetime import datetime
from typing import Callable
from models.turno import Turno, EstadoTurno
from models.configuracion import get_config
from models.transaccion import Transaccion
from utils.session import session
from utils.helpers import format_datetime, format_money

class TurnoView(ft.View):
    """Vista para gestionar turnos (apertura y cierre de caja)"""
    
    def __init__(self, on_complete: Callable):
        super().__init__()
        self.route = "/turno"
        self.on_complete = on_complete
        self.turno_actual = None
        self._build()
    
    def _build(self):
        self.appbar = ft.AppBar(
            title=ft.Text("Gestión de Turno"),
            bgcolor=ft.Colors.BLUE,
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: self.on_complete())
        )
        
        # Verificar si hay turno abierto
        self.turno_actual = Turno.buscar_turno_abierto(session.usuario_id)
        
        if not self.turno_actual:
            # === APERTURA DE TURNO ===
            self._build_apertura()
        else:
            # === CIERRE DE TURNO ===
            self._build_cierre()
    
    def _build_apertura(self):
        """Construye la interfaz de apertura de turno"""
        config = get_config()
        
        self.txt_tasa = ft.TextField(
            label="Tasa de Cambio (Bs/USD)",
            value=str(config.tasa_dolar_bs),
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        self.txt_efectivo_usd = ft.TextField(
            label="Efectivo USD en Caja",
            value="0.00",
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        self.txt_efectivo_bs = ft.TextField(
            label="Efectivo BS en Caja",
            value="0.00",
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        btn_abrir = ft.ElevatedButton(
            "Abrir Turno",
            icon=ft.Icons.LOCK_OPEN,
            bgcolor=ft.Colors.GREEN,
            color=ft.Colors.WHITE,
            on_click=self._abrir_turno
        )
        
        self.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text("Apertura de Turno", weight=ft.FontWeight.BOLD, size=20),
                                ft.Text(f"Usuario: {session.usuario.nombre_completo}"),
                                ft.Text(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}"),
                                ft.Divider(),
                                self.txt_tasa,
                                ft.Text("Efectivo inicial en caja:", weight=ft.FontWeight.BOLD),
                                self.txt_efectivo_usd,
                                self.txt_efectivo_bs,
                                ft.Divider(),
                                btn_abrir
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=30
                        )
                    )
                ], alignment=ft.MainAxisAlignment.CENTER),
                padding=50,
                expand=True
            )
        ]
    
    def _build_cierre(self):
        """Construye la interfaz de cierre de turno"""
        # Calcular totales del turno
        self.turno_actual.calcular_totales()
        
        # Resumen del turno
        info_turno = ft.Column([
            ft.Text("Información del Turno", weight=ft.FontWeight.BOLD, size=16),
            ft.Text(f"Apertura: {format_datetime(self.turno_actual.fecha_apertura)}"),
            ft.Text(f"Tasa de apertura: ${self.turno_actual.tasa_apertura:.2f} Bs/USD"),
            ft.Text(f"Efectivo inicial USD: ${self.turno_actual.efectivo_usd_apertura:.2f}"),
            ft.Text(f"Efectivo inicial BS: Bs {self.turno_actual.efectivo_bs_apertura:.2f}"),
        ])
        
        # Movimientos del turno
        movimientos = ft.Column([
            ft.Text("Movimientos del Turno", weight=ft.FontWeight.BOLD, size=16),
            ft.Text(f"Total Ventas: ${self.turno_actual.total_ventas_usd:.2f}"),
            ft.Text(f"Total Pagos Recibidos: ${self.turno_actual.total_pagos_usd:.2f}"),
            ft.Divider(),
            ft.Text(f"Ventas BS: Bs {self.turno_actual.total_ventas_bs:.2f}"),
            ft.Text(f"Pagos BS: Bs {self.turno_actual.total_pagos_bs:.2f}"),
        ])
        
        # Campos de cierre
        config = get_config()
        self.txt_tasa_cierre = ft.TextField(
            label="Tasa de Cierre (Bs/USD)",
            value=str(config.tasa_dolar_bs),
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        self.txt_efectivo_usd_cierre = ft.TextField(
            label="Efectivo USD en Caja",
            value=str(self.turno_actual.efectivo_usd_apertura + self.turno_actual.total_pagos_usd),
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        self.txt_efectivo_bs_cierre = ft.TextField(
            label="Efectivo BS en Caja",
            value=str(self.turno_actual.efectivo_bs_apertura + self.turno_actual.total_pagos_bs),
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        self.txt_observaciones = ft.TextField(
            label="Observaciones",
            multiline=True,
            min_lines=2,
            max_lines=4,
            width=400
        )
        
        btn_cerrar = ft.ElevatedButton(
            "Cerrar Turno",
            icon=ft.Icons.LOCK,
            bgcolor=ft.Colors.RED,
            color=ft.Colors.WHITE,
            on_click=self._cerrar_turno
        )
        
        self.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Card(content=ft.Container(content=info_turno, padding=15)),
                    ft.Card(content=ft.Container(content=movimientos, padding=15)),
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text("Cierre de Caja", weight=ft.FontWeight.BOLD, size=16),
                                self.txt_tasa_cierre,
                                self.txt_efectivo_usd_cierre,
                                self.txt_efectivo_bs_cierre,
                                self.txt_observaciones,
                                btn_cerrar
                            ]),
                            padding=15
                        )
                    )
                ], scroll=ft.ScrollMode.AUTO),
                padding=20,
                expand=True
            )
        ]
    
    def _abrir_turno(self, e):
        """Abre un nuevo turno"""
        try:
            tasa = float(self.txt_tasa.value)
            efectivo_usd = float(self.txt_efectivo_usd.value or 0)
            efectivo_bs = float(self.txt_efectivo_bs.value or 0)
        except ValueError:
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Valores numéricos inválidos"), bgcolor=ft.Colors.RED)
            )
            return
        
        # Actualizar tasa en configuración
        config = get_config()
        config.actualizar_tasa(tasa)
        
        # Crear turno
        turno = Turno(
            usuario_id=session.usuario_id,
            tasa_apertura=tasa,
            efectivo_usd_apertura=efectivo_usd,
            efectivo_bs_apertura=efectivo_bs
        )
        turno_id = turno.guardar()
        
        # Guardar en sesión
        session.set_turno(turno_id)
        
        self.page.show_snack_bar(
            ft.SnackBar(content=ft.Text("Turno abierto correctamente"), bgcolor=ft.Colors.GREEN)
        )
        
        self.on_complete()
    
    def _cerrar_turno(self, e):
        """Cierra el turno actual"""
        try:
            tasa_cierre = float(self.txt_tasa_cierre.value)
            efectivo_usd = float(self.txt_efectivo_usd_cierre.value or 0)
            efectivo_bs = float(self.txt_efectivo_bs_cierre.value or 0)
        except ValueError:
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Valores numéricos inválidos"), bgcolor=ft.Colors.RED)
            )
            return
        
        # Cerrar turno
        self.turno_actual.cerrar(
            efectivo_usd_cierre=efectivo_usd,
            efectivo_bs_cierre=efectivo_bs,
            tasa_cierre=tasa_cierre,
            observaciones=self.txt_observaciones.value or ""
        )
        
        # Limpiar sesión
        session.clear_turno()
        
        self.page.show_snack_bar(
            ft.SnackBar(content=ft.Text("Turno cerrado correctamente"), bgcolor=ft.Colors.GREEN)
        )
        
        self.on_complete()
