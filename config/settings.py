#config/settings

import os
from dotenv import load_dotenv

# Carregar as variáveis do arquivo .env
load_dotenv()

# Configurações JWT
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")


DATABASE_URL = os.getenv("DATABASE_URL")