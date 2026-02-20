"""
Vista de Check-out
"""
import flet as ft
from datetime import datetime
from typing import Callable
from models.registro import Registro, EstadoRegistro
from models.habitacion import Habitacion, EstadoHabitacion
from models.huesped import Huesped
from models.transaccion import Transaccion, MetodoPago, TipoTransaccion
from models.configuracion import get_config
from utils.session import session
from utils.helpers import format_money, format_datetime
from components.payment_form import PaymentForm

class CheckoutView(ft.View):
    """Vista para realizar el check-out de huéspedes"""
    
    def __init__(self, on_complete: Callable, on_cancel: Callable, registro_id: int):
        super().__init__()
        self.route = "/checkout"
        self.on_complete = on_complete
        self.on_cancel = on_cancel
        self.registro_id = registro_id
        self.registro = None
        self.config = get_config()
        self._build()
    
    def _build(self):
        self.appbar = ft.AppBar(
            title=ft.Text("Check-out de Huésped"),
            bgcolor=ft.Colors.RED,
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: self.on_cancel())
        )
        
        # Cargar datos del registro
        self.registro = Registro.buscar_por_id(self.registro_id)
        
        if not self.registro:
            self.controls = [ft.Text("Registro no encontrado", color=ft.Colors.RED)]
            return
        
        # === INFORMACIÓN DEL HUÉSPED ===
        info_huesped = ft.Column([
            ft.Text("Información del Huésped", weight=ft.FontWeight.BOLD, size=16),
            ft.Text(f"Nombre: {self.registro.huesped_nombre}"),
            ft.Text(f"Habitación: {self.registro.habitacion_numero:03d} ({self.registro.habitacion_tipo})"),
            ft.Text(f"Entrada: {format_datetime(self.registro.fecha_entrada)}"),
            ft.Text(f"Salida prevista: {format_datetime(self.registro.fecha_salida_prevista)}"),
        ])
        
        # === DETALLE DE CARGOS ===
        self.lbl_noches = ft.Text(f"Noches: {self.registro.noches_estadia}", size=12)
        self.lbl_habitacion = ft.Text(f"Habitación: ${self.registro.total_habitacion_usd:.2f}", size=12)
        self.lbl_extras = ft.Text(f"Extras: ${self.registro.total_extras_usd:.2f}", size=12)
        self.lbl_descuentos = ft.Text(f"Descuentos: -${self.registro.total_descuentos_usd:.2f}", size=12)
        self.lbl_pagado = ft.Text(f"Pagado: ${self.registro.total_pagado_usd:.2f}", size=12, color=ft.Colors.GREEN)
        
        # Saldo pendiente
        saldo_pendiente = self.registro.saldo_actual_usd
        if saldo_pendiente > 0:
            self.lbl_saldo = ft.Text(
                f"PENDIENTE POR PAGAR: ${saldo_pendiente:.2f}",
                size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED
            )
        elif saldo_pendiente < 0:
            self.lbl_saldo = ft.Text(
                f"SALDO A FAVOR: ${abs(saldo_pendiente):.2f}",
                size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN
            )
        else:
            self.lbl_saldo = ft.Text(
                "CUENTA SALDADA",
                size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN
            )
        
        detalle_cargos = ft.Column([
            ft.Text("Detalle de Cargos", weight=ft.FontWeight.BOLD, size=16),
            self.lbl_noches,
            self.lbl_habitacion,
            self.lbl_extras,
            self.lbl_descuentos,
            ft.Divider(),
            ft.Text(f"TOTAL ESTADÍA: ${self.registro.total_estadia_usd:.2f}", weight=ft.FontWeight.BOLD),
            self.lbl_pagado,
            ft.Divider(),
            self.lbl_saldo
        ])
        
        # === PAGOS ADICIONALES (si hay saldo pendiente) ===
        self.payment_container = ft.Container(visible=False)
        
        if saldo_pendiente > 0:
            self.payment_form = PaymentForm(total_requerido=saldo_pendiente)
            self.payment_container.content = ft.Column([
                ft.Text("Pago de Saldo Pendiente", weight=ft.FontWeight.BOLD, size=16),
                self.payment_form
            ])
            self.payment_container.visible = True
        
        # === BOTONES ===
        btn_completar = ft.ElevatedButton(
            "Completar Check-out",
            icon=ft.Icons.EXIT_TO_APP,
            bgcolor=ft.Colors.RED,
            color=ft.Colors.WHITE,
            on_click=self._confirmar_checkout
        )
        
        btn_cancelar = ft.OutlinedButton(
            "Cancelar",
            icon=ft.Icons.CANCEL,
            on_click=lambda e: self.on_cancel()
        )
        
        # Layout
        self.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Card(content=ft.Container(content=info_huesped, padding=15)),
                    ft.Card(content=ft.Container(content=detalle_cargos, padding=15)),
                    ft.Card(content=ft.Container(content=self.payment_container, padding=15)),
                    ft.Row([
                        btn_cancelar,
                        btn_completar
                    ], alignment=ft.MainAxisAlignment.END)
                ], scroll=ft.ScrollMode.AUTO),
                padding=20,
                expand=True
            )
        ]
    
    def _confirmar_checkout(self, e):
        """Muestra confirmación antes del checkout"""
        saldo_pendiente = self.registro.saldo_actual_usd
        
        # Si hay saldo pendiente, procesar pago
        if saldo_pendiente > 0:
            lineas_pago = self.payment_form.obtener_lineas()
            total_pagado = sum(l.monto_usd for l in lineas_pago)
            
            if total_pagado < saldo_pendiente:
                self._show_error(f"Pago insuficiente. Faltan ${saldo_pendiente - total_pagado:.2f}")
                return
            
            # Guardar pagos
            for linea in lineas_pago:
                transaccion = Transaccion(
                    registro_id=self.registro.id,
                    huesped_id=self.registro.huesped_principal_id,
                    monto_usd=linea.monto_usd,
                    tasa_cambio=self.config.tasa_dolar_bs,
                    monto_bs=linea.monto_bs,
                    metodo_pago=linea.metodo,
                    tipo=TipoTransaccion.PAGO,
                    referencia=linea.referencia,
                    concepto=f"Check-out Habitación {self.registro.habitacion_numero:03d}",
                    usuario_id=session.usuario_id,
                    turno_id=session.turno_id
                )
                transaccion.guardar()
            
            # Si hay cambio, guardar como saldo a favor
            if total_pagado > saldo_pendiente:
                cambio = total_pagado - saldo_pendiente
                huesped = Huesped.buscar_por_id(self.registro.huesped_principal_id)
                if huesped:
                    huesped.ajustar_saldo(cambio)
        
        # Si hay saldo a favor, transferirlo al huésped
        elif saldo_pendiente < 0:
            huesped = Huesped.buscar_por_id(self.registro.huesped_principal_id)
            if huesped:
                huesped.ajustar_saldo(abs(saldo_pendiente))
        
        # Realizar checkout
        self.registro.realizar_checkout(session.usuario_id)
        
        self.on_complete()
    
    def _show_error(self, message: str):
        """Muestra un mensaje de error"""
        self.page.show_snack_bar(
            ft.SnackBar(content=ft.Text(message), bgcolor=ft.Colors.RED)
        )
