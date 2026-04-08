# ADR-0003: E2B Firecracker sandbox для выполнения кода

**Status:** Accepted  
**Date:** 2026-03-25

## Context

Студенты сдают проекты с кодом (Docker, Python, Node.js). Нужно запускать их код для проверки: сборка, тесты, health checks. Выполнение untrusted code на хосте — неприемлемый риск.

## Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| Docker-in-Docker | Знакомо, cheap | Побег из контейнера возможен, shared kernel |
| GitHub Actions | Нативная интеграция | Ограничения по времени, расходует минуты студентов |
| **E2B (Firecracker)** | Полная изоляция (microVM), API, auto-cleanup | Платный, зависимость от SaaS |
| Kata Containers | Полная изоляция | Сложная настройка, self-hosted |

## Decision

Использовать E2B Sandbox (Firecracker microVM). Code review реализован как sub-agent с tool-use loop внутри sandbox.

## Consequences

**Positive:**
- Полная изоляция: отдельная VM на каждый запуск
- Auto-cleanup: sandbox уничтожается после использования (`finally: sandbox.kill()`)
- Native git clone с GitHub App token авторизацией
- Sub-agent может исследовать проект адаптивно (не hardcoded sequence)

**Negative:**
- Стоимость: ~0.01 USD per sandbox (5 min)
- Лимит: 20 concurrent sandboxes
- Зависимость от SaaS (E2B API)
- Sandbox timeout 600s — долгий для CI

**Mitigations:**
- `finally: sandbox.kill()` гарантирует cleanup
- Graceful degradation: если E2B недоступен, грейдинг продолжается без code review
- `settings.e2b_api_key` optional — система работает без sandbox
