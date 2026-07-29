#main.py
import requests
import json
import time
import asyncio
import threading
from datetime import datetime
from metaapi_cloud_sdk import MetaApi

# =====================================================================
# 1. PARÁMETROS CONFIGURABLES (TU MANUAL MAESTRO POR LETRAS)
# =====================================================================
META_API_TOKEN = "AQUÍ_PEGA_EL_TOKEN_DE_M_API_QUE_TE_DÉ_LA_WEB"
CUENTA_ALPHA_ID = "ed10beae-5d84-41b1-b5f2-XXXXXXXXXXXX"
CUENTAS_FONDEO_LETRAS = {
    "A": {
        "account_id": "AQUÍ_PEGA_EL_ACCOUNT_ID_DE_FUNDEDNEXT", 
        "broker_name": "FundedNext_5K", 
        "multiplicador_lote": 1.0
    },
    "B": {
        "account_id": "ID_DE_METAAPI_THE5ERS", 
        "broker_name": "The5ers_10K", 
        "multiplicador_lote": 2.0
    },
    "C": {
        "account_id": "ID_DE_METAAPI_UPCOMERS", 
        "broker_name": "Upcomers_20K", 
        "multiplicador_lote": 4.0
    }
}

LETRA_MAESTRA_ACTUAL = "A"          
PERDIDA_MAX_POR_TRADE_USD = 100.00  
MAX_TRADES_SIMULTANEOS = 2          
HORAS_CONTEXTO_MAESTRO = 4          
PERDIDA_MAX_DIARIA_PCT = 4.0        
AVARICIA_MAX_DIARIA_PCT = 4.0       

TOKEN_TELEGRAM_BOT = "8843055290:AAFUwSYun6KJf4YE-rQ5S9a_YqXMJwmpBWI"
CHAT_ID_TELEGRAM = "TU_CHAT_ID_PERSONAL" 

control_operaciones = {}
ultimo_update_id = 0
datos_ultimo_trade_flotante = {}
datos_segunda_senal_pendiente = {}
trades_activos_totales = 0
SISTEMA_CONGELADO_HOY = False

