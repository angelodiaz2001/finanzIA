# Constitución del Proyecto FinanzIA

Principios no negociables para cualquier cambio desarrollado por personas o por agentes en este repositorio:

1. **La IA interpreta, nunca calcula:** todo monto, porcentaje, promedio o agregación financiera se calcula en código determinista (`backend/app/analytics.py` o servicios de dominio). El asistente (`backend/app/ai/assistant.py`) solo consulta herramientas con `"strict": True` y explica resultados.
2. **Reglas contables obligatorias:** todo indicador financiero excluye movimientos marcados como duplicados (`Transaction.is_duplicate == True`) y excluye `Transferencias internas` de ingresos y gastos; en métricas de comercios y gastos de consumo se excluye también `Transferencias enviadas`.
3. **Contrato sincronizado entre capas:** el frontend usa JavaScript sin TypeScript; todo cambio o adición de endpoint actualiza `docs/api-contracts.md` junto al código de `backend/app/` antes de consumirlo en `frontend/src/api.js`.
4. **TDD con permisos separados:** las pruebas se escriben desde los criterios de aceptación de `spec.md` antes de implementar (`Red -> Green -> Refactor`). El agente que programa no edita la carpeta de pruebas y el umbral mínimo de cobertura es del 80 % en backend y frontend.
5. **Protección de entorno, datos simulados y diseño visual:** queda prohibido leer o editar `.env`, alterar puertos o credenciales de `docker-compose.yml`, modificar las tres APIs simuladas de `services/**` o introducir colores hexadecimales fijos en componentes JSX fuera de `frontend/src/styles.css`.
6. **Trazabilidad hacia `main`:** todo cambio entra desde una rama independiente mediante Pull Request con el workflow de integración continua en verde y revisión humana del equipo.
