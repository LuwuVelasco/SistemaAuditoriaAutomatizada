"""
Punto de entrada para ejecutar el servidor SAAM localmente.

Uso:
    python run.py                    # desarrollo con hot-reload
    python run.py --env production   # producción sin reload
"""

import argparse
import os

import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Servidor SAAM Backend")
    parser.add_argument("--host", default="0.0.0.0", help="Host de escucha")
    parser.add_argument("--port", type=int, default=8000, help="Puerto")
    parser.add_argument("--env",  default=os.getenv("APP_ENV", "development"), help="Entorno")
    args = parser.parse_args()

    is_dev = args.env != "production"

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=is_dev,
        log_level="debug" if is_dev else "info",
        workers=1 if is_dev else 4,
    )


if __name__ == "__main__":
    main()
