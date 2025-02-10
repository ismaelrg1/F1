# 🏎️ Proyecto de Apuestas de F1 con Flask & FastF1

Este es un proyecto web desarrollado en **Python** utilizando **Flask**, **Flask-SQLAlchemy** y **FastF1**, donde un grupo de amigos puede realizar apuestas sobre las carreras de F1 y ver su progreso en un ranking global. 🔥

## 🚀 Características
- 📊 **Base de datos con Flask-SQLAlchemy**.
- 🏠 **Página Home** con diseño y navegación.
- 📅 **Página de calendario** con las fechas de las carreras.
- 🏁 **Página de carreras** donde se pueden visualizar detalles.
- 🎲 **Añadir apuesta a la base de datos con restricciones temporales**.
- 🛠 **CLI** con comandos como `add_user`, `add_temporada`, `add_apuesta`.
- ⚡ **SocketIO** implementado para futuras funcionalidades en tiempo real.
- 🔐 **Sistema de login** y restricciones de acceso para usuarios no autenticados.

---

## 📌 Instalación y Configuración
### **1️⃣ Crear un entorno virtual de Python**
Ejecuta en la terminal:
```sh
python -m venv venv
```
Activa el entorno virtual:
- **Windows**:
  ```sh
  venv\Scripts\activate
  ```
- **Mac/Linux**:
  ```sh
  source venv/bin/activate
  ```

### **2️⃣ Instalar dependencias**
Ejecuta:
```sh
pip install -r requirements.txt
```
Esto instalará todas las librerías necesarias, como **Flask, Flask-SQLAlchemy y FastF1**.

### **3️⃣ Configurar variables de entorno**
Es necesario crear un archivo `.env` en el directorio `backend/app/.env` con las credenciales necesarias. Ejemplo del archivo:
```env
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here
DATABASE_URL=sqlite:///database_f1.db
```

### **4️⃣ Ejecutar la aplicación**
Inicia el servidor web con el siguiente comando:
```sh
python start.py
```

---

## 📅 TODO - Funcionalidades Pendientes
🔨 **Cosas por hacer:**
- 📌 **Crear la página del ranking**.
- 📊 **Calcular puntuación de los usuarios según los resultados de FastF1**.
- ⏳ **Automatizar cálculos con un `crontab` o `Flask_APScheduler`**.
- 👀 **Decidir cómo mostrar las apuestas de otros usuarios**.
- 🔄 **Posible cambio a ID de `Season` en el modelo `RaceEvent`**.
- 🔑 **Convertir `race_event` en llave foránea en el modelo `ScoreRace`**.
- 🗑️ **Eliminar `get_season_id_from_race_event()` si se modifica el modelo `RaceEvent`**.
- 📝 **Refactorizar `set_bet()` para simplificar su código**.
- 🔄 **Modificar completamente la API `get_bets()`**.
- 🔄 **Optimizar `get_bets_for_race()` para hacerlo más eficiente**.
- 🐳 **Añadir soporte para Docker**.

✅ **Cosas ya implementadas:**
- 🛠 **Base de datos funcional**.
- 🏠 **Página Home** con diseño.
- 📅 **Página calendario** con su respectivo diseño.
- 🏁 **Página de carreras** y su diseño.
- 🎲 **Añadir apuesta a la base de datos con restricción temporal**.
- 🔧 **CLI con comandos `add_user`, `add_temporada`, `add_apuesta`**.
- ⚡ **Implementación de SocketIO para futuros desarrollos**.
- 🔐 **Sistema de login** y restricciones de acceso.
- 🎨 **Decorar las páginas web**.

---
