import uvicorn
from app.app import (
    create_app,
)  # adjust import if your create_app is in a different module

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",  # "module_name:app_instance"
        host="0.0.0.0",  # listen on all interfaces
        port=8000,  # port number
        reload=True,  # auto-reload on code changes (dev only)
    )
