# Sistema de Auditoría Automatizada RAG (con Google Gemini)

Este proyecto es una plataforma completa (Backend en Python + Frontend en React) diseñada para realizar auditorías automatizadas sobre documentos (PDFs, DOCX) utilizando el motor de **Google Gemini 2.5 Flash** (RAG).

---

## 🔑 1. Configurar la API Key de Gemini

Antes de iniciar el servidor, debes asegurarte de que el sistema tenga acceso a la API de Google Gemini.

1. Ve a la carpeta `backend/app/`.
2. Abre el archivo `config.py`.
3. Busca la línea donde se define `GEMINI_API_KEY` (aproximadamente en la línea 57).
4. Reemplaza el valor con tu clave secreta:
   ```python
   GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "TU_CLAVE_API_AQUI")
   ```

*(Nota: En un entorno de producción, lo ideal es crear un archivo `.env` y poner la clave ahí, pero por simplicidad para este proyecto académico, puedes dejarla directamente en `config.py`).*

---

## ⚙️ 2. Levantar el Backend (Servidor Python)

El backend expone la API REST y los WebSockets que necesita la interfaz web.

1. Abre una terminal (Símbolo del sistema o PowerShell).
2. Navega hasta la carpeta `backend` del proyecto:
   ```bash
   cd "c:\UNIVERSIDAD\NOVENO SEMESTRE\AUDITORIA DE SISTEMAS\Trabajo\SistemaAuditoriaAutomatizada\backend"
   ```
3. *(Opcional pero recomendado)* Activa tu entorno virtual de Python si estás usando uno.
4. Ejecuta el servidor con **Uvicorn**:
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```
5. Si ves un mensaje diciendo `Application startup complete`, el servidor estará corriendo exitosamente en `http://localhost:8000`.

---

## 🌐 3. Levantar el Frontend (Interfaz React)

El frontend es la página web visual donde configuras la auditoría y ves los resultados.

1. Abre **otra** terminal nueva.
2. Navega hasta la carpeta `frontend` del proyecto:
   ```bash
   cd "c:\UNIVERSIDAD\NOVENO SEMESTRE\AUDITORIA DE SISTEMAS\Trabajo\SistemaAuditoriaAutomatizada\frontend"
   ```
3. Ejecuta el servidor de desarrollo de **Vite**:
   ```bash
   npm run dev
   ```
4. La terminal te mostrará un enlace (usualmente `http://localhost:5173` o `http://localhost:5174`).
5. Abre ese enlace en tu navegador web.

---

## 🚀 4. Uso del Sistema

1. **Sube Documentos:** Ve a la pestaña "Documentos" y sube los PDFs o archivos Word que quieras auditar.
2. **Inicia Auditoría:** Ve a "Auditoría", ingresa el nombre de tu grupo y dale a **Iniciar Auditoría Automatizada**.
3. **Ver Resultados:** Espera a que la IA analice todo (tardará unos segundos). Luego el sistema te redirigirá a la vista de resultados.
4. **Exportar:** Desde la vista de resultados, podrás descargar automáticamente los informes en Word y Excel.
