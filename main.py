import ctypes
import win32gui
import win32ui
import win32con
from PIL import Image
import numpy as np
import time
from threading import Thread
import logging
from queue import Queue
from plyer import notification
import win32clipboard
import io

# ========================
# CONFIGURAÇÕES GLOBAIS
# ========================
logging.basicConfig(filename='monitor.log', level=logging.INFO,
                    format='%(asctime)s - %(message)s')

CONFIG = {
    'cor_alvo_min': (200, 0, 0),  # vermelho mínimo
    'cor_alvo_max': (255, 80, 80),  # vermelho máximo
    'limite_pixels': 5,
    'intervalo': 5,
    'alerta_cooldown': 90
}

REGIAO_ICONE = (15, 2, 30, 30)
fila_notificacoes = Queue()
palavras_chaves = ["Agente", "agente", "Estado", "Fila", "Agentes", "agentes"]

# ========================
# FUNÇÕES DE CAPTURA
# ========================
def send_to_clipboard(image):
    output = io.BytesIO()
    image.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()

def capturar_janela_background(nome_janela):
    try:
        def callback(hwnd, hwnds):
            if win32gui.IsWindowVisible(hwnd) and nome_janela.lower() in win32gui.GetWindowText(hwnd).lower():
                hwnds.append(hwnd)
            return True

        hwnds = []
        win32gui.EnumWindows(callback, hwnds)
        if not hwnds:
            logging.warning(f"Janela '{nome_janela}' não encontrada")
            return None

        hwnd = hwnds[0]
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top

        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)
        result = ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)

        if result != 1:
            logging.warning(f"Falha ao capturar janela '{nome_janela}'")
            return None

        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        imagem = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                                  bmpstr, 'raw', 'BGRX', 0, 1)
        return imagem

    except Exception as e:
        logging.error(f"Erro ao capturar janela '{nome_janela}': {str(e)}")
        return None

    finally:
        if 'saveBitMap' in locals():
            win32gui.DeleteObject(saveBitMap.GetHandle())
        if 'saveDC' in locals():
            saveDC.DeleteDC()
        if 'mfcDC' in locals():
            mfcDC.DeleteDC()
        if 'hwndDC' in locals():
            win32gui.ReleaseDC(hwnd, hwndDC)

def extrair_regiao_icone(imagem_janela, regiao):
    try:
        if (regiao[0] + regiao[2] > imagem_janela.width or
            regiao[1] + regiao[3] > imagem_janela.height):
            logging.error("Região do ícone fora dos limites da janela")
            return None

        return imagem_janela.crop((
            regiao[0], regiao[1],
            regiao[0] + regiao[2], regiao[1] + regiao[3]
        ))

    except Exception as e:
        logging.error(f"Erro ao extrair região do ícone: {str(e)}")
        return None

# ========================
# DETECÇÃO
# ========================
def detectar_cor_alvo(imagem):
    try:
        img_array = np.array(imagem)
        mask = (
            (img_array[:, :, 0] >= CONFIG['cor_alvo_min'][0]) & (img_array[:, :, 0] <= CONFIG['cor_alvo_max'][0]) &
            (img_array[:, :, 1] >= CONFIG['cor_alvo_min'][1]) & (img_array[:, :, 1] <= CONFIG['cor_alvo_max'][1]) &
            (img_array[:, :, 2] >= CONFIG['cor_alvo_min'][2]) & (img_array[:, :, 2] <= CONFIG['cor_alvo_max'][2])
        )
        return np.sum(mask) >= CONFIG['limite_pixels']
    except Exception as e:
        logging.error(f"Erro ao detectar cor-alvo: {str(e)}")
        return False

def gerenciador_notificacoes():
    while True:
        nome_janela = fila_notificacoes.get()
        mensagem = f"Irregularidade detectada em {nome_janela[24:]}!"
        notification.notify(
            title="ALERTA DE MONITORAMENTO",
            message=mensagem,
            timeout=3
        )
        print(f"\a{mensagem}")
        fila_notificacoes.task_done()

def monitorar_janela(nome_janela):
    ultimo_alerta = 0
    while True:
        try:
            imagem_janela = capturar_janela_background(nome_janela)
            if not imagem_janela:
                time.sleep(CONFIG['intervalo'])
                continue

            icone = extrair_regiao_icone(imagem_janela, REGIAO_ICONE)
            send_to_clipboard(icone)

            if not icone:
                time.sleep(CONFIG['intervalo'])
                continue

            if detectar_cor_alvo(icone):
                agora = time.time()
                if agora - ultimo_a_
