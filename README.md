# 🏋️ Lyfta Weekly Workout Digest to Gmail (GitHub Actions)

Automatización en Python con **GitHub Actions** para extraer semanalmente tu historial de entrenamientos desde la API de **Lyfta**, procesar estadísticas clave (volumen total, rutinas, series y repeticiones) y enviarte un resumen visual y estructurado por correo electrónico a través de **Gmail**.

---

## 📁 Estructura del Proyecto

```text
├── .github/
│   └── workflows/
│       └── schedule.yml       # Workflow programado (Sábados 9:00 PM hora de Chile con ajuste DST automático)
├── .env.example               # Plantilla de variables de entorno para pruebas locales
├── .gitignore                 # Archivos y secretos ignorados por git
├── main.py                    # Script principal de extracción, Gemini AI y envío SMTP
├── requirements.txt           # Dependencias de Python (requests, google-genai, markdown, tzdata)
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

### 3. `GEMINI_API_KEY` (Recomendaciones y Coaching con Inteligencia Artificial)
Para que Google Gemini (`gemini-3.8-flash`) analice tus rutinas, sobrecarga progresiva y recuperación:

1. Entra en Google AI Studio: [https://aistudio.google.com/](https://aistudio.google.com/)
2. Inicia sesión con tu cuenta de Google.
3. Haz clic en **Get API key** > **Create API key**.
4. Copia tu clave generada (empieza por `AIzaSy...`). Esta será tu variable `GEMINI_API_KEY`.

---

## ⚙️ Configuración de Secretos en GitHub

1. En tu repositorio de GitHub, haz clic en **Settings** (pestaña superior).
2. En el menú lateral izquierdo, ve a **Secrets and variables** > **Actions**.
3. Añade los siguientes secretos:
   - `LYFTA_API_KEY`: Tu token de Lyfta.
   - `GMAIL_ADDRESS`: Tu correo Gmail.
   - `GMAIL_APP_PASSWORD`: Tu contraseña de aplicación de 16 caracteres.
   - `GEMINI_API_KEY`: Tu clave de Google AI Studio para coaching y recomendaciones con IA.
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