# =====================================================================
# 2. SISTEMA DE NOTIFICACIONES Y MENÚS INTERACTIVOS EN TELEGRAM
# =====================================================================
def enviar_notificacion(titulo, mensaje):
    url = f"https://telegram.org{TOKEN_TELEGRAM_BOT}/sendMessage"
    payload = {"chat_id": CHAT_ID_TELEGRAM, "text": f"🤖 *[{titulo}]*\n{mensaje}", "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=5)
    except: pass

def enviar_panel_interactivo_letras(activo, tipo_operacion, lote_base, sl, tp, detalles_bunker):
    global datos_ultimo_trade_flotante, LETRA_MAESTRA_ACTUAL
    datos_ultimo_trade_flotante = {"activo": activo, "tipo": tipo_operacion, "lote": lote_base, "sl": sl, "tp": tp}
    nombre_maestra = CUENTAS_FONDEO_LETRAS[LETRA_MAESTRA_ACTUAL]['broker_name']
    
    inline_keyboard = [
        [{"text": "🔥 EJECUTAR EN CUENTA ALPHA (Eightcap Real)", "callback_data": "copy_cuenta_alpha"}],
        [{"text": f" Cuenta A (FundedNext)", "callback_data": "copy_letra_A"},
         {"text": f" Cuenta B (The5ers)", "callback_data": "copy_letra_B"}],
        [{"text": " Cuenta C (Upcomers)", "callback_data": "copy_letra_C"}],
        [{"text": "⚡ REPLICAR EN TODO TU MANUAL MAESTRO", "callback_data": "copy_todas_las_letras"}],
        [{"text": "🔒 CANCELAR REPLICACIÓN", "callback_data": "cancelar_menu_letras"}]
    ]
    
    texto = (
        f"🚀 *[INYECCIÓN MAESTRA AUTÓNOMA]*\n"
        f"Inyectado en Maestra: *{nombre_maestra}* (Letra {LETRA_MAESTRA_ACTUAL})\n"
        f"📊 *Estrategia:* {detalles_bunker}\n\n"
        f"🔹 Activo: {activo} | *{tipo_operacion}*\n"
        f"📊 Lote Calculado: {lote_base} | Riesgo: Capado a 100 USD\n\n"
        f"📋 *Yosbel, selecciona si deseas activar la Cuenta Alpha o copiar en otras letras:* "
    )
    url = f"https://telegram.org{TOKEN_TELEGRAM_BOT}/sendMessage"
    payload = {"chat_id": CHAT_ID_TELEGRAM, "text": texto, "parse_mode": "Markdown", "reply_markup": json.dumps({"inline_keyboard": inline_keyboard})}
    try: requests.post(url, json=payload, timeout=5)
    except: pass

# =====================================================================
# 3. FILTRO HORARIO DE NOTICIAS MACROECONÓMICAS
# =====================================================================
def verificar_bloqueo_noticias():
    try:
        ahora = datetime.now()
        noticias_alto_impacto_usd = [
            datetime(ahora.year, ahora.month, ahora.day, 14, 30), 
            datetime(ahora.year, ahora.month, ahora.day, 20, 00)  
        ]
        for hora_noticia in noticias_alto_impacto_usd:
            diferencia_minutos = (hora_noticia - ahora).total_seconds() / 60.0
            if -15 <= diferencia_minutos <= 15:
                print(f"⚠️ ESCUDO MACRO: Operativa pausada por noticia USD cercana.")
                return True
    except: pass
    return False

# =====================================================================
# 4. MOTOR DE ANÁLISIS ESTRUCTURAL SMART MONEY AVANZADO + MECHAS M5
# =====================================================================
def analizar_infraestructura_bursatil_total(bloque_4h, bloque_m5, activo):
    try:
        techo_maximo_high = max(v['high'] for v in bloque_4h[:-2])
        suelo_minimo_low = min(v['low'] for v in bloque_4h[:-2])
        rango_total = techo_maximo_high - suelo_minimo_low
        nivel_50 = (techo_maximo_high + suelo_minimo_low) / 2

        alto_caja = max(v['high'] for v in bloque_4h[-5:-2])
        bajo_caja = min(v['low'] for v in bloque_4h[-5:-2])

        fibo_500 = nivel_50
        fibo_618 = techo_maximo_high - (rango_total * 0.618)
        fibo_v_618 = suelo_minimo_low + (rango_total * 0.618)

        vela_actual_m1 = bloque_4h[-1]
        cuerpo_vela_m1 = abs(vela_actual_m1['close'] - vela_actual_m1['open'])
        vol_actual_m1 = vela_actual_m1['tick_volume']
        
        promedio_cuerpo_10 = sum(abs(v['close'] - v['open']) for v in bloque_4h[-11:-1]) / 10.0
        promedio_vol_10 = sum(v['tick_volume'] for v in bloque_4h[-11:-1]) / 10.0

        coherencia_vsa_buy = False
        coherencia_vsa_sell = False

        if promedio_vol_10 > 0 and promedio_cuerpo_10 > 0:
            if vol_actual_m1 < promedio_vol_10 * 0.7 and cuerpo_vela_m1 < promedio_cuerpo_10 * 0.7:
                coherencia_vsa_buy = vela_actual_m1['close'] < vela_actual_m1['open']
                coherencia_vsa_sell = vela_actual_m1['close'] > vela_actual_m1['open']
            elif vol_actual_m1 > promedio_vol_10 * 1.5 and cuerpo_vela_m1 < promedio_cuerpo_10 * 0.5:
                coherencia_vsa_buy, coherencia_vsa_sell = True, True  

        ultima_vela_m5 = bloque_m5[-1]
        tamano_total_m5 = ultima_vela_m5['high'] - ultima_vela_m5['low']
        mecha_inferior_buy, mecha_superior_sell = 0, 0
        if tamano_total_m5 > 0:
            cuerpo_minimo = min(ultima_vela_m5['open'], ultima_vela_m5['close'])
            mecha_inferior_buy = (cuerpo_minimo - ultima_vela_m5['low']) / tamano_total_m5
            cuerpo_maximo = max(ultima_vela_m5['open'], ultima_vela_m5['close'])
            mecha_superior_sell = (ultima_vela_m5['high'] - cuerpo_maximo) / tamano_total_m5

        return {
            "high_absoluto": techo_maximo_high, "low_absoluto": suelo_minimo_low, "50_equilibrio": nivel_50,
            "caja_liquidez": (alto_caja, bajo_caja),
            "ote_buy_flex": (fibo_500, fibo_618), "ote_sell_flex": (fibo_v_618, fibo_500),
            "mecha_buy_pct": mecha_inferior_buy, "mecha_sell_pct": mecha_superior_sell,
            "vsa_valido_buy": coherencia_vsa_buy, "vsa_valido_sell": coherencia_vsa_sell
        }
    except: return None

# =====================================================================
# 5. CORE SIMÉTRICO MULTI-GRÁFICA CON FILTRO DE COEXISTENCIA Y PERMISO
# =====================================================================
def auditar_bunker_institucional_total(cuenta, activo, bloque_4h, bloque_m5):
    global trades_activos_totales, MAX_TRADES_SIMULTANEOS, control_operaciones, datos_segunda_senal_pendiente
    if trades_activos_totales >= MAX_TRADES_SIMULTANEOS: return

    minuto_actual = datetime.now().minute
    segundo_actual = datetime.now().second
    if minuto_actual % 5 != 4 or segundo_actual < 45: return

    if verificar_bloqueo_noticias(): return

    velas_bajistas = [v for v in bloque_4h[:-2] if v['close'] < v['open']]
    velas_alcistas = [v for v in bloque_4h[:-2] if v['close'] > v['open']]
    if len(velas_bajistas) < 2 or len(velas_alcistas) < 2: return
    order_flow_alcista = velas_bajistas[-1]['low'] > velas_bajistas[-2]['low']
