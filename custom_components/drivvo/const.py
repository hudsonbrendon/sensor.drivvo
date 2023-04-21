from datetime import datetime, timedelta


ICON = "mdi:gas-station"
SCAN_INTERVAL = timedelta(minutes=60)
ATTRIBUTION = "Data provided by drivvo api"
DOMAIN = "drivvo"
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_MODEL = "model"
CONF_ID_VEHICLE = "id_vehicle"
LOGIN_BASE_URL = "https://api.drivvo.com/autenticacao/login"
BASE_URL = "https://api.drivvo.com/veiculo/{}/{}/web"
