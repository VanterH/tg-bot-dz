from fastapi.templating import Jinja2Templates

# Единый экземпляр шаблонов для всего приложения
templates = Jinja2Templates(directory="templates")