"""
Componente de formulario de pagos multimoneda
"""
import flet as ft
from typing import Callable, List
from dataclasses import dataclass
from models.transaccion import MetodoPago
from models.configuracion import get_config

@dataclass
class LineaPago:
    metodo: MetodoPago
    monto_usd: float
    monto_bs: float
    referencia: str = ""

class PaymentForm(ft.Column):
    """Formulario para agregar múltiples líneas de pago"""
    
    def __init__(self, total_requerido: float = 0.0, on_change=None):
        super().__init__()
        self.total_requerido = total_requerido
        self.on_change_callback = on_change
        self.lineas: List[LineaPago] = []
        self.tasa_cambio = get_config().tasa_dolar_bs
        self._build()
    
    def _build(self):
        self.spacing = 10
        self.scroll = ft.ScrollMode.AUTO
        
        # Contenedor de líneas de pago
        self.lineas_container = ft.Column(spacing=5)
        
        # Totales
        self.lbl_total_usd = ft.Text("$0.00", weight=ft.FontWeight.BOLD, size=16)
        self.lbl_total_bs = ft.Text("Bs 0.00", weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.GREY)
        self.lbl_restante = ft.Text("Restante: $0.00", size=14, color=ft.Colors.ORANGE)
        self.lbl_cambio = ft.Text("", size=14, color=ft.Colors.GREEN)
        
        # Botón agregar pago
        btn_agregar = ft.ElevatedButton(
            "Agregar Pago",
            icon=ft.Icons.ADD,
            on_click=self._agregar_linea
        )
        
        # Resumen
        resumen = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Resumen de Pagos", weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.Text("Total USD:"),
                        self.lbl_total_usd
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([
                        ft.Text("Total BS:"),
                        self.lbl_total_bs
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(),
                    self.lbl_restante,
                    self.lbl_cambio
                ]),
                padding=15
            )
        )
        
        self.controls = [
            ft.Text("Métodos de Pago", weight=ft.FontWeight.BOLD, size=16),
            self.lineas_container,
            btn_agregar,
            resumen
        ]
        
        # Agregar primera línea
        self._agregar_linea(None)
    
    def _agregar_linea(self, e):
        """Agrega una nueva línea de pago"""
        # Dropdown de método de pago
        dd_metodo = ft.Dropdown(
            label="Método",
            width=150,
            options=[
                ft.dropdown.Option(m.value, m.value.replace('_', ' '))
                for m in MetodoPago if m != MetodoPago.AJUSTE
            ],
            value=MetodoPago.EFECTIVO_USD.value,
            on_change=self._on_linea_change
        )
        
        # Campo de monto USD
        tf_monto_usd = ft.TextField(
            label="Monto USD",
            width=120,
            keyboard_type=ft.KeyboardType.NUMBER,
            value="0.00",
            on_change=self._on_linea_change
        )
        
        # Campo de monto BS (calculado automáticamente)
        tf_monto_bs = ft.TextField(
            label="Monto BS",
            width=120,
            keyboard_type=ft.KeyboardType.NUMBER,
            value="0.00",
            read_only=True,
            bgcolor=ft.Colors.GREY_100
        )
        
        # Campo de referencia
        tf_referencia = ft.TextField(
            label="Referencia",
            width=150,
            visible=False,
            on_change=self._on_linea_change
        )
        
        # Botón eliminar
        btn_eliminar = ft.IconButton(
            icon=ft.Icons.DELETE,
            icon_color=ft.Colors.RED,
            on_click=lambda e, row=len(self.lineas_container.controls): self._eliminar_linea(e, row)
        )
        
        # Fila de la línea
        fila = ft.Row(
            [dd_metodo, tf_monto_usd, tf_monto_bs, tf_referencia, btn_eliminar],
            alignment=ft.MainAxisAlignment.START,
            spacing=5
        )
        
        self.lineas_container.controls.append({
            'fila': fila,
            'dd_metodo': dd_metodo,
            'tf_monto_usd': tf_monto_usd,
            'tf_monto_bs': tf_monto_bs,
            'tf_referencia': tf_referencia
        })
        
        self.update()
        self._actualizar_totales()
    
    def _eliminar_linea(self, e, index):
        """Elimina una línea de pago"""
        if len(self.lineas_container.controls) > 1:
            self.lineas_container.controls.pop(index)
            self.update()
            self._actualizar_totales()
    
    def _on_linea_change(self, e):
        """Maneja cambios en cualquier campo de la línea"""
        # Actualizar campos visibles según método
        for linea in self.lineas_container.controls:
            metodo = MetodoPago(linea['dd_metodo'].value)
            requiere_ref = metodo in [MetodoPago.PAGO_MOVIL, MetodoPago.TRANSFERENCIA, 
                                       MetodoPago.ZELLE, MetodoPago.BINANCE]
            linea['tf_referencia'].visible = requiere_ref
            
            # Calcular BS desde USD
            try:
                monto_usd = float(linea['tf_monto_usd'].value or 0)
                monto_bs = monto_usd * self.tasa_cambio
                linea['tf_monto_bs'].value = f"{monto_bs:.2f}"
            except ValueError:
                linea['tf_monto_bs'].value = "0.00"
        
        self.update()
        self._actualizar_totales()
    
    def _actualizar_totales(self):
        """Calcula y muestra los totales"""
        total_usd = 0.0
        total_bs = 0.0
        
        for linea in self.lineas_container.controls:
            try:
                monto_usd = float(linea['tf_monto_usd'].value or 0)
                monto_bs = float(linea['tf_monto_bs'].value or 0)
                total_usd += monto_usd
                total_bs += monto_bs
            except ValueError:
                pass
        
        # Actualizar labels
        self.lbl_total_usd.value = f"${total_usd:,.2f}"
        self.lbl_total_bs.value = f"Bs {total_bs:,.2f}"
        
        # Calcular restante o cambio
        restante = self.total_requerido - total_usd
        if restante > 0:
            self.lbl_restante.value = f"Restante: ${restante:.2f}"
            self.lbl_restante.color = ft.Colors.ORANGE
            self.lbl_cambio.value = ""
        elif restante < 0:
            self.lbl_restante.value = "Completo ✓"
            self.lbl_restante.color = ft.Colors.GREEN
            self.lbl_cambio.value = f"Cambio/Saldo a favor: ${abs(restante):.2f}"
        else:
            self.lbl_restante.value = "Completo ✓"
            self.lbl_restante.color = ft.Colors.GREEN
            self.lbl_cambio.value = ""
        
        self.update()
        
        # Notificar cambio
        if self.on_change_callback:
            self.on_change_callback(total_usd, total_bs, restante)
    
    def obtener_lineas(self) -> List[LineaPago]:
        """Obtiene las líneas de pago validadas"""
        lineas = []
        for linea in self.lineas_container.controls:
            try:
                monto_usd = float(linea['tf_monto_usd'].value or 0)
                if monto_usd > 0:
                    lineas.append(LineaPago(
                        metodo=MetodoPago(linea['dd_metodo'].value),
                        monto_usd=monto_usd,
                        monto_bs=float(linea['tf_monto_bs'].value or 0),
                        referencia=linea['tf_referencia'].value or ""
                    ))
            except ValueError:
                pass
        return lineas
    
    def get_total_pagado(self) -> float:
        """Retorna el total pagado en USD"""
        total = 0.0
        for linea in self.obtener_lineas():
            total += linea.monto_usd
        return total
    
    def es_valido(self) -> bool:
        """Verifica si el pago es válido (total >= requerido)"""
        return self.get_total_pagado() >= self.total_requerido
    
    def get_cambio(self) -> float:
        """Retorna el cambio/saldo a favor"""
        return max(0, self.get_total_pagado() - self.total_requerido)
