# 🏋️ Lyfta Weekly Workout Digest to Gmail (GitHub Actions)

Automatización en Python con **GitHub Actions** para extraer semanalmente tu historial de entrenamientos desde la API de **Lyfta**, procesar estadísticas clave (volumen total, rutinas, series y repeticiones) y enviarte un resumen visual y estructurado por correo electrónico a través de **Gmail**.

---

## 📁 Estructura del Proyecto

```text
├── .github/
│   └── workflows/
│       └── schedule.yml       # Workflow programado de GitHub Actions (Domingos 08:00 UTC)
├── .env.example               # Plantilla de variables de entorno para pruebas locales
├── .gitignore                 # Archivos y secretos ignorados por git
├── main.py                    # Script principal de extracción, procesamiento y envío SMTP
├── requirements.txt           # Dependencias de Python
└── README.md                  # Documentación completa y guía de configuración
```

---

## 🔑 Cómo Obtener tus Credenciales y Claves API

> [!IMPORTANT]
> Por razones de seguridad y privacidad, las claves y contraseñas personales nunca deben subirse al repositorio ni compartirse. Sigue estos pasos para obtenerlas en tus cuentas:

### 1. `GMAIL_APP_PASSWORD` (Contraseña de Aplicación de Google)
Para permitir que el script envíe correos desde tu cuenta de Gmail:

1. Ve a tu cuenta de Google: [https://myaccount.google.com/](https://myaccount.google.com/)
2. En el menú lateral izquierdo, haz clic en **Seguridad**.
3. Asegúrate de tener activada la **Verificación en dos pasos**.
4. En la barra de búsqueda superior de tu cuenta de Google, escribe **"Contraseñas de aplicaciones"** (o accede directamente a [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)).
5. Escribe un nombre descriptivo para la aplicación (por ejemplo: `Lyfta Digest Bot`).
6. Haz clic en **Crear**.
7. Google te mostrará un código de 16 caracteres (ejemplo: `abcd efgh ijkl mnop`).
8. Copia esa contraseña de 16 caracteres. Esta será tu variable `GMAIL_APP_PASSWORD`.

### 2. `LYFTA_API_KEY` (Token de la API de Lyfta)
1. Inicia sesión en la plataforma web de Lyfta: [https://my.lyfta.app/](https://my.lyfta.app/)
2. Ve a tu perfil o configuración de cuenta (**Settings / Profile**).
3. Busca la sección de **Developer API** o **Integrations / API Access**.
4. Genera tu nuevo token de acceso personal (**Personal Access Token / API Key**).
5. Copia el token generado. Esta será tu variable `LYFTA_API_KEY`.

---

## ⚙️ Configuración de Secretos en GitHub

1. En tu repositorio de GitHub, haz clic en **Settings** (pestaña superior).
2. En el menú lateral izquierdo, ve a **Secrets and variables** > **Actions**.
3. Haz clic en el botón verde **New repository secret** y añade los siguientes 3 secretos:
   - Nombre: `LYFTA_API_KEY` | Valor: *Tu token de Lyfta*
   - Nombre: `GMAIL_ADDRESS` | Valor: *Tu correo Gmail (ej. juan@gmail.com)*
   - Nombre: `GMAIL_APP_PASSWORD` | Valor: *Tu contraseña de aplicación de 16 caracteres*
4. ¡Listo! El workflow [.github/workflows/schedule.yml](file:///.github/workflows/schedule.yml) se ejecutará automáticamente todos los **domingos a las 08:00 AM UTC**.
5. **Para probarlo de inmediato sin esperar al domingo:**
   - Ve a la pestaña **Actions** en tu repositorio de GitHub.
   - En la lista de workflows a la izquierda, selecciona **Weekly Lyfta Workout Digest**.
   - Haz clic en el botón **Run workflow** > **Run workflow**.

---

## 💻 Ejecución y Pruebas en Local (Opcional)

Si deseas probar el script directamente en tu máquina:

1. Crea y activa un entorno virtual de Python:
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   # En Linux / macOS:
   source venv/bin/activate
   ```

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Crea tu archivo de variables locales a partir de la plantilla:
   ```bash
   cp .env.example .env
   ```
   Edita `.env` con tus credenciales reales.

4. Ejecuta el script:
   ```bash
   python main.py
   ```
