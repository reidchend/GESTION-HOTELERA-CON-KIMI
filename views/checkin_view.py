"""
Vista de Check-in
"""
import flet as ft
from datetime import datetime, timedelta
from typing import Callable
from models.huesped import Huesped
from models.habitacion import Habitacion, EstadoHabitacion
from models.registro import Registro
from models.configuracion import get_config
from models.transaccion import Transaccion, MetodoPago, TipoTransaccion
from utils.session import session
from utils.helpers import format_money, format_date, validar_cedula, validar_telefono, validar_email
from components.payment_form import PaymentForm, LineaPago

class CheckinView(ft.View):
    """Vista para realizar el check-in de huéspedes"""
    
    def __init__(self, on_complete: Callable, on_cancel: Callable, habitacion_numero: int = None):
        super().__init__()
        self.route = "/checkin"
        self.on_complete = on_complete
        self.on_cancel = on_cancel
        self.habitacion_numero = habitacion_numero
        self.huesped = None
        self.habitacion = None
        self.config = get_config()
        self._build()
    
    def _build(self):
        self.appbar = ft.AppBar(
            title=ft.Text("Check-in de Huésped"),
            bgcolor=ft.Colors.BLUE,
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: self.on_cancel())
        )
        
        # === SECCIÓN 1: Búsqueda de Huésped ===
        self.txt_buscar_documento = ft.TextField(
            label="Documento (Cédula/Pasaporte)",
            prefix_icon=ft.Icons.SEARCH,
            width=250,
            on_submit=self._buscar_huesped
        )
        
        btn_buscar = ft.ElevatedButton(
            "Buscar",
            icon=ft.Icons.SEARCH,
            on_click=self._buscar_huesped
        )
        
        btn_nuevo = ft.ElevatedButton(
            "Nuevo Huésped",
            icon=ft.Icons.PERSON_ADD,
            on_click=self._mostrar_form_nuevo_huesped
        )
        
        self.lbl_huesped_info = ft.Text("", size=14)
        self.lbl_saldo_huesped = ft.Text("", size=14, weight=ft.FontWeight.BOLD)
        
        # === SECCIÓN 2: Datos de la Estancia ===
        self.dd_habitacion = ft.Dropdown(
            label="Habitación",
            width=150,
            options=[
                ft.dropdown.Option(str(h.numero), f"{h.numero:03d} - {h.tipo} (${h.precio_usd:.0f})")
                for h in Habitacion.listar_disponibles()
            ],
            value=str(self.habitacion_numero) if self.habitacion_numero else None,
            on_change=self._on_habitacion_change
        )
        
        # Fechas
        hoy = datetime.now()
        manana = hoy + timedelta(days=1)
        
        self.dp_entrada = ft.TextField(
            label="Fecha Entrada",
            value=hoy.strftime("%d/%m/%Y"),
            read_only=True,
            width=150
        )
        
        self.dp_salida = ft.TextField(
            label="Fecha Salida",
            value=manana.strftime("%d/%m/%Y"),
            width=150,
            hint_text="DD/MM/AAAA"
        )
        
        self.lbl_noches = ft.Text("1 noche", size=12, color=ft.Colors.GREY)
        
        # === SECCIÓN 3: Pre-factura ===
        self.lbl_precio_noche = ft.Text("Precio/noche: $0.00", size=12)
        self.lbl_subtotal = ft.Text("Subtotal: $0.00", size=14)
        self.lbl_deuda_anterior = ft.Text("Deuda anterior: $0.00", size=12, color=ft.Colors.RED)
        self.lbl_saldo_favor = ft.Text("Saldo a favor: $0.00", size=12, color=ft.Colors.GREEN)
        self.lbl_total = ft.Text("TOTAL: $0.00", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE)
        
        # === SECCIÓN 4: Pagos ===
        self.payment_form = PaymentForm(total_requerido=0, on_change=self._on_pago_change)
        
        # === BOTONES ===
        btn_guardar = ft.ElevatedButton(
            "Completar Check-in",
            icon=ft.Icons.CHECK_CIRCLE,
            bgcolor=ft.Colors.GREEN,
            color=ft.Colors.WHITE,
            on_click=self._guardar_checkin
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
                    # Búsqueda de huésped
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text("1. Buscar Huésped", weight=ft.FontWeight.BOLD, size=16),
                                ft.Row([
                                    self.txt_buscar_documento,
                                    btn_buscar,
                                    btn_nuevo
                                ]),
                                self.lbl_huesped_info,
                                self.lbl_saldo_huesped
                            ]),
                            padding=15
                        )
                    ),
                    
                    # Datos de estancia
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text("2. Datos de la Estancia", weight=ft.FontWeight.BOLD, size=16),
                                ft.Row([
                                    self.dd_habitacion,
                                    self.dp_entrada,
                                    self.dp_salida,
                                    self.lbl_noches
                                ]),
                                self.lbl_precio_noche
                            ]),
                            padding=15
                        )
                    ),
                    
                    # Pre-factura
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text("3. Resumen de Cargo", weight=ft.FontWeight.BOLD, size=16),
                                self.lbl_subtotal,
                                self.lbl_deuda_anterior,
                                self.lbl_saldo_favor,
                                ft.Divider(),
                                self.lbl_total
                            ]),
                            padding=15
                        )
                    ),
                    
                    # Pagos
                    ft.Card(
                        content=ft.Container(
                            content=self.payment_form,
                            padding=15
                        )
                    ),
                    
                    # Botones
                    ft.Row([
                        btn_cancelar,
                        btn_guardar
                    ], alignment=ft.MainAxisAlignment.END)
                    
                ], scroll=ft.ScrollMode.AUTO),
                padding=20,
                expand=True
            )
        ]
        
        # Cargar habitación inicial
        if self.habitacion_numero:
            self._cargar_habitacion(self.habitacion_numero)
    
    def _buscar_huesped(self, e):
        """Busca un huésped por documento"""
        documento = self.txt_buscar_documento.value.strip()
        if not documento:
            return
        
        self.huesped = Huesped.buscar_por_documento(documento)
        
        if self.huesped:
            self.lbl_huesped_info.value = f"✓ {self.huesped.nombre_completo}"
            self.lbl_huesped_info.color = ft.Colors.GREEN
            
            if self.huesped.tiene_saldo_favor:
                self.lbl_saldo_huesped.value = f"Saldo a favor: ${self.huesped.saldo_acumulado:.2f}"
                self.lbl_saldo_huesped.color = ft.Colors.GREEN
            elif self.huesped.tiene_deuda:
                self.lbl_saldo_huesped.value = f"Deuda pendiente: ${abs(self.huesped.saldo_acumulado):.2f}"
                self.lbl_saldo_huesped.color = ft.Colors.RED
            else:
                self.lbl_saldo_huesped.value = "Sin saldo pendiente"
                self.lbl_saldo_huesped.color = ft.Colors.GREY
        else:
            self.lbl_huesped_info.value = "Huésped no encontrado. Cree uno nuevo."
            self.lbl_huesped_info.color = ft.Colors.ORANGE
            self.lbl_saldo_huesped.value = ""
        
        self._calcular_totales()
        self.update()
    
    def _mostrar_form_nuevo_huesped(self, e):
        """Muestra diálogo para crear nuevo huésped"""
        # Campos del formulario
        txt_nombres = ft.TextField(label="Nombres", width=250)
        txt_apellidos = ft.TextField(label="Apellidos", width=250)
        txt_documento = ft.TextField(label="Documento", value=self.txt_buscar_documento.value, width=250)
        txt_telefono = ft.TextField(label="Teléfono", width=250)
        txt_email = ft.TextField(label="Email (opcional)", width=250)
        txt_nacionalidad = ft.TextField(label="Nacionalidad", value="Venezolano", width=250)
        
        def guardar_nuevo(e):
            # Validaciones
            if not txt_nombres.value or not txt_apellidos.value or not txt_documento.value:
                return
            
            # Crear huésped
            self.huesped = Huesped(
                documento=txt_documento.value.strip(),
                nombres=txt_nombres.value.strip(),
                apellidos=txt_apellidos.value.strip(),
                telefono=txt_telefono.value.strip(),
                email=txt_email.value.strip(),
                nacionalidad=txt_nacionalidad.value.strip()
            )
            self.huesped.guardar()
            
            # Actualizar UI
            self.lbl_huesped_info.value = f"✓ Nuevo huésped: {self.huesped.nombre_completo}"
            self.lbl_huesped_info.color = ft.Colors.GREEN
            self.lbl_saldo_huesped.value = "Sin saldo pendiente"
            self.lbl_saldo_huesped.color = ft.Colors.GREY
            
            dialog.open = False
            self.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Nuevo Huésped"),
            content=ft.Column([
                txt_nombres, txt_apellidos, txt_documento,
                txt_telefono, txt_email, txt_nacionalidad
            ], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.ElevatedButton("Guardar", on_click=guardar_nuevo)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _on_habitacion_change(self, e):
        """Maneja cambio de habitación"""
        if self.dd_habitacion.value:
            self._cargar_habitacion(int(self.dd_habitacion.value))
    
    def _cargar_habitacion(self, numero: int):
        """Carga información de la habitación"""
        self.habitacion = Habitacion.buscar_por_numero(numero)
        if self.habitacion:
            self.lbl_precio_noche.value = f"Precio/noche: ${self.habitacion.precio_usd:.2f}"
            self._calcular_totales()
    
    def _calcular_totales(self):
        """Calcula los totales de la pre-factura"""
        if not self.habitacion:
            return
        
        # Calcular noches
        try:
            fecha_salida = datetime.strptime(self.dp_salida.value, "%d/%m/%Y")
            fecha_entrada = datetime.now()
            noches = max(1, (fecha_salida - fecha_entrada).days)
        except:
            noches = 1
        
        self.lbl_noches.value = f"{noches} {'noche' if noches == 1 else 'noches'}"
        
        # Subtotal
        subtotal = noches * self.habitacion.precio_usd
        self.lbl_subtotal.value = f"Subtotal: ${subtotal:.2f}"
        
        # Deuda/Saldo del huésped
        deuda = 0.0
        saldo_favor = 0.0
        
        if self.huesped:
            if self.huesped.tiene_deuda:
                deuda = abs(self.huesped.saldo_acumulado)
                self.lbl_deuda_anterior.value = f"Deuda anterior: ${deuda:.2f}"
                self.lbl_deuda_anterior.visible = True
                self.lbl_saldo_favor.visible = False
            elif self.huesped.tiene_saldo_favor:
                saldo_favor = self.huesped.saldo_acumulado
                self.lbl_saldo_favor.value = f"Saldo a favor: ${saldo_favor:.2f}"
                self.lbl_saldo_favor.visible = True
                self.lbl_deuda_anterior.visible = False
            else:
                self.lbl_deuda_anterior.visible = False
                self.lbl_saldo_favor.visible = False
        else:
            self.lbl_deuda_anterior.visible = False
            self.lbl_saldo_favor.visible = False
        
        # Total
        total = subtotal + deuda - saldo_favor
        self.lbl_total.value = f"TOTAL: ${total:.2f}"
        
        # Actualizar formulario de pagos
        self.payment_form.total_requerido = total
        self.payment_form._actualizar_totales()
    
    def _on_pago_change(self, total_usd, total_bs, restante):
        """Maneja cambios en el pago"""
        pass
    
    def _guardar_checkin(self, e):
        """Guarda el check-in completo"""
        # Validaciones
        if not self.huesped:
            self._show_error("Debe seleccionar un huésped")
            return
        
        if not self.habitacion:
            self._show_error("Debe seleccionar una habitación")
            return
        
        if not session.tiene_turno_abierto:
            self._show_error("Debe abrir un turno primero")
            return
        
        # Obtener líneas de pago
        lineas_pago = self.payment_form.obtener_lineas()
        total_pagado = sum(l.monto_usd for l in lineas_pago)
        total_requerido = self.payment_form.total_requerido
        
        if total_pagado < total_requerido:
            self._show_error(f"El pago es insuficiente. Faltan ${total_requerido - total_pagado:.2f}")
            return
        
        # Calcular fechas
        try:
            fecha_salida = datetime.strptime(self.dp_salida.value, "%d/%m/%Y")
        except:
            self._show_error("Fecha de salida inválida")
            return
        
        # Crear registro
        registro = Registro(
            huesped_principal_id=self.huesped.id,
            habitacion_numero=self.habitacion.numero,
            fecha_entrada=datetime.now(),
            fecha_salida_prevista=fecha_salida,
            usuario_checkin_id=session.usuario_id
        )
        
        # Calcular noches y total
        noches = max(1, (fecha_salida - datetime.now()).days)
        registro.total_habitacion_usd = noches * self.habitacion.precio_usd
        
        # Aplicar deuda/saldo anterior
        if self.huesped.tiene_deuda:
            registro.total_extras_usd = abs(self.huesped.saldo_acumulado)
        elif self.huesped.tiene_saldo_favor:
            registro.total_descuentos_usd = self.huesped.saldo_acumulado
        
        # Guardar registro
        registro_id = registro.guardar()
        
        # Procesar pagos
        cambio = 0.0
        for linea in lineas_pago:
            transaccion = Transaccion(
                registro_id=registro_id,
                huesped_id=self.huesped.id,
                monto_usd=linea.monto_usd,
                tasa_cambio=self.config.tasa_dolar_bs,
                monto_bs=linea.monto_bs,
                metodo_pago=linea.metodo,
                tipo=TipoTransaccion.PAGO,
                referencia=linea.referencia,
                concepto=f"Check-in Habitación {self.habitacion.numero:03d}",
                usuario_id=session.usuario_id,
                turno_id=session.turno_id
            )
            transaccion.guardar()
        
        # Si hay cambio, guardar como saldo a favor
        if total_pagado > total_requerido:
            cambio = total_pagado - total_requerido
            self.huesped.ajustar_saldo(cambio)
        
        # Si había deuda, limpiarla
        if self.huesped.tiene_deuda:
            self.huesped.saldo_acumulado = 0
            self.huesped.guardar()
        
        # Si había saldo a favor, consumirlo
        elif self.huesped.tiene_saldo_favor:
            saldo_usado = min(self.huesped.saldo_acumulado, registro.total_habitacion_usd)
            self.huesped.saldo_acumulado -= saldo_usado
            self.huesped.guardar()
        
        self.on_complete()
    
    def _show_error(self, message: str):
        """Muestra un mensaje de error"""
        self.page.show_snack_bar(
            ft.SnackBar(content=ft.Text(message), bgcolor=ft.Colors.RED)
        )
