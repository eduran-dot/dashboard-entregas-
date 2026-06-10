# Dashboard de Entregas

Dashboard web para visualizar reportes de entregas. Una persona sube el Excel y todos ven los datos en tiempo real.

## Estructura

```
dashboard-entregas/
├── app.py              # Backend Flask
├── requirements.txt    # Dependencias Python
├── Procfile            # Para Render
├── templates/
│   ├── index.html      # Dashboard principal
│   └── admin.html      # Página de carga del reporte
└── .gitignore
```

## Cómo usar

- **`/`** — Dashboard (todos pueden ver)
- **`/admin`** — Subir el reporte Excel diario (solo el administrador)

## Deploy en Render

1. Sube este repositorio a GitHub
2. Entra a [render.com](https://render.com) y crea cuenta con GitHub
3. New → Web Service → conecta tu repo
4. Configuración:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Plan:** Free
5. Deploy → en 2-3 minutos tienes tu URL

## Columnas requeridas en el Excel

- `Reference Number`
- `Delivery Successful`
- `Destination Branch`
- `Initial Delivery Date`

## Columnas opcionales

- `Order Out for Delivery` (1, 2, 3)
- `Tracking Status`
