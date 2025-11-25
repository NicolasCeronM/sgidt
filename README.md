# SGIDT - Sistema de Gestión Inteligente de Documentos Tributarios

**Proyecto de Título para optar al título de Ingeniero en Informática | Duoc UC**

**Autor: Nicolás Cerón, Benjamin Barraza, Claudio Tobar, Ignacio Brito**

---

## Descripción General

**SGIDT** es una solución integral diseñada para optimizar y automatizar la gestión de documentos tributarios para Pequeñas y Medianas Empresas (PyMEs) en Chile. La plataforma combina una potente aplicación web de administración con una aplicación móvil para la captura y gestión de documentos en tiempo real.

El núcleo del sistema utiliza tecnologías de **Reconocimiento Óptico de Caracteres (OCR)** para extraer información clave de facturas, boletas y notas de crédito, validando posteriormente estos datos contra los registros del Servicio de Impuestos Internos (SII) de Chile. El objetivo es reducir la carga de trabajo manual, minimizar errores y proporcionar a las empresas una visión clara y actualizada de su situación contable.

Este proyecto se ha desarrollado como parte del proceso de titulación de la carrera de Ingeniería en Informática de Duoc UC, aplicando metodologías ágiles, arquitectura de software moderna y buenas prácticas de desarrollo para entregar una solución robusta y escalable.

> **Nota:** Este proyecto se encuentra **en desarrollo activo**. Las funcionalidades descritas están en diferentes etapas de implementación.

---

## ⚠️ Nota sobre Credenciales y Seguridad

Es posible que durante la revisión del código fuente se encuentren algunas credenciales o claves de acceso (como las de la base de datos o claves secretas) directamente expuestas.

**Aclaración importante:** Esta práctica se realizó de manera intencional y únicamente para cumplir con los requisitos de evaluación de la casa de estudios, facilitando la revisión y ejecución del proyecto por parte de los docentes. **Las credenciales expuestas son exclusivamente para entornos de prueba y no tienen validez ni acceso a ningún servicio productivo.**

### ¿Cuál es la forma correcta de manejar las credenciales?

En un entorno profesional y de producción, las credenciales **nunca** deben estar escritas directamente en el código (hardcodeadas). La práctica recomendada es utilizar **variables de entorno**.

1.  **Centralizar:** Se crea un archivo en la raíz del proyecto, comúnmente llamado `.env`. Este archivo contiene todas las variables sensibles (claves de API, contraseñas de bases de datos, etc.).
2.  **Ignorar:** El archivo `.env` **debe ser incluido** en el `.gitignore` para asegurar que nunca se suba al repositorio de código.
3.  **Cargar:** La aplicación (en este caso, Django) utiliza una librería como `django-environ` para leer las variables de este archivo y cargarlas en la configuración en tiempo de ejecución.

Este método asegura que el código fuente permanezca limpio de información sensible, permitiendo que cada desarrollador o entorno (desarrollo, pruebas, producción) utilice sus propias credenciales sin modificar el código. En la sección **"Cómo Ejecutar el Proyecto Localmente"** se detalla cómo implementar este método.

---

## Características Principales

### Backend y Plataforma Web
* **Gestión Multi-Empresa:** Permite a un usuario administrar múltiples empresas desde una única cuenta.
* **Carga de Documentos:** Carga masiva de documentos (PDF, imágenes) a través de la plataforma web.
* **Procesamiento Asíncrono con OCR:** Utiliza Celery y Redis para procesar documentos en segundo plano sin bloquear la interfaz de usuario, extrayendo datos como RUT, razón social, folio, fechas y montos.
* **Integración con SII:** Sistema de validación de documentos contra la API del Servicio de Impuestos Internos.
* **Dashboard Interactivo:** Visualización de métricas clave y estado de los documentos.
* **API RESTful Segura:** Endpoints basados en Django REST Framework con autenticación JWT para la comunicación con la aplicación móvil.
* **Integraciones Externas:** Conectividad con Google Drive y Dropbox para la importación de documentos.

### Aplicación Móvil (Flutter)
* **Captura Rápida:** Digitaliza documentos físicos usando la cámara del dispositivo.
* **Visualización de Documentos:** Accede a la lista de documentos procesados, su estado y detalles.
* **Notificaciones:** Alertas sobre el estado del procesamiento de documentos.
* **Interfaz Moderna y Adaptativa:** Diseño limpio con soporte para modo claro y oscuro.

---

## Estado del Proyecto y Próximos Pasos

Este proyecto es un trabajo en progreso y continúa evolucionando. La base funcional está implementada, pero hay varias áreas clave que se están mejorando y desarrollando activamente.

**Roadmap actual:**

* **Finalizar Integración con SII:** Pasar del entorno de pruebas (`SII_USE_MOCK = True`) a una conexión productiva con la API real del SII para la validación automática de documentos.
* **Mejorar la Precisión del OCR:** Refinar los algoritmos de extracción de datos para manejar una mayor variedad de formatos de documentos y mejorar la tasa de acierto.
* **Expandir Módulo de Reportes:** Agregar gráficos más complejos, filtros avanzados y opciones de exportación (PDF, Excel) en el panel de reportes.
* **Aumentar la Cobertura de Pruebas:** Implementar tests unitarios y de integración más exhaustivos para garantizar la estabilidad y fiabilidad del sistema.
* **Despliegue en la Nube (AWS):** Preparar y ejecutar el despliegue de la aplicación en Amazon Web Services para un entorno de producción real.

