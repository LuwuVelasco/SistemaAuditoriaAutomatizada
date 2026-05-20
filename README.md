# Sistema de Auditoría Automatizada Multimarco (SAAM)

Un sistema inteligente diseñado para optimizar, centralizar y acelerar el proceso de auditoría de sistemas y de TI. La plataforma automatiza la revisión documental y la generación de matrices de riesgos cruzando normativas locales e internacionales.

## 🚀 Características Principales

* **Análisis Multimarco Inteligente:** Procesa documentación técnica y operativa para identificar hallazgos basados de forma simultánea en tres pilares regulatorios:
    * **COBIT:** Gobernanza y gestión de TI.
    * **COSO:** Control interno y gestión de riesgos corporativos.
    * **RGSI de la ASFI:** Reglamento de Gestión de la Seguridad de la Información (Normativa Boliviana).
* **Flexibilidad en Reportes:** * Generación de una **Matriz de Hallazgos Integrada** (COBIT + COSO + ASFI).
    * Exportación de documentos y reportes individuales y específicos por cada marco normativo.
* **Evaluación de Riesgos Interactiva:** El sistema detecta los hallazgos potenciales y guía al auditor a través de un flujo interactivo para calificar y verificar la **Probabilidad** y el **Impacto** automatizando el cálculo del nivel de riesgo.
* **Documentación Automatizada:** Generación automática de papeles de trabajo, incluyendo **Fichas de Pruebas** y evidencias de auditoría.

---

## 🛠️ Flujo de Trabajo del Sistema

1. **Carga de Archivos:** El usuario sube los documentos, PNP, manuales u otros de la organización.
2. **Procesamiento y Mapeo:** El motor del software analiza el texto y lo contrasta con los objetivos de control de COBIT, los componentes de COSO y los artículos del RGSI de la ASFI.
3. **Validación del Auditor:** El sistema presenta los hallazgos preliminares. El auditor confirma su veracidad, causa/efecto, conclusión y recomendaciones y asigna los criterios de impacto/probabilidad.
4. **Generación de Entregables:** Se exportan las matrices integradas, reportes independientes y fichas de prueba listas para su presentación.

---

## 💻 Stack Tecnológico (Propuesto inicialmente)

* **Backend:** Python (FastAPI / Django) para el procesamiento lógico y análisis de texto.
* **Base de Datos:** PostgreSQL para el almacenamiento relacional de hallazgos, marcos y matrices.
* **Contenedores:** Docker para asegurar un despliegue rápido y consistente.

---

## 👥 Autores
* *Luciana Velasco, Daniela Guzman, Carlos Caba, Josue Nisthaus, José Manzaneda*

---
*Proyecto desarrollado en el marco del Workshop de Auditoría de Sistemas.*