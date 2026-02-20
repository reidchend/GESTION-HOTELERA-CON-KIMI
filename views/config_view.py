"""
Vista de Configuración del Sistema
"""
import flet as ft
from typing import Callable
from models.configuracion import get_config, Configuracion
from models.usuario import Usuario, RolUsuario
from utils.session import session

class ConfigView(ft.View):
    """Vista de configuración del sistema"""
    
    def __init__(self, on_back: Callable):
        super().__init__()
        self.route = "/config"
        self.on_back = on_back
        self.config = get_config()
        self._build()
    
    def _build(self):
        self.appbar = ft.AppBar(
            title=ft.Text("Configuración del Sistema"),
            bgcolor=ft.Colors.BLUE,
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda e: self.on_back())
        )
        
        # Tabs
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="General",
                    icon=ft.icons.SETTINGS,
                    content=self._build_tab_general()
                ),
                ft.Tab(
                    text="Usuarios",
                    icon=ft.icons.PEOPLE,
                    content=self._build_tab_usuarios()
                ),
                ft.Tab(
                    text="Habitaciones",
                    icon=ft.icons.HOTEL,
                    content=self._build_tab_habitaciones()
                ),
            ],
            expand=True
        )
        
        self.controls = [
            ft.Container(content=tabs, padding=20, expand=True)
        ]
    
    def _build_tab_general(self):
        """Construye la pestaña de configuración general"""
        self.txt_nombre_hotel = ft.TextField(
            label="Nombre del Hotel",
            value=self.config.nombre_hotel,
            width=400
        )
        
        self.txt_direccion = ft.TextField(
            label="Dirección",
            value=self.config.direccion,
            width=400,
            multiline=True,
            min_lines=2
        )
        
        self.txt_telefono = ft.TextField(
            label="Teléfono",
            value=self.config.telefono,
            width=200
        )
        
        self.txt_email = ft.TextField(
            label="Email",
            value=self.config.email,
            width=300
        )
        
        self.txt_rif = ft.TextField(
            label="RIF",
            value=self.config.rif,
            width=200
        )
        
        self.txt_tasa = ft.TextField(
            label="Tasa de Cambio (Bs/USD)",
            value=str(self.config.tasa_dolar_bs),
            width=200,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        btn_guardar = ft.ElevatedButton(
            "Guardar Configuración",
            icon=ft.icons.SAVE,
            on_click=self._guardar_config
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Información del Hotel", weight=ft.FontWeight.BOLD, size=18),
                self.txt_nombre_hotel,
                self.txt_direccion,
                self.txt_telefono,
                self.txt_email,
                self.txt_rif,
                ft.Divider(),
                ft.Text("Configuración Financiera", weight=ft.FontWeight.BOLD, size=18),
                self.txt_tasa,
                ft.Divider(),
                btn_guardar
            ], scroll=ft.ScrollMode.AUTO),
            padding=20
        )
    
    def _build_tab_usuarios(self):
        """Construye la pestaña de gestión de usuarios"""
        self.tabla_usuarios = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Usuario")),
                ft.DataColumn(ft.Text("Nombre")),
                ft.DataColumn(ft.Text("Rol")),
                ft.DataColumn(ft.Text("Estado")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=[]
        )
        
        btn_nuevo = ft.ElevatedButton(
            "Nuevo Usuario",
            icon=ft.icons.PERSON_ADD,
            on_click=self._mostrar_form_usuario
        )
        
        self._cargar_usuarios()
        
        return ft.Container(
            content=ft.Column([
                ft.Row([btn_nuevo], alignment=ft.MainAxisAlignment.END),
                ft.Container(
                    content=self.tabla_usuarios,
                    expand=True,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=8
                )
            ]),
            padding=20
        )
    
    def _build_tab_habitaciones(self):
        """Construye la pestaña de gestión de habitaciones"""
        from models.habitacion import Habitacion
        
        self.tabla_habitaciones = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Número")),
                ft.DataColumn(ft.Text("Tipo")),
                ft.DataColumn(ft.Text("Descripción")),
                ft.DataColumn(ft.Text("Precio USD")),
                ft.DataColumn(ft.Text("Capacidad")),
                ft.DataColumn(ft.Text("Acciones")),
            ],
            rows=[]
        )
        
        for h in Habitacion.listar_todas():
            self.tabla_habitaciones.rows.append(ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(f"{h.numero:03d}")),
                    ft.DataCell(ft.Text(h.tipo)),
                    ft.DataCell(ft.Text(h.descripcion)),
                    ft.DataCell(ft.Text(f"${h.precio_usd:.2f}")),
                    ft.DataCell(ft.Text(str(h.capacidad))),
                    ft.DataCell(ft.IconButton(
                        icon=ft.icons.EDIT,
                        tooltip="Editar",
                        on_click=lambda e, hab=h: self._editar_habitacion(hab)
                    ))
                ]
            ))
        
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=self.tabla_habitaciones,
                    expand=True,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=8
                )
            ]),
            padding=20
        )
    
    def _cargar_usuarios(self):
        """Carga la tabla de usuarios"""
        self.tabla_usuarios.rows.clear()
        
        for u in Usuario.listar_todos():
            self.tabla_usuarios.rows.append(ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(u.username)),
                    ft.DataCell(ft.Text(u.nombre_completo)),
                    ft.DataCell(ft.Text(u.rol.value)),
                    ft.DataCell(
                        ft.Text("Activo" if u.activo else "Inactivo",
                               color=ft.Colors.GREEN if u.activo else ft.Colors.RED)
                    ),
                    ft.DataCell(ft.Row([
                        ft.IconButton(
                            icon=ft.icons.EDIT,
                            tooltip="Editar",
                            on_click=lambda e, id=u.id: self._editar_usuario(id)
                        ),
                        ft.IconButton(
                            icon=ft.icons.LOCK_RESET,
                            tooltip="Cambiar Contraseña",
                            on_click=lambda e, id=u.id: self._cambiar_password(id)
                        )
                    ], spacing=0))
                ]
            ))
    
    def _guardar_config(self, e):
        """Guarda la configuración general"""
        try:
            self.config.nombre_hotel = self.txt_nombre_hotel.value
            self.config.direccion = self.txt_direccion.value
            self.config.telefono = self.txt_telefono.value
            self.config.email = self.txt_email.value
            self.config.rif = self.txt_rif.value
            self.config.tasa_dolar_bs = float(self.txt_tasa.value)
            self.config.guardar()
            
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Configuración guardada"), bgcolor=ft.Colors.GREEN)
            )
        except ValueError:
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Tasa inválida"), bgcolor=ft.Colors.RED)
            )
    
    def _mostrar_form_usuario(self, e, usuario: Usuario = None):
        """Muestra formulario para crear/editar usuario"""
        es_nuevo = usuario is None
        
        txt_username = ft.TextField(label="Usuario *", value=usuario.username if usuario else "")
        txt_nombre = ft.TextField(label="Nombre Completo *", value=usuario.nombre_completo if usuario else "")
        dd_rol = ft.Dropdown(
            label="Rol",
            value=usuario.rol.value if usuario else RolUsuario.RECEPCIONISTA.value,
            options=[ft.dropdown.Option(r.value, r.value) for r in RolUsuario]
        )
        txt_password = ft.TextField(
            label="Contraseña" + (" *" if es_nuevo else " (dejar en blanco para no cambiar)"),
            password=True,
            value=""
        )
        
        def guardar(e):
            if not txt_username.value or not txt_nombre.value:
                return
            
            if es_nuevo and not txt_password.value:
                return
            
            if es_nuevo:
                u = Usuario(
                    username=txt_username.value.strip(),
                    nombre_completo=txt_nombre.value.strip(),
                    rol=RolUsuario(dd_rol.value)
                )
                u.password_hash = Usuario.hash_password(txt_password.value)
            else:
                u = usuario
                u.username = txt_username.value.strip()
                u.nombre_completo = txt_nombre.value.strip()
                u.rol = RolUsuario(dd_rol.value)
                if txt_password.value:
                    u.password_hash = Usuario.hash_password(txt_password.value)
            
            u.guardar()
            
            dialog.open = False
            self._cargar_usuarios()
            self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Nuevo Usuario" if es_nuevo else "Editar Usuario"),
            content=ft.Column([txt_username, txt_nombre, dd_rol, txt_password], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.ElevatedButton("Guardar", on_click=guardar)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _editar_usuario(self, usuario_id: int):
        """Edita un usuario existente"""
        usuario = Usuario.buscar_por_id(usuario_id)
        if usuario:
            self._mostrar_form_usuario(None, usuario)
    
    def _cambiar_password(self, usuario_id: int):
        """Cambia la contraseña de un usuario"""
        usuario = Usuario.buscar_por_id(usuario_id)
        if not usuario:
            return
        
        txt_nueva = ft.TextField(label="Nueva Contraseña", password=True)
        txt_confirmar = ft.TextField(label="Confirmar Contraseña", password=True)
        
        def cambiar(e):
            if txt_nueva.value != txt_confirmar.value:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Las contraseñas no coinciden"), bgcolor=ft.Colors.RED)
                )
                return
            
            usuario.cambiar_password(txt_nueva.value)
            dialog.open = False
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Contraseña cambiada"), bgcolor=ft.Colors.GREEN)
            )
            self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text(f"Cambiar Contraseña - {usuario.username}"),
            content=ft.Column([txt_nueva, txt_confirmar], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.ElevatedButton("Cambiar", on_click=cambiar)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _editar_habitacion(self, habitacion):
        """Edita una habitación"""
        from models.habitacion import Habitacion
        
        txt_tipo = ft.TextField(label="Tipo", value=habitacion.tipo)
        txt_desc = ft.TextField(label="Descripción", value=habitacion.descripcion)
        txt_precio = ft.TextField(label="Precio USD", value=str(habitacion.precio_usd), keyboard_type=ft.KeyboardType.NUMBER)
        txt_capacidad = ft.TextField(label="Capacidad", value=str(habitacion.capacidad), keyboard_type=ft.KeyboardType.NUMBER)
        
        def guardar(e):
            habitacion.tipo = txt_tipo.value
            habitacion.descripcion = txt_desc.value
            habitacion.precio_usd = float(txt_precio.value or 0)
            habitacion.capacidad = int(txt_capacidad.value or 2)
            habitacion.guardar()
            
            dialog.open = False
            # Recargar pestaña
            self._build()
            self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text(f"Editar Habitación {habitacion.numero:03d}"),
            content=ft.Column([txt_tipo, txt_desc, txt_precio, txt_capacidad], tight=True),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.ElevatedButton("Guardar", on_click=guardar)
            ]
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
