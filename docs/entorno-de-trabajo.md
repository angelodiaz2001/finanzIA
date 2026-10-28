# Entorno de trabajo del proyecto FinanzIA

Este documento describe el entorno de trabajo usado para desarrollar el proyecto integrador FinanzIA: editores de código, herramienta de control de versiones y suscripciones de modelos de inteligencia artificial. Las versiones indicadas corresponden al equipo de desarrollo principal a la fecha de entrega (octubre de 2026).

Repositorio del proyecto: https://github.com/angelodiaz2001/finanzIA

## 1. Resumen

| Categoría | Herramienta | Uso en el proyecto | Costo |
|---|---|---|---|
| Editor de código principal | Visual Studio Code 1.143 | Desarrollo del backend (Python), de las APIs simuladas y del frontend (React) | Gratuito |
| Editor de código alternativo | Cursor 2.4 | Edición asistida por IA sobre la misma base de código | Por confirmar (tiene plan gratuito y planes de pago) |
| Control de versiones | Git 2.49 + GitHub + GitHub Desktop 3.5 | Historial del código, respaldo remoto y entrega del repositorio | Gratuito |
| Modelo de IA en la aplicación | API de Anthropic (Claude Opus 5.5, `claude-opus-5-5`) | Asistente conversacional y sugerencia de categorías dentro de FinanzIA | De pago, por uso (tokens consumidos) |
| Asistente de IA para programar | Claude Code (app de escritorio y extensión de VS Code 2.1) | Generación y revisión de código, documentación, pruebas | De pago (requiere plan de Claude o facturación por API; plan por confirmar) |
| Autocompletado de código | Codeium 1.48 (extensión de VS Code) | Sugerencias de código en línea | Gratuito en su plan básico (por confirmar si se usa un plan de pago) |
| Agente de IA en el editor | Claude Dev (extensión `kodu-ai.claude-dev-experimental`) | Tareas de edición asistidas desde VS Code | Extensión gratuita; consume créditos del proveedor configurado |

## 2. Editores de código

### Visual Studio Code (principal)

- Versión 1.143.1 sobre Windows 10 Pro (compilación 19045).
- Extensiones instaladas relevantes para el proyecto:
  - `ms-python.python`, `ms-python.vscode-pylance`, `ms-python.debugpy`, `ms-python.vscode-python-envs`: soporte de Python, análisis estático, depuración y selección del entorno virtual `.venv`.
  - `anthropic.claude-code`: asistente de IA integrado en el editor.
  - `codeium.codeium`: autocompletado de código con IA.
  - `kodu-ai.claude-dev-experimental`: agente de edición asistida.
  - `github.vscode-pull-request-github`, `github.remotehub`, `ms-vscode.remote-repositories`: integración con GitHub (pull requests, repositorios remotos).
  - `ms-azuretools.vscode-containers`, `ms-vscode-remote.remote-containers`: trabajo con contenedores Docker (MySQL del proyecto).
  - `mechatroner.rainbow-csv`: lectura de archivos CSV de datos de prueba.
- Configuración recomendada para el equipo: abrir la carpeta raíz del repositorio, seleccionar el intérprete de Python en `.venv\Scripts\python.exe` y activar el formateo al guardar.

### Cursor (alternativo)

- Versión 2.4.7. Es un editor derivado de VS Code con asistencia de IA integrada; comparte la misma configuración del proyecto y las extensiones de Python (`ms-python.python`, `anysphere.cursorpyright`, `ms-python.debugpy`).
- Se usa para sesiones de edición asistida; el código resultante se revisa y se versiona igual que el escrito a mano.

## 3. Control de versiones

- **Herramienta:** Git 2.49 para Windows, con Git Credential Manager para la autenticación con GitHub.
- **Cliente gráfico:** GitHub Desktop 3.5, usado para revisar cambios y sincronizar con el remoto cuando no se trabaja desde la terminal.
- **Plataforma remota:** GitHub, repositorio `angelodiaz2001/finanzIA` (rama principal `main`).
- **Identidad de los commits:** el repositorio fija a nivel local el usuario y el correo *noreply* de la cuenta educativa `angelodiaz2001`, de modo que todas las contribuciones quedan atribuidas a esa cuenta con independencia de la configuración global de cada máquina.
- **Convenciones:**
  - Mensajes de commit en español, con un título breve y un cuerpo que explica el qué y el porqué.
  - `.gitignore` excluye entornos virtuales, `node_modules`, bases de datos locales y el archivo `.env` con credenciales; `.env.example` documenta las variables sin secretos.
  - `.gitattributes` normaliza los finales de línea para que el equipo pueda trabajar en Windows, Linux o macOS.
  - Antes de cada commit se ejecutan las pruebas (`pytest`) y se verifica que no haya secretos en los archivos versionados.

## 4. Suscripciones de modelos de IA

### API de Anthropic (usada por la aplicación)

- Modelo por defecto: Claude Opus 5.5 (`claude-opus-5-5`), configurable mediante la variable `ANTHROPIC_MODEL`.
- Modalidad: de pago por uso (facturación por tokens de entrada y salida), con clave de API gestionada desde la consola de Anthropic.
- La clave se guarda únicamente en el archivo local `.env`, que no se versiona. Sin clave, la aplicación funciona sin el asistente.
- Uso en el proyecto: asistente conversacional con herramientas (tool use) y sugerencia de categorías con salida estructurada, ambos descritos en `docs/api-contracts.md`.

### Herramientas de IA para el desarrollo

| Herramienta | Modalidad | Observación |
|---|---|---|
| Claude Code (Anthropic) | De pago | Requiere una suscripción de Claude (Pro, Max o Team) o facturación por API. Plan concreto del equipo: por confirmar. |
| Codeium | Gratuita en su plan básico | Autocompletado; plan de pago opcional. Plan concreto del equipo: por confirmar. |
| Cursor | Gratuita en su plan básico | Editor con IA; planes de pago opcionales. Plan concreto del equipo: por confirmar. |
| Claude Dev (extensión) | Gratuita | Consume créditos de la API del proveedor que se configure. |

Las filas marcadas "por confirmar" deben completarse con el plan real contratado por cada integrante antes de la entrega final.

## 5. Entorno de ejecución

| Componente | Versión | Uso |
|---|---|---|
| Sistema operativo | Windows 10 Pro 22H2 (19045) | Equipo de desarrollo principal |
| Python | 3.13.3 (entorno virtual `.venv`) | Backend principal y las tres APIs simuladas (FastAPI, SQLAlchemy, pytest) |
| Node.js / npm | 24.12.0 / 11.6.2 | Frontend React con Vite y Recharts |
| Docker Desktop | 29.2.1 | Contenedor de MySQL 8 definido en `docker-compose.yml` |
| Base de datos | MySQL 8.4 (Docker) o SQLite (respaldo local sin Docker) | Persistencia de movimientos consolidados |
| Navegador | Chromium (Edge o Chrome) | Pruebas de la interfaz en http://localhost:5173 |

Los pasos de instalación y ejecución están en el [README](../README.md).
