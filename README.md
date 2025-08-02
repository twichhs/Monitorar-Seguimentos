# Monitoramento de Segmentos com Python 🖥️

Este script monitora **múltiplas janelas do Windows** e detecta **cores específicas** (ex: vermelho) em áreas configuradas da tela. Ao detectar uma anomalia, ele dispara uma **notificação automática**.

## Funcionalidades

✅ Captura janelas em segundo plano  
✅ Monitora pixels com base em uma cor alvo  
✅ Suporte a múltiplas janelas simultaneamente  
✅ Notificações automáticas via `plyer`  
✅ Log de alertas (`monitor.log`)

---

## Tecnologias

- Python 3.10+
- `Pillow`
- `numpy`
- `pyautogui`
- `plyer`
- `pywin32`
- `threading`
- `logging`

---

## Como usar

1. Instale as dependências:

```bash
pip install pillow numpy pyautogui plyer pywin32