---

## Tecnologías Utilizadas

El proyecto sigue una arquitectura de servicios dockerizados, facilitando un entorno de desarrollo consistente y un despliegue simplificado.

* **Backend:**
    * **Framework:** Django 5
    * **API:** Django REST Framework, Simple JWT
    * **Base de Datos:** PostgreSQL
    * **Tareas Asíncronas:** Celery
    * **Cache y Mensajería:** Redis
    * **OCR:** Tesseract, Pytesseract, PDFMiner
* **Frontend (Panel Web):**
    * HTML5, CSS3, JavaScript (Vanilla)
    * **Plantillas:** Django Templates
* **Aplicación Móvil:**
    * **Framework:** Flutter
    * **Gestión de Estado:** Provider / ChangeNotifier (implícito en `ThemeController`)
* **Infraestructura y Despliegue:**
    * **Contenerización:** Docker, Docker Compose
    * **Servidor de Producción (WSGI):** Gunicorn

---

## Cómo Ejecutar el Proyecto Localmente

La forma más sencilla de levantar todo el entorno de desarrollo es utilizando Docker y Docker Compose.

### Prerrequisitos
* [Docker](https://www.docker.com/get-started) instalado en tu sistema.
* [Docker Compose](https://docs.docker.com/compose/install/) (generalmente viene con Docker Desktop).
* Un editor de código como Visual Studio Code.
* Para la app móvil: [Flutter SDK](https://flutter.dev/docs/get-started/install) y un emulador/dispositivo configurado.

### 1. Configuración del Backend

1.  **Clona el repositorio:**
    ```bash
    git clone [https://github.com/tu-usuario/sgidt.git](https://github.com/tu-usuario/sgidt.git)
    cd sgidt
    ```

2.  **Configura las variables de entorno:**
    El backend necesita credenciales que no deben estar en el código. Crea un archivo `.env` en la raíz del proyecto. Puedes basarte en el archivo `settings.py` para saber qué variables necesitas. Como mínimo, tu `.env` debería tener:

    ```env
    # Clave secreta de Django (puedes generar una nueva)
    SECRET_KEY='django-insecure-=g+wgz+d6t+u60f(ar0$!#o#-$m=(nwcv)!_df5oz^gyuee*e0'

    # Activa el modo debug para desarrollo
    DEBUG=1

    # URL de la base de datos (Docker Compose la gestionará)
    DATABASE_URL='postgres://sgidt_user:admin123@db:5432/sgidt'

    # URLs de Redis (Docker Compose las gestionará)
    CELERY_BROKER_URL='redis://redis:6379/0'
    CELERY_RESULT_BACKEND='redis://redis:6379/1'
    ```
    > **Importante:** Para que esto funcione, primero debes adaptar tu `settings.py` para leer estas variables de entorno usando una librería como `django-environ`. Asegúrate también de que el archivo `.env` esté listado en tu `.gitignore`.

3.  **Levanta los servicios con Docker Compose:**
    Desde la raíz del proyecto, ejecuta el siguiente comando. Esto construirá las imágenes de Docker y levantará los contenedores para la web, la base de datos, Redis y el worker de Celery.

    ```bash
    docker-compose up --build
    ```

4.  **Accede a la aplicación:**
    * **Aplicación Web:** Abre tu navegador y ve a `http://localhost:8000`.
    * **Adminer (Gestor de BD):** Ve a `http://localhost:8080` para administrar la base de datos PostgreSQL.

    La primera vez que levantes el proyecto, el comando de `docker-compose` ejecutará las migraciones y recolectará los archivos estáticos automáticamente.

### 2. Configuración de la Aplicación Móvil (Flutter)

1.  **Navega al directorio de la app móvil:**
    ```bash
    cd sgidt_mobile
    ```

2.  **Instala las dependencias de Flutter:**
    ```bash
    flutter pub get
    ```

3.  **Configura la URL de la API:**
    Abre el archivo `sgidt_mobile/lib/core/config/app_config.dart` (o donde definas la URL base) y asegúrate de que apunte a tu máquina local.
    * Si usas un emulador de Android, la URL de la API debe ser `http://10.0.2.2:8000`.
    * Si usas un simulador de iOS o un dispositivo físico en la misma red, usa la IP de tu máquina (ej. `http://192.168.1.100:8000`).

4.  **Ejecuta la aplicación:**
    Asegúrate de tener un emulador corriendo o un dispositivo conectado y ejecuta:
    ```bash
    flutter run
    ```

---

## Contexto Académico

Este repositorio representa el esfuerzo, investigación y desarrollo realizados para el **Proyecto de Título de la carrera de Ingeniería en Informática de Duoc UC**. El proyecto busca no solo cumplir con los requisitos académicos, sino también proponer una solución tecnológica viable y de alto impacto para un problema real del mercado chileno.

A lo largo de su desarrollo se han aplicado conocimientos en áreas como:
* Análisis y Diseño de Software.
* Arquitectura de Sistemas.
* Desarrollo de Aplicaciones Web y Móviles.
* Administración de Bases de Datos.
* Automatización y Despliegue de Aplicaciones (DevOps).
