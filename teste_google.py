import requests

# Cole sua chave exata aqui dentro das aspas
CHAVE_GOOGLE = "AIzaSyBmTxTvBG7Wx-P9B1tys6f_KWqdHV4V9s8" 

# Endereço da De'licia
origem = "Rua Capitão Leônidas Marques, 2410, Curitiba, PR"
# Um CEP qualquer para teste (UFPR)
destino = "81530-000"

url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origem}&destinations={destino}&key={CHAVE_GOOGLE}"

print("Enviando requisição para o Google...")
resposta = requests.get(url)

print("\n--- RESPOSTA DO GOOGLE ---")
print(resposta.json())