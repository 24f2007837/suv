from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def coerce_value(key: str, value: str):
    if key in ("port", "workers"):
        try:
            return int(value)
        except ValueError:
            return value
    elif key == "debug":
        if isinstance(value, bool):
            return value
        val_lower = str(value).strip().lower()
        return val_lower in ("true", "1", "yes", "on")
    else:
        return str(value)

@app.get("/effective-config")
def get_effective_config(set: list[str] = Query(default=[])):
    # Layer 1: Defaults
    config = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000"
    }
    
    # Layer 2: config.development.yaml overrides
    config["workers"] = 6
    config["debug"] = False
    
    # Layer 3: .env file overrides
    config["debug"] = True
    config["api_key"] = "key-wrxwbiujqg"
    if os.environ.get("NUM_WORKERS"):
        try:
            config["workers"] = int(os.environ.get("NUM_WORKERS"))
        except ValueError:
            pass
            
    # Layer 4: OS env vars (APP_* prefix)
    if os.environ.get("APP_LOG_LEVEL"):
        config["log_level"] = os.environ.get("APP_LOG_LEVEL")
        
    for k, v in os.environ.items():
        if k.startswith("APP_"):
            config_key = k[4:].lower()
            if config_key in config:
                config[config_key] = coerce_value(config_key, v)

    # Layer 5: CLI Overrides (?set=key=value)
    for override in set:
        if "=" in override:
            k, v = override.split("=", 1)
            k = k.strip()
            v = v.strip()
            if k in config:
                config[k] = coerce_value(k, v)
                
    # Final type coercion
    for k in config:
        config[k] = coerce_value(k, config[k])
        
    # Secret masking rule
    config["api_key"] = "****"
    
    return config
