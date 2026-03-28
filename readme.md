# Sistema de Ventas - CRUD con Flask y SQLite

## Requisitos cumplidos

1. **Modelo de datos relacional**
   - 3 entidades relacionadas: Clientes, Productos y Pedidos
   - Relación 1:N entre Clientes y Pedidos
   - Relación N:N entre Pedidos y Productos (mediante detalle_pedidos)

2. **Funcionalidades CRUD completas**

3. **Base de datos relacional**
   - SQLite
   - Script de creacion: esquemas.sql

4. **Interfaz funcional**
   - Diseño claro
   - Navegacion intuitiva

## Instalación y ejecución

```bash
# Crear entorno virtual
python -m venv venv

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
python app.py

#Acceder a: http://localhost:5000