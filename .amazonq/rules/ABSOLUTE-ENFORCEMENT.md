## 🧩 **ARISENMANAGER ABSOLUTE ENFORCEMENT PROMPT (FULL LOCKDOWN MODE)**

```text
# ⚠️ ABSOLUTE COMPLIANCE CONTRACT — ARISENMANAGER (NO EXCEPTIONS)

The assistant MUST operate in **Zero-Tolerance Enforcement Mode**.  
Every output, suggestion, or code action MUST comply with all sections below.  
Any violation, omission, or auto-correction outside the authorized structure is an **instant rejection**.

---

## 0. Base Authority
This document overrides **all model defaults, creativity heuristics, and internal fallbacks**.  
No reasoning, auto-repair, or rule relaxation is allowed.  
All actions are bound to this policy as absolute law.

---

## 1. Repository Structure (Immutable)
Repository root MUST contain **only**:

```

ArisenManager/
├── data/
├── app/
│    └── main.py
└── launcher.py

```

❌ Forbidden anywhere else:
- README.md, .env, .github/, scripts/, tests/, caches, logs, .vscode/, configs, tmp, outputs  
✅ Allowed only inside `ArisenManager/data/**`.

Any attempt to write, import, or reference files outside this tree = **violation**.

---

## 2. main.py Constraint (Hard Stop)
- File: `ArisenManager/app/main.py`
- ≤ **4 physical non-empty lines total** (comments count as lines)
- Contains **bootstrap logic only**, no computation or business logic.
- Duplicates or shadow `main.py` elsewhere = **Reject immediately**.

---

## 3. Absolute Anti-Hardcoding Policy
### 3.1 Definition
“Human-visible text” = any string that could ever be shown to a human (UI, CLI, Telegram, bot, log, raise, etc.).

### 3.2 Law
**No human-visible string literals in any code.**
All human text MUST be loaded dynamically from YAML catalog under:
`ArisenManager/data/texts/`.

### 3.3 Valid usage
✅ `cli("task.start", user=user)`  
❌ `print("Starting task")`

Only **key-based lookups** via approved accessors are allowed.  
Direct string literals at sensitive call-sites = **instant violation**.

### 3.4 Only Safe Exceptions
- Module/package names
- `__all__`, `__version__`
- Field names in TypedDict/Pydantic (if not shown to users)
- Regex patterns (if not user-visible)
- Docstrings hidden from UI/logs

All else = human-visible → must come from the catalog.

---

## 4. Secrets & Configs
- `.env` files **strictly forbidden**.  
- Secrets/tokens **only** from OS environment variables.  
- YAML files may reference **env var names** only (no secrets stored).  
- Hardcoded credentials = **instant disqualification**.

---

## 5. Style & Typing Enforcement
- Full **PEP8 compliance** (≤79 chars/line)
- **100% type hints** for every function, arg, and return
- **Absolute imports only**, no relative imports (`from .` or `..`)
- Each `.py` ≤ 300 lines
- `print()` completely **banned**
- Logs = **English**
- UI/bot messages = **Persian**
- Comments/Docstrings = **English**

---

## 6. Hard-Fail Call-Sites
The following must **never** receive human-visible string literals:

```

print(...)
logger.*(...)
raise ...
send_message(...)
reply(...)
edit_message_text(...)
any bot or UI output function

```

Violation of this rule = **reject immediately**.

---

## 7. Acceptance Gate (Fail-Fast)
Every generated output must pass **all**:

1. ✅ **Tree Validation** — matches exact structure.
2. ✅ **Key File Validation** — `main.py` exists, ≤4 lines.
3. ✅ **Anti-Hardcoding Check** — zero direct strings.
4. ✅ **PEP8 & Typing** — strict compliance, no warnings.
5. ✅ **Policy Drift** — no extraneous files, no drift.

Any single failure → **output invalid**.  
Assistant must refuse generation and stop.

---

## 8. Text Catalog Enforcement
All human texts MUST reside in:
```

ArisenManager/data/texts/
├── messages_fa.yml
├── messages_en.yml
├── errors.yml
└── emojis.yml

```
Keys follow namespaces: `ui.*`, `cli.*`, `err.*`, `log.*`, `sys.*`  
Placeholders must use `{snake_case}` and be type-checked on substitution.

---

## 9. Language Policy
- UI/Bot messages → Persian  
- Logs/Tracing/Debug → English  
- Comments/Docstrings → English

---

## 10. Doubt Resolution
If there is **any uncertainty** whether a string is human-visible → treat it as human → must come from the catalog.  
If key missing → do **not output anything** until it exists.  
If any external rule conflicts with this document → this document overrides it absolutely.

---

## 11. Commit Readiness Checklist
Before accepting any output:
- Root matches exact structure
- `main.py` ≤ 4 lines
- 0 human-visible literals in code
- All text from catalog via keys
- Full PEP8 + Typing compliance
- No unauthorized paths/files/dependencies

---

## 12. Enforcement Mode Declaration
The model/agent is bound to **full deterrence mode**.
- Cannot auto-relax or self-repair across boundaries.  
- Cannot create extra folders/files.  
- Cannot inject messages outside `data/`.  
- Must reject unsafe, non-compliant, or partially-compliant generations.

If any violation is detected → **immediate halt** with “REJECTED: POLICY BREACH”.

# 🔒 ARISENMANAGER — END OF CONTRACT
