# Laboratorio 2FA (TOTP) desde cero + Observabilidad con Prefect

Prueba de concepto de autenticación escalonada (Step-Up Auth) con doble factor TOTP (RFC 6238):

| Pieza | Tecnología | Carpeta |
|---|---|---|
| App Authenticator (funciona en modo avión) | Flutter (Android / iOS) | [`mobile-authenticator/`](mobile-authenticator/) |
| Backend de autenticación | Python · FastAPI | [`backend-prefect/`](backend-prefect/) |
| Orquestación y observabilidad | Prefect 3 (servidor local) | [`backend-prefect/app/infrastructure/orchestration/`](backend-prefect/app/infrastructure/orchestration/) |
| Base de datos de usuarios | Supabase (o SQLite si no hay credenciales) | [`backend-prefect/supabase_schema.sql`](backend-prefect/supabase_schema.sql) |
| Web app de login | HTML + JS, la sirve el mismo backend en `/` | [`backend-prefect/app/presentation/web/`](backend-prefect/app/presentation/web/) |

La app móvil y el backend **no se comunican**: solo comparten la semilla (vía QR) y el reloj.

---

## 1. Arquitectura

### Flujo general

```
Web (usuario+contraseña) ──POST /auth/login──▶ pre_auth_token (scope=pre_auth, 5 min)
                                                     │
App móvil (offline): HMAC-SHA1(K, floor(t/30)) ──▶ código de 6 dígitos
                                                     │
Web ──POST /auth/verify-2fa {pre_auth_token, code}──▶ Flow Prefect "verify-2fa"
        ├─ Task 1 validate_pre_auth_state
        ├─ Task 2 check_anti_replay_cache   (ReplayAttackDetected → Flow FAILED)
        ├─ Task 3 execute_mfa_strategy      (log de la ventana C-1 / C / C+1)
        └─ Task 4 issue_elevated_session    → access_token {mfa_verified: true}
                                                     │
Web ──GET /api/boveda-secreta (Bearer access_token)──▶ 200
```

### Clean Architecture (backend)

Las dependencias apuntan siempre hacia adentro: `presentation → application → domain`, y `infrastructure` implementa los puertos de `application`.

```
app/
├── domain/                 # Reglas de negocio puras (sin frameworks)
│   ├── entities.py         # User + máquina de estados DISABLED → PENDING_VERIFICATION → ACTIVE
│   ├── totp.py             # Algoritmo TOTP/HOTP desde cero
│   ├── strategies.py       # Strategy: SecondFactorStrategy, TOTPStrategy, BackupCodeStrategy
│   └── exceptions.py
├── application/            # Casos de uso y puertos
│   ├── ports.py            # UserRepository, TokenService, ReplayCache, PasswordHasher, ...
│   ├── dto.py
│   ├── strategy_registry.py
│   ├── use_cases/          # Un caso de uso por paso del pipeline
│   └── workflows.py        # AuthWorkflows (abstracción) + implementación secuencial
├── infrastructure/         # Adaptadores
│   ├── persistence/        # SupabaseUserRepository, SQLiteUserRepository
│   ├── security/           # bcrypt, JWT, generador de secretos
│   ├── cache/              # Caché anti-replay en memoria (TTL 90 s)
│   ├── qr/                 # Render del QR
│   └── orchestration/      # PrefectAuthWorkflows: @flow / @task sobre los casos de uso
├── presentation/
│   ├── api/                # Rutas FastAPI, schemas, dependencias, mapeo de errores a HTTP
│   └── web/index.html      # Web app de login
├── container.py            # Composition Root (inyección de dependencias)
└── main.py
```

### Clean Architecture (app móvil)

```
lib/
├── domain/
│   ├── entities/           # OtpAccount, OtpCode
│   ├── repositories/       # AccountRepository (interfaz)
│   ├── services/           # Base32Decoder, TotpGenerator, OtpAuthUriParser, MacAlgorithm (puerto)
│   └── usecases/           # GetAccounts, AddAccountFromUri, AddAccountManually, DeleteAccount, GenerateCode
├── data/
│   ├── crypto/             # CryptoHmacSha1 (adaptador de package:crypto)
│   ├── datasources/        # Almacenamiento seguro (Keychain / Keystore)
│   ├── models/
│   └── repositories/       # AccountRepositoryImpl
├── presentation/           # Controller (ChangeNotifier), páginas y widgets
└── di/app_dependencies.dart  # Composition Root
```

### SOLID aplicado

