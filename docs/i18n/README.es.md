<div align="center">

# pm-skill

<p><a href="../../README.md">English</a> | <a href="README.zh-CN.md">简体中文</a> | <a href="README.zh-TW.md">繁體中文</a> | <a href="README.ja.md">日本語</a> | <a href="README.ko.md">한국어</a> | <a href="README.es.md">Español</a> | <a href="README.tr.md">Türkçe</a> | <a href="README.ru.md">Русский</a></p>

</div>

**Gestión de proyectos local-first para desarrollo asistido por IA.**

`pm-skill` guarda requisitos, TODOs, progreso de ramas, verificaciones, handovers y registros de auditoría dentro del repositorio Git. Así, personas y coding agents pueden retomar el trabajo desde hechos versionados, no desde el historial del chat.

## Por qué existe

Las sesiones de programación con IA son poderosas, pero el estado del proyecto suele quedar disperso en conversaciones. `pm-skill` hace que el repositorio pueda explicar en qué rama estás, qué TODOs existen, qué requisitos importan, qué checks corrieron y cuál es el siguiente paso.

## Características

- Local-first: el estado vive en el repositorio.
- Consciente de ramas: requisitos, TODOs y changelogs por rama.
- Markdown legible para humanos y herramientas.
- CLI, REST y MCP comparten el mismo command envelope.
- Las escrituras quedan auditadas en `.pm-skill/audit/audit-log.jsonl`.

## Quick Start

```bash
pipx install git+https://github.com/AIGRABER/pm-skill.git
```

Después de instalarlo, habla con tu coding agent en lenguaje natural:

El valor principal de `pm-skill` no es solo recuperar contexto. Es dar a AI coding un plano de control dentro del repositorio: recuperar estado -> discutir incertidumbre -> extraer requisitos borrador -> aprobar alcance -> dividir TODOs -> limitar contexto -> verificar aceptación -> auditar cambios -> handover/release.

```text
Usa pm-skill para inicializar el proyecto en C:\Users\win\Documents\MyProject. Usa project id my-project y nombre visible "My Project".
```

```text
Usa pm-skill para recuperar el estado de control del proyecto y dime la rama actual, archivos modificados, requisitos activos, TODOs abiertos, riesgos y siguiente acción segura.
```

```text
No estoy seguro de qué debe incluir el rediseño del login. Discútelo conmigo primero, haz preguntas de aclaración, extrae objetivos, restricciones, riesgos y criterios de aceptación de la conversación, y guárdalo como requisito borrador de pm-skill para revisión.
```

```text
Usa pm-skill para crear una superficie de trabajo para "Añadir flujo de inicio de sesión" y ejecuta los checks normales del repositorio.
```

```text
Crea con pm-skill un requisito borrador para "Inicio de sesión sin contraseña" y conviértelo en el límite de alcance antes de codificar: objetivo, responsables, riesgos y criterios iniciales de aceptación.
```

```text
Promueve la parte de magic-link sign-in a requisito formal, crea TODOs desde ese requisito y genera una matriz de aceptación.
```

```text
Crea un work package para el primer TODO, agrega archivos de implementación y verificación para limitar el contexto del agent, y valida la matriz de aceptación antes de marcarlo como terminado.
```

También puedes pedirlo en otro idioma; el agent traduce la intención a comandos `pm-skill`, REST o MCP.

## Ideas Clave

- Los archivos del repositorio son la fuente de verdad.
- `.pm-skill/` guarda el estado del plano de control legible por máquina.
- Markdown guarda requisitos, TODOs, changelogs, notas de aceptación y handovers.
- CLI, REST y MCP deben usar el mismo command envelope.
- Las escrituras quedan auditadas para reconstruir trabajos largos de AI coding.

## Comandos Útiles

| Comando | Uso |
| --- | --- |
| `pm-skill show-status --json` | Ver rama, archivos modificados, TODOs activos, avisos y siguiente paso. |
| `pm-skill recover-project --json` | Recuperar el estado de control y el contexto del proyecto. |
| `pm-skill create-requirement --title "..." --json` | Crear un requisito borrador desde una conversación o especificación. |
| `pm-skill promote-requirement REQ-DRAFT-... --json` | Promover un requisito borrador a requisito formal. |
| `pm-skill create-todo-from-source --source-requirement REQ-... --json` | Crear TODOs trazables desde un requisito formal. |
| `pm-skill create-acceptance-matrix TODO-... --json` | Generar una matriz de aceptación para un TODO. |
| `pm-skill create-work-package TODO-... --json` | Crear un work package enfocado para limitar el contexto del agent. |
| `pm-skill validate-acceptance TODO-... --checks-profile default --json` | Validar completitud con matriz de aceptación y checks. |
| `pm-skill handover --summary-level standard --json` | Dejar un handover para la siguiente sesión. |

## License

Apache License 2.0. See [LICENSE](../../LICENSE).
