"""
Vista de Gestión de Huéspedes
"""
import flet as ft
from typing import Callable
from models.huesped import Huesped
from utils.helpers import format_date, format_money

class HuespedesView(ft.View):
    """Vista para gestionar huéspedes"""
    
    def __init__(self, on_back: Callable, on_select: Callable = None):
        super().__init__()
        self.route = "/huespedes"
        self.on_back = on_back
        self.on_select = on_select
        self.huespedes = []
        self._build()
    
    def _build(self):
        self.appbar = ft.AppBar(
            title=ft.Text("Gestión de Huéspedes"),
            bgcolor=ft.Colors.BLUE,
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda e: self.on_back())
        )
        
        # Barra de búsqueda
        self.txt_buscar = ft.TextField(
            label="Buscar por nombre o documento",
            prefix_icon=ft.icons.SEARCH,
            expand=True,
            on_change=self._buscar
        )
        
        btn_nuevo = ft.ElevatedButton(
            "Nuevo Huésped",
            icon=ft.icons.PERSON_ADD,
            on_click=self._mostrar_form_nuevo
        )
        
        # Tabla de huéspedes
        self.tabla = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Documento")),
                ft.DataColumn(ft.Text("Nombre")),
                ft.DataColumn(ft.Text("Teléfono")),
                ft.DataColumn(ft.Text("Saldo")),
                ft.DataColumn(ft.Text("Última Visita")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=[],
            expand=True
        )
        
        # Layout
        self.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Row([self.txt_buscar, btn_nuevo]),
                    ft.Container(
                        content=self.tabla,
                        expand=True,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=8
                    )
                ]),
                padding=20,
                expand=True
            )
        ]
        
        self._cargar_huespedes()
    
    def _cargar_huespedes(self):
        """Carga la lista de huéspedes"""
        self.huespedes = Huesped.listar_todos()
        self._actualizar_tabla()
    
    def _actualizar_tabla(self):
        """Actualiza la tabla con los huéspedes filtrados"""
        self.tabla.rows.clear()
        
        for h in self.huespedes:
            # Color según saldo
            saldo_color = ft.Colors.BLACK
            saldo_texto = f"${h.saldo_acumulado:.2f}"
            if h.tiene_saldo_favor:
                saldo_color = ft.Colors.GREEN
                saldo_texto = f"+${h.saldo_acumulado:.2f}"
            elif h.tiene_deuda:
                saldo_color = ft.Colors.RED
                saldo_texto = f"-${abs(h.saldo_acumulado):.2f}"
            
            acciones = ft.Row([
                ft.IconButton(
                    icon=ft.icons.EDIT,
                    tooltip="Editar",
                    on_click=lambda e, id=h.id: self._editar_huesped(id)
                ),
                ft.IconButton(
                    icon=ft.icons.HISTORY,
                    tooltip="Historial",
                    on_click=lambda e, id=h.id: self._ver_historial(id)
                )
            ], spacing=0)
            
            if self.on_select:
                acciones.controls.insert(0, ft.IconButton(
                    icon=ft.icons.CHECK_CIRCLE,
                    tooltip="Seleccionar",
                    icon_color=ft.Colors.GREEN,
                    on_click=lambda e, id=h.id: self.on_select(Huesped.buscar_por_id(id))
                ))
            
            self.tabla.rows.append(ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(h.documento)),
                    ft.DataCell(ft.Text(h.nombre_completo)),
                    ft.DataCell(ft.Text(h.telefono or "-")),
                    ft.DataCell(ft.Text(saldo_texto, color=saldo_color)),
                    ft.DataCell(ft.Text(format_date(h.ultima_visita))),
                    ft.DataCell(acciones)
                ]
            ))
        
        self.update()
    
    def _buscar(self, e):
        """Filtra huéspedes según búsqueda"""
        texto = self.txt_buscar.value.lower()
        if texto:
            self.huespedes = [h for h in Huesped.listar_todos() 
                            if texto in h.nombre_completo.lower() 
                            or texto in h.documento.lower()]
        else:
            self.huespedes = Huesped.listar_todos()
        self._actualizar_tabla()
    
    def _mostrar_form_nuevo(self, e):
        """Muestra formulario para nuevo huésped"""
        self._mostrar_form_huesped(None)
    
    def _editar_huesped(self, huesped_id: int):
        """Muestra formulario para editar huésped"""
        huesped = Huesped.buscar_por_id(huesped_id)
        if huesped:
            self._mostrar_form_huesped(huesped)
    
    def _mostrar_form_huesped(self, huesped: Huesped = None):
        """Muestra formulario de huésped (nuevo o edición)"""
        es_nuevo = huesped is None
        
        txt_nombres = ft.TextField(label="Nombres *", value=huesped.nombres if huesped else "")
        txt_apellidos = ft.TextField(label="Apellidos *", value=huesped.apellidos if huesped else "")
        txt_documento = ft.TextField(label="Documento *", value=huesped.documento if huesped else "")
        txt_telefono = ft.TextField(label="Teléfono", value=huesped.telefono if huesped else "")
        txt_email = ft.TextField(label="Email", value=huesped.email if huesped else "")
        txt_nacionalidad = ft.TextField(label="Nacionalidad", value=huesped.nacionalidad if huesped else "Venezolano")
        txt_profesion = ft.TextField(label="Profesión", value=huesped.profesion if huesped else "")
        txt_vehiculo = ft.TextField(label="Vehículo", value=huesped.vehiculo if huesped else "")
        txt_placa = ft.TextField(label="Placa", value=huesped.placa_vehiculo if huesped else "")
        
        def guardar(e):
            if not txt_nombres.value or not txt_apellidos.value or not txt_documento.value:
                return
            
            if es_nuevo:
                h = Huesped()
            else:
                h = huesped
            
            h.nombres = txt_nombres.value.strip()
            h.apellidos = txt_apellidos.value.strip()
            h.documento = txt_documento.value.strip()
            h.telefono = txt_telefono.value.strip()
            h.email = txt_email.value.strip()
            h.nacionalidad = txt_nacionalidad.value.strip()
            h.profesion = txt_profesion.value.strip()
            h.vehiculo = txt_vehiculo.value.strip()
            h.placa_vehiculo = txt_placa.value.strip()
            
            h.guardar()
            
            dialog.open = False
            self._cargar_huespedes()
            self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Nuevo Huésped" if es_nuevo else "Editar Huésped"),
            content=ft.Column([
                txt_nombres, txt_apellidos, txt_documento,
                txt_telefono, txt_email, txt_nacionalidad,
                txt_profesion, txt_vehiculo, txt_placa
            ], tight=True, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.ElevatedButton("Guardar", on_click=guardar)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _ver_historial(self, huesped_id: int):
        """Muestra el historial de estadías del huésped"""
        from models.registro import Registro
        
        registros = Registro.listar_por_huesped(huesped_id)
        huesped = Huesped.buscar_por_id(huesped_id)
        
        if not registros:
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("No hay historial para este huésped"))
            )
            return
        
        lista = ft.Column(tight=True, spacing=5)
        for r in registros:
            lista.controls.append(ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(f"Habitación {r.habitacion_numero:03d} - {r.habitacion_tipo}"),
                        ft.Text(f"Entrada: {format_date(r.fecha_entrada)} - Salida: {format_date(r.fecha_salida_real or r.fecha_salida_prevista)}"),
                        ft.Text(f"Total: ${r.total_estadia_usd:.2f} | Estado: {r.estado.value}", 
                               color=ft.Colors.GREY, size=12)
                    ]),
                    padding=10
                )
            ))
        
        dialog = ft.AlertDialog(
            title=ft.Text(f"Historial de {huesped.nombre_completo}"),
            content=ft.Container(content=lista, width=400, height=300),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: setattr(dialog, 'open', False))]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