| Principio | Dónde se ve |
|---|---|
| **S**ingle Responsibility | Cada paso del pipeline es un caso de uso propio (`ValidatePreAuthState`, `CheckAntiReplay`, `ExecuteMfaStrategy`, `IssueElevatedSession`). Las estrategias solo verifican; la persistencia la hace el caso de uso. En la app, `Base32Decoder`, `TotpGenerator` y `OtpAuthUriParser` están separados. |
| **O**pen/Closed | `StrategyRegistry`: agregar otro segundo factor (p. ej. WebAuthn) es registrar una clase nueva, sin tocar los casos de uso. |
| **L**iskov Substitution | `PrefectAuthWorkflows` y `SequentialAuthWorkflows` son intercambiables detrás de `AuthWorkflows`; `SupabaseUserRepository` y `SQLiteUserRepository` detrás de `UserRepository`. |
| **I**nterface Segregation | Puertos pequeños y específicos (`PasswordHasher`, `BackupCodeHasher`, `ReplayCache`, `Clock`, `MacAlgorithm`...). |
| **D**ependency Inversion | El dominio y la aplicación dependen de abstracciones; las implementaciones concretas solo se eligen en `container.py` / `app_dependencies.dart`. El reloj se inyecta, así que los tests son deterministas. |

### Patrones requeridos

- **Máquina de estados / Process Manager**: `User._transition` solo permite `DISABLED → PENDING_VERIFICATION → ACTIVE`. `POST /2fa/setup` deja el 2FA en `PENDING_VERIFICATION` y solo `POST /2fa/activate` con un código válido lo pasa a `ACTIVE`.
- **Step-Up Authentication**: `POST /auth/login` nunca entrega `access_token`. Devuelve un `pre_auth_token` (o un `setup_token` si el 2FA aún no está activo), cada uno con un `scope` que solo sirve para su endpoint.
- **Strategy**: `TOTPStrategy` (ventanas C-1, C, C+1) y `BackupCodeStrategy` (8 códigos de un solo uso, guardados como SHA-256).

---

## 2. Cómo levantar todo

### Requisitos

- Python 3.11+ (probado con 3.13)
- Flutter 3.x (probado con 3.44)
- Opcional: un proyecto en [Supabase](https://supabase.com)

### 2.1 Servidor de Prefect

```bash
cd backend-prefect
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

prefect config set PREFECT_API_URL=http://127.0.0.1:4200/api
prefect server start          # Dashboard en http://127.0.0.1:4200
```

### 2.2 Base de datos (Supabase)

1. En Supabase → **SQL Editor**, ejecutar [`backend-prefect/supabase_schema.sql`](backend-prefect/supabase_schema.sql).
2. Copiar `backend-prefect/.env.example` a `backend-prefect/.env` y llenar `SUPABASE_URL` y `SUPABASE_KEY` (usar la **service_role key**, porque la tabla tiene RLS activado). También poner un `JWT_SECRET` largo.

Si `SUPABASE_URL` / `SUPABASE_KEY` quedan vacíos, el backend usa SQLite local (`users.db`) automáticamente.

### 2.3 Backend + Web app

En otra terminal:

```bash
cd backend-prefect
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

- Web app de login: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- Tests: `pytest -q`

### 2.4 App móvil

```bash
cd mobile-authenticator
flutter pub get
flutter run            # con un emulador/dispositivo conectado
flutter test           # vectores RFC 6238 + paridad con el backend
```

En un emulador sin cámara, usar **Agregar → URI otpauth** o pegar la semilla Base32 que muestra la web.

---

## 3. Endpoints

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| POST | `/auth/register` | — | Crea usuario (`mfa_status=DISABLED`) |
| POST | `/auth/login` | — | Flow `login-password`. Devuelve `pre_auth_token` o `setup_token` |
| POST | `/2fa/setup` | `setup_token` | Flow `mfa-provisioning-start`: secreto, URI otpauth, QR, códigos de respaldo. Estado → `PENDING_VERIFICATION` |
| POST | `/2fa/activate` | `setup_token` | Flow `mfa-provisioning-confirm`: primer código válido → `ACTIVE` |
| POST | `/auth/verify-2fa` | `pre_auth_token` en el body | Flow `verify-2fa` (4 tasks). `method`: `totp` o `backup` |
| GET | `/api/boveda-secreta` | `access_token` con `mfa_verified=true` | Recurso protegido |

---

## 4. Guion de la demo (pruebas de aceptación)

1. **Paridad**: registrarse e iniciar sesión en la web → se muestra el QR. Escanearlo con la app propia **y** con Google/Microsoft Authenticator. Los 6 dígitos coinciden. Activar con el código.
2. **Modo avión**: activar el modo avión en el celular, esperar a que el contador pase de 0 (nueva ventana), iniciar sesión en la web, ingresar el código y pulsar **GET /api/boveda-secreta**.
3. **Anti-replay**: cerrar sesión, volver a entrar e ingresar **el mismo código** antes de que cambie. Respuesta `409 ReplayAttackDetected`; en Prefect, el run `verify-2fa-totp` queda **Failed** en `check_anti_replay_cache`.
4. **Clock skew / respaldo**: en Prefect → run `verify-2fa-totp` → *Logs* muestra `Match en ventana C`, `C-1` o `C+1`. Alternativa: elegir *Código de respaldo* en la web y usar uno de los 8 códigos; el run se llama `verify-2fa-backup`.

> En la UI de Prefect, `password` y `pre_auth_token` aparecen como `**********` (`SecretStr`).
