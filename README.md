# DGSI-FIB-ChatBot

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-CC2927?style=for-the-badge&logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

## Descripción del Proyecto

Se trata de un proyecto experimental sobre cómo crear modelos de lenguaje con embeddings, en el marco de la asignatura DGSI de la FIB UPC.

DGSI-FIB-ChatBot es una aplicación de chatbot diseñada específicamente para la Facultad de Informática de Barcelona (FIB). El proyecto proporciona una interfaz interactiva que permite a los usuarios realizar consultas y obtener respuestas automáticas relacionadas con información de la facultad.

## Características Principales

- **API RESTful**: Construida con FastAPI para un alto rendimiento y facilidad de uso.
- **Autenticación**: Sistema de autenticación basado en JWT (JSON Web Tokens).
- **Almacenamiento de Conversaciones**: Capacidad para guardar y recuperar historial de conversaciones.
- **Interfaz Web**: Interfaz de usuario accesible desde navegadores web.
- **Sistema de Usuarios**: Gestión de cuentas de usuario con autenticación segura.

## Tecnologías Utilizadas

- **Backend**: 
  - FastAPI (framework web de alto rendimiento)
  - SQLAlchemy (ORM para interacción con bases de datos)
  - Pydantic (validación de datos y serialización)
  - Uvicorn (servidor ASGI para ejecutar la aplicación)
  - Python 3.11+

- **Seguridad**:
  - JWT para autenticación
  - Passlib para hash de contraseñas
  - Python-jose para operaciones criptográficas

- **Base de Datos**:
  - SQLite (por defecto)
  - Soporte para otras bases de datos a través de SQLAlchemy

- **Despliegue**:
  - Docker y Docker Compose para containerización y despliegue fácil

## Estructura del Proyecto

```
DGSI-FIB-ChatBot/
├── app/
│   ├── api/                # Endpoints de la API 
│   ├── core/               # Configuración central y utilidades
│   ├── db/                 # Modelos de datos y conexión a la base de datos
│   ├── schemas/            # Esquemas Pydantic para validación de datos
│   └── services/           # Lógica de negocio y servicios
├── static/                 # Archivos estáticos (HTML, CSS, JS)
├── Dockerfile              # Configuración de Docker
├── docker-compose.yml      # Configuración de Docker Compose
├── main.py                 # Punto de entrada de la aplicación
└── requirements.txt        # Dependencias del proyecto
```

## Modelos de Datos

El sistema maneja varios modelos clave:
- **User**: Gestión de usuarios y autenticación
- **Conversation**: Almacenamiento de conversaciones
- **Message**: Mensajes dentro de las conversaciones

## Instalación y Ejecución

### Requisitos Previos
- Python 3.11+
- Docker y Docker Compose (opcional, para despliegue containerizado)

### Instalación Local

1. Clonar el repositorio:
```shell script
git clone https://github.com/yourusername/DGSI-FIB-ChatBot.git
   cd DGSI-FIB-ChatBot
```

2. Crear y activar un entorno virtual:
```shell script
python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```shell script
pip install -r requirements.txt
```

4. Configurar variables de entorno (opcional):
   Crear un archivo `.env` en la raíz del proyecto con:
```
SECRET_KEY=tu_clave_secreta_aqui
   DATABASE_URL=sqlite:///./chatbot.db
```

5. Ejecutar la aplicación:
```shell script
python main.py
```

6. Acceder a la aplicación en [http://localhost:8000](http://localhost:8000)

### Despliegue con Docker

1. Construir y ejecutar los contenedores:
```shell script
docker-compose up --build
```

2. Acceder a la aplicación en [http://localhost:8000](http://localhost:8000)

## API Endpoints

- **Autenticación**:
  - `/api/v1/auth/register`: Registro de usuarios
  - `/api/v1/auth/login`: Inicio de sesión

- **Usuarios**:
  - `/api/v1/users/me`: Obtener información del usuario actual

- **Conversaciones**:
  - `/api/v1/conversations`: CRUD para conversaciones
  - `/api/v1/chat`: Endpoint para interactuar con el chatbot

## Desarrollo

### Estructura de Código
- Utilizamos Pydantic para la validación de datos
- SQLAlchemy como ORM para interactuar con la base de datos
- FastAPI para definir los endpoints de la API

### Estándares de Código
- Código formateado según PEP 8
- Documentación con docstrings
- Tipado estático en Python

## Contribución

1. Hacer fork del repositorio
2. Crear una rama para tu característica (`git checkout -b feature/amazing-feature`)
3. Realizar cambios y hacer commit (`git commit -m 'Add some amazing feature'`)
4. Hacer push a la rama (`git push origin feature/amazing-feature`)
5. Abrir un Pull Request

## Estado del Proyecto

![Estado de Desarrollo](https://img.shields.io/badge/Estado-En%20Desarrollo-yellow?style=for-the-badge)

## Equipo y Contacto

### Desarrolladores
* **Junjie Li** - [![GitHub](https://img.shields.io/badge/GitHub-junjielyu13-181717?style=flat-square&logo=github)](https://github.com/junjielyu13) - junjie.li@estudiantat.upc.edu
* **Aleix Padrell** - [![GitHub](https://img.shields.io/badge/GitHub-aleixpg-181717?style=flat-square&logo=github)](https://github.com/aleixpg) - aleix.padrell@estudiantat.upc.edu
* **Alfonso Cano** - [![GitHub](https://img.shields.io/badge/GitHub-Alfons0Cano-181717?style=flat-square&logo=github)](https://github.com/Alfons0Cano) - alfonso.cano@estudiantat.upc.edu
* **Àlex Ollé** - [![GitHub](https://img.shields.io/badge/GitHub-aolle99-181717?style=flat-square&logo=github)](https://github.com/aolle99) - alex.olle@estudiantat.upc.edu

### Supervisión Académica
**Dr. Marc Alier** - [![GitHub](https://img.shields.io/badge/GitHub-granludo-181717?style=flat-square&logo=github)](https://github.com/granludo) - marc.alier@upc.edu  
Profesor del Departamento de Ingeniería de Servicios y Sistemas de Información

### Contexto Académico
Este proyecto se ha desarrollado en el marco de la asignatura **Desarrollo y Gestión de Sistemas Inteligentes (DGSI)** del Máster en Ingeniería Informática de la [Facultad de Informática de Barcelona (FIB)](https://www.fib.upc.edu/) de la [Universitat Politècnica de Catalunya (UPC)](https://www.upc.edu/).

**Curso académico:** 2024/2025 - Segundo cuatrimestreK

## Licencia

Este proyecto está bajo la Licencia MIT - vea el archivo [LICENSE](LICENSE) para más detalles.

---

<div align="center">
  <img src="https://dse.upc.edu/es/logosfooter-es/fib/@@images/image-400-f2beea873ec10b898a274f29520bed2c.png" alt="FIB-UPC Logo" width="200"/>
  <p>Desarrollado con ❤️ en la FIB-UPC</p>
</div>